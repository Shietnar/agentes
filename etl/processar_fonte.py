"""
Processa uma fonte única (URL ou bytes de PDF) e retorna markdown de conhecimento.
Detecta automaticamente o tipo: YouTube vídeo, playlist, artigo web, PDF.
"""
import re
from typing import Optional
from datetime import datetime


def detectar_tipo(url: str) -> str:
    """Detecta o tipo de fonte a partir da URL."""
    url_lower = url.lower()
    if re.search(r'(youtube\.com|youtu\.be)', url_lower):
        if 'list=' in url_lower:
            return 'youtube_playlist'
        return 'youtube_video'
    if 'instagram.com' in url_lower:
        return 'instagram'
    return 'web_article'


def processar_url(
    url: str,
    agent_key: str,
    topico: str,
    on_status: callable = None,
    model: str = "claude-sonnet-4-6",
) -> dict:
    """
    Processa uma URL e retorna dict com {md, tipo, chars, erro}.
    on_status(mensagem) é chamado com atualizações de progresso.
    """
    def _status(msg):
        if on_status:
            on_status(msg)

    tipo = detectar_tipo(url)

    try:
        if tipo == 'youtube_video':
            return _processar_youtube_video(url, agent_key, topico, _status, model)
        elif tipo == 'youtube_playlist':
            return _processar_youtube_playlist(url, agent_key, topico, _status, model)
        elif tipo == 'instagram':
            return _processar_instagram(url, agent_key, topico, _status, model)
        else:
            return _processar_web(url, agent_key, topico, _status, model)
    except Exception as e:
        return {"md": None, "tipo": tipo, "chars": 0, "erro": str(e)}


def processar_pdf(
    conteudo_bytes: bytes,
    nome_arquivo: str,
    agent_key: str,
    topico: str,
    on_status: callable = None,
    model: str = "claude-sonnet-4-6",
) -> dict:
    """Processa um PDF e retorna dict com {md, tipo, chars, erro}."""
    def _status(msg):
        if on_status:
            on_status(msg)

    _status("Extraindo texto do PDF...")
    from etl.extractors.pdf import extrair_pdf
    texto = extrair_pdf(conteudo_bytes, nome_arquivo)
    if not texto:
        return {"md": None, "tipo": "pdf", "chars": 0, "erro": "Não foi possível extrair texto do PDF"}

    chars_texto = len(texto)
    _status(f"Texto extraído: {chars_texto:,} chars. Processando com Claude...")
    from etl.processors.knowledge_extractor import extrair_conhecimento
    md = extrair_conhecimento(
        texto=texto,
        agente=agent_key,
        topico=topico,
        fonte=nome_arquivo,
        titulo=topico,
        model=model,
    )
    if not md:
        return {"md": None, "tipo": "pdf", "chars": 0, "erro": "Claude não encontrou conteúdo relevante"}

    return {"md": md, "tipo": "pdf", "chars": len(md), "erro": None}


def _extrair_video_id(url: str) -> Optional[str]:
    m = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    return m.group(1) if m else None


def _extrair_playlist_id(url: str) -> Optional[str]:
    m = re.search(r'list=([a-zA-Z0-9_-]+)', url)
    return m.group(1) if m else None


def _processar_youtube_video(url, agent_key, topico, status_cb, model):
    video_id = _extrair_video_id(url)
    if not video_id:
        return {"md": None, "tipo": "youtube_video", "chars": 0, "erro": "ID de vídeo não encontrado na URL"}

    status_cb("Obtendo título do vídeo...")
    from etl.extractors.youtube import extrair_video, obter_titulo_video
    titulo = obter_titulo_video(video_id)
    status_cb(f"Extraindo transcrição de: {titulo}...")
    transcricao = extrair_video(video_id, idioma="pt")
    if not transcricao:
        return {"md": None, "tipo": "youtube_video", "chars": 0, "erro": "Transcrição não disponível para este vídeo"}

    chars_transcricao = len(transcricao)
    status_cb(f"Transcrição obtida ({chars_transcricao:,} chars). Processando com Claude...")
    from etl.processors.knowledge_extractor import extrair_conhecimento
    md = extrair_conhecimento(
        texto=transcricao,
        agente=agent_key,
        topico=topico,
        fonte=url,
        titulo=titulo,
        model=model,
    )
    if not md:
        return {"md": None, "tipo": "youtube_video", "chars": 0, "erro": "Claude não encontrou conteúdo relevante"}
    return {"md": md, "tipo": "youtube_video", "chars": len(md), "erro": None}


def _processar_youtube_playlist(url, agent_key, topico, status_cb, model):
    playlist_id = _extrair_playlist_id(url)
    if not playlist_id:
        return {"md": None, "tipo": "youtube_playlist", "chars": 0, "erro": "ID de playlist não encontrado na URL"}

    status_cb("Extraindo vídeos da playlist...")
    from etl.extractors.youtube import extrair_playlist
    videos = extrair_playlist(playlist_id, idioma="pt", max_videos=15)
    if not videos:
        return {"md": None, "tipo": "youtube_playlist", "chars": 0, "erro": "Nenhum vídeo com transcrição encontrado na playlist"}

    n_videos = len(videos)
    status_cb(f"{n_videos} vídeos com transcrição. Consolidando com Claude...")
    from etl.processors.knowledge_extractor import consolidar_conhecimento
    md = consolidar_conhecimento(videos, agent_key, topico)
    if not md:
        return {"md": None, "tipo": "youtube_playlist", "chars": 0, "erro": "Claude não encontrou conteúdo relevante"}
    return {"md": md, "tipo": "youtube_playlist", "chars": len(md), "erro": None}


def _processar_web(url, agent_key, topico, status_cb, model):
    status_cb(f"Fazendo scraping de: {url}...")
    from etl.extractors.web_scraper import extrair_artigo
    artigo = extrair_artigo(url)
    if not artigo:
        return {"md": None, "tipo": "web_article", "chars": 0, "erro": "Não foi possível extrair conteúdo da página"}

    chars_conteudo = len(artigo['conteudo'])
    status_cb(f"Conteúdo obtido ({chars_conteudo:,} chars). Processando com Claude...")
    from etl.processors.knowledge_extractor import extrair_conhecimento
    md = extrair_conhecimento(
        texto=artigo["conteudo"],
        agente=agent_key,
        topico=topico,
        fonte=url,
        titulo=artigo.get("titulo", topico),
        model=model,
    )
    if not md:
        return {"md": None, "tipo": "web_article", "chars": 0, "erro": "Claude não encontrou conteúdo relevante"}
    return {"md": md, "tipo": "web_article", "chars": len(md), "erro": None}


def _processar_instagram(url, agent_key, topico, status_cb, model):
    # Instagram bloqueia scraping — trata como artigo web genérico
    status_cb("Tentando extrair conteúdo do Instagram...")
    return _processar_web(url, agent_key, topico, status_cb, model)
