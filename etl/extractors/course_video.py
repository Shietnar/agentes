"""
Extrator de vídeos de plataformas de cursos pagos.
Usa yt-dlp com cookies de autenticação.
Transcrição: legenda embutida (preferida) → OpenAI Whisper API (fallback).
"""
import os
import re
import tempfile
from pathlib import Path
from typing import Optional


# Plataformas conhecidas que exigem autenticação
_PLATAFORMAS_CURSO = [
    "subido.com.br",
    "hotmart.com",
    "kiwify.com.br", "kiwify.app",
    "eduzz.com",
    "braip.com",
    "teachable.com",
    "thinkific.com",
    "membro.club",
    "sparkle.io",
    "memberkit.com.br",
    "curseduca.com",
]


def eh_plataforma_curso(url: str) -> bool:
    return any(p in url.lower() for p in _PLATAFORMAS_CURSO)


def baixar_e_transcrever(
    url: str,
    cookies_file: Optional[str] = None,
    on_status=None,
) -> dict:
    """
    Baixa áudio/legendas de um vídeo de curso e retorna transcrição.

    Returns:
        {
            "texto": str,        # transcrição completa
            "titulo": str,       # título do vídeo
            "duracao_min": float,
            "fonte": str,        # "legenda" ou "whisper"
            "erro": str,         # None se sucesso
        }
    """
    def log(msg):
        if on_status:
            on_status(msg)

    try:
        import yt_dlp
    except ImportError:
        return {"erro": "yt-dlp não instalado. Execute: pip install yt-dlp"}

    with tempfile.TemporaryDirectory() as tmpdir:
        log("Conectando à plataforma de curso...")

        ydl_opts = {
            # Preferência: áudio separado pequeno; fallback: melhor disponível
            "format": "bestaudio[filesize<25M]/bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best[height<=480]/best",
            "outtmpl": os.path.join(tmpdir, "audio.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            # Tenta baixar legendas embutidas (mais rápido, sem Whisper)
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["pt", "pt-BR", "pt-br", "en"],
            "subtitlesformat": "vtt",
            # Não baixa o vídeo inteiro se só precisarmos das legendas
            "skip_download": False,
        }

        if cookies_file:
            ydl_opts["cookiefile"] = cookies_file

        # ── Tenta primeiro só legendas (sem baixar vídeo) ─────────────────────
        opts_leg = {**ydl_opts, "skip_download": True}
        titulo = "Vídeo de curso"
        duracao_s = 0

        try:
            with yt_dlp.YoutubeDL(opts_leg) as ydl:
                info = ydl.extract_info(url, download=True)
                titulo = info.get("title", titulo)
                duracao_s = info.get("duration", 0) or 0
        except Exception:
            pass

        # Verifica se alguma legenda foi baixada
        for vtt_file in Path(tmpdir).glob("*.vtt"):
            log("Legenda encontrada — extraindo texto...")
            texto = _vtt_para_texto(str(vtt_file))
            if texto and len(texto) > 300:
                log(f"Transcrição via legenda: {len(texto):,} chars.")
                return {
                    "texto": texto,
                    "titulo": titulo,
                    "duracao_min": duracao_s / 60,
                    "fonte": "legenda",
                    "erro": None,
                }

        # ── Sem legenda: baixa áudio e usa Whisper ────────────────────────────
        log("Nenhuma legenda disponível. Baixando áudio para transcrição...")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                titulo = info.get("title", titulo)
                duracao_s = info.get("duration", 0) or 0
        except Exception as e:
            err = str(e)
            if "Sign in" in err or "login" in err.lower() or "private" in err.lower():
                return {
                    "erro": (
                        "Vídeo requer autenticação. Exporte os cookies do seu browser "
                        "e faça upload do arquivo cookies.txt acima."
                    )
                }
            if "Unsupported URL" in err:
                return {"erro": f"Plataforma não suportada pelo yt-dlp: {err}"}
            return {"erro": f"Erro ao baixar: {err}"}

        # Localiza o arquivo de áudio baixado
        audio_file = _encontrar_audio(tmpdir)
        if not audio_file:
            return {"erro": "Arquivo de áudio não encontrado após download."}

        tamanho_mb = Path(audio_file).stat().st_size / 1024 / 1024
        log(f"Áudio baixado ({tamanho_mb:.1f} MB). Transcrevendo com Whisper...")

        if tamanho_mb > 24:
            log(f"Arquivo grande ({tamanho_mb:.0f} MB) — Whisper processa até 25 MB.")
            if tamanho_mb > 50:
                return {
                    "erro": (
                        f"Arquivo muito grande ({tamanho_mb:.0f} MB). "
                        "Instale o FFmpeg para habilitar transcrição de vídeos longos."
                    )
                }

        texto = _transcrever_whisper(audio_file, on_status=on_status)
        if not texto:
            return {"erro": "Falha na transcrição. Verifique OPENAI_API_KEY no .env."}

        log(f"Transcrição concluída: {len(texto):,} chars.")
        return {
            "texto": texto,
            "titulo": titulo,
            "duracao_min": duracao_s / 60,
            "fonte": "whisper",
            "erro": None,
        }


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def _encontrar_audio(tmpdir: str) -> Optional[str]:
    for ext in ["m4a", "webm", "mp3", "opus", "ogg", "mp4", "wav"]:
        candidate = Path(tmpdir) / f"audio.{ext}"
        if candidate.exists():
            return str(candidate)
    for f in Path(tmpdir).iterdir():
        if f.suffix.lstrip(".") in {"m4a", "webm", "mp3", "opus", "ogg", "mp4", "wav"}:
            return str(f)
    return None


def _vtt_para_texto(vtt_path: str) -> str:
    """Extrai texto limpo de arquivo WebVTT."""
    with open(vtt_path, encoding="utf-8", errors="replace") as f:
        conteudo = f.read()

    linhas = conteudo.split("\n")
    textos = []
    for linha in linhas:
        linha = linha.strip()
        if (
            not linha
            or linha.startswith("WEBVTT")
            or linha.startswith("NOTE")
            or "-->" in linha
            or re.match(r"^\d+$", linha)
        ):
            continue
        linha = re.sub(r"<[^>]+>", "", linha)  # remove tags HTML
        linha = re.sub(r"&amp;", "&", linha)
        linha = re.sub(r"&lt;", "<", linha)
        linha = re.sub(r"&gt;", ">", linha)
        if linha:
            textos.append(linha)

    # Remove duplicatas consecutivas (legendas repetidas em janelas sobrepostas)
    resultado = []
    prev = ""
    for t in textos:
        if t != prev:
            resultado.append(t)
            prev = t

    return " ".join(resultado)


def _transcrever_whisper(audio_file: str, on_status=None) -> Optional[str]:
    """Transcreve áudio via OpenAI Whisper API."""
    from config.settings import OPENAI_API_KEY
    if not OPENAI_API_KEY:
        if on_status:
            on_status("OPENAI_API_KEY não configurada em .env — transcrição indisponível.")
        return None

    try:
        from openai import OpenAI
    except ImportError:
        if on_status:
            on_status("openai não instalado. Execute: pip install openai")
        return None

    client = OpenAI(api_key=OPENAI_API_KEY)

    with open(audio_file, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="pt",
        )
    return response.text
