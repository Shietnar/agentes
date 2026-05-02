"""
YouTube Extractor — extrai transcrições de vídeos e playlists.
Usa youtube-transcript-api (não precisa de API key).
"""
import re
import json
import httpx
from typing import Optional


import time

_yt_api = None
_ip_blocked = False  # flag global: para extração se IP bloqueado


def _get_yt_api():
    global _yt_api
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        if _yt_api is None:
            _yt_api = YouTubeTranscriptApi()
        return _yt_api
    except ImportError:
        raise ImportError("Execute: pip install youtube-transcript-api")


def extrair_video(video_id: str, idioma: str = "pt", delay: float = 1.5) -> Optional[str]:
    """
    Extrai transcrição de um vídeo do YouTube.
    delay: segundos de espera entre requests para evitar bloqueio de IP.
    Retorna texto limpo ou None se não houver transcrição.
    """
    global _ip_blocked
    if _ip_blocked:
        return None  # não tenta se IP já foi bloqueado nesta sessão

    api = _get_yt_api()
    time.sleep(delay)  # pausa entre requests

    try:
        idiomas_pref = [idioma, "pt-BR", "pt", "en"] if idioma != "en" else ["en", "pt", "pt-BR"]
        try:
            fetched = api.fetch(video_id, languages=idiomas_pref)
        except Exception:
            # Fallback: pega qualquer transcrição disponível
            transcript_list = api.list(video_id)
            fetched = next(iter(transcript_list)).fetch()

        texto = " ".join(s.text for s in fetched)
        texto = re.sub(r'\s+', ' ', texto).strip()
        return texto if len(texto) > 200 else None

    except Exception as e:
        err = str(e)
        if "IpBlocked" in err or "ipblocked" in err.lower() or "ip" in err.lower() and "block" in err.lower():
            print("  ⚠ IP bloqueado pelo YouTube. Parando extração de transcrições por agora.")
            print("  Dica: aguarde 15-30 minutos e rode novamente com --force.")
            _ip_blocked = True
        return None


def obter_titulo_video(video_id: str) -> str:
    """Obtém título do vídeo via oEmbed (sem API key)."""
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        r = httpx.get(url, timeout=10, follow_redirects=True)
        if r.status_code == 200:
            return r.json().get("title", video_id)
    except Exception:
        pass
    return video_id


def extrair_playlist(playlist_id: str, idioma: str = "pt", max_videos: int = 20) -> list[dict]:
    """
    Extrai transcrições de vídeos de uma playlist.
    Retorna lista de dicts: {video_id, titulo, transcricao}.
    """
    ids = _ids_da_playlist(playlist_id, max_videos)
    resultados = []
    for vid_id in ids:
        titulo = obter_titulo_video(vid_id)
        texto = extrair_video(vid_id, idioma)
        if texto:
            resultados.append({"video_id": vid_id, "titulo": titulo, "transcricao": texto})
    return resultados


def extrair_canal_recente(channel_id: str, idioma: str = "pt", max_videos: int = 10) -> list[dict]:
    """
    Extrai transcrições dos vídeos mais recentes de um canal.
    Usa RSS feed do YouTube (sem API key).
    """
    ids = _ids_do_canal(channel_id, max_videos)
    resultados = []
    for vid_id in ids:
        titulo = obter_titulo_video(vid_id)
        texto = extrair_video(vid_id, idioma)
        if texto:
            resultados.append({"video_id": vid_id, "titulo": titulo, "transcricao": texto})
    return resultados


def _ids_da_playlist(playlist_id: str, max_videos: int) -> list[str]:
    """
    Extrai IDs de vídeos de uma playlist.
    YouTube renderiza via JS mas embute os dados em ytInitialData — extrai com JSON.
    """
    try:
        url = f"https://www.youtube.com/playlist?list={playlist_id}"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                 "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        r = httpx.get(url, headers=headers, timeout=20, follow_redirects=True)
        return _extrair_ids_do_html(r.text, max_videos)
    except Exception:
        return []


def _ids_do_canal(channel_id: str, max_videos: int) -> list[str]:
    """
    Obtém IDs dos vídeos mais recentes de um canal.
    Tenta RSS feed primeiro; se falhar, tenta scraping da página do canal.
    """
    # Tenta RSS (funciona quando channel_id é o ID numérico UC...)
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        r = httpx.get(url, timeout=10, follow_redirects=True)
        if r.status_code == 200:
            ids = re.findall(r'<yt:videoId>([a-zA-Z0-9_-]{11})</yt:videoId>', r.text)
            if ids:
                return ids[:max_videos]
    except Exception:
        pass

    # Fallback: scraping da página de vídeos do canal
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                 "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        # Tenta como handle (@nome) e como ID direto
        for url in [
            f"https://www.youtube.com/{channel_id}/videos",
            f"https://www.youtube.com/channel/{channel_id}/videos",
        ]:
            r = httpx.get(url, headers=headers, timeout=20, follow_redirects=True)
            if r.status_code == 200:
                ids = _extrair_ids_do_html(r.text, max_videos)
                if ids:
                    return ids
    except Exception:
        pass

    return []


def _extrair_ids_do_html(html: str, max_videos: int) -> list[str]:
    """Extrai video IDs de HTML do YouTube (página de canal/playlist/busca)."""
    # Padrão 1: videoId em JSON embarcado
    ids = re.findall(r'"videoId"\s*:\s*"([a-zA-Z0-9_-]{11})"', html)
    if not ids:
        # Padrão 2: links /watch?v=
        ids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
    seen = set()
    unique = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            unique.append(i)
    return unique[:max_videos]


def buscar_videos_por_query(query: str, max_videos: int = 10) -> list[dict]:
    """
    Busca vídeos no YouTube por query e extrai transcrições.
    Útil quando o canal/playlist ID é desconhecido.
    """
    try:
        import urllib.parse
        q = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={q}"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                 "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        r = httpx.get(url, headers=headers, timeout=20, follow_redirects=True)
        ids = _extrair_ids_do_html(r.text, max_videos * 3)  # pega mais para filtrar sem transcrição
    except Exception:
        return []

    resultados = []
    for vid_id in ids:
        if len(resultados) >= max_videos:
            break
        titulo = obter_titulo_video(vid_id)
        texto = extrair_video(vid_id, "pt")
        if texto:
            resultados.append({"video_id": vid_id, "titulo": titulo, "transcricao": texto})
    return resultados
