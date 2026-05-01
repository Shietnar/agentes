"""
TikTok Content Posting API — UnboundSales
Publicação de vídeos via TikTok for Developers Content Posting API v2.

Permissões necessárias (TikTok Developer App):
  video.publish, video.upload, user.info.basic
"""
import os
import sys
import requests
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import TIKTOK_ACCESS_TOKEN

TIKTOK_API = "https://open.tiktokapis.com/v2"


def _headers(token: Optional[str] = None) -> dict:
    return {
        "Authorization": f"Bearer {token or TIKTOK_ACCESS_TOKEN}",
        "Content-Type": "application/json; charset=UTF-8",
    }


# ─── USUÁRIO ──────────────────────────────────────────────────────────────────

def obter_usuario_info(access_token: Optional[str] = None) -> dict:
    """Retorna informações do usuário TikTok autenticado."""
    r = requests.post(
        f"{TIKTOK_API}/user/info/",
        headers=_headers(access_token),
        json={"fields": ["open_id", "union_id", "display_name", "avatar_url",
                         "follower_count", "following_count", "likes_count"]},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("data", {}).get("user", {})


# ─── PUBLICAÇÃO DE VÍDEO ──────────────────────────────────────────────────────

def publicar_video(
    video_path: str,
    titulo: str,
    privacidade: str = "SELF_ONLY",
    acesso_comentarios: bool = True,
    acesso_dueto: bool = False,
    acesso_stitch: bool = False,
    access_token: Optional[str] = None,
) -> dict:
    """
    Publica vídeo no TikTok via upload direto (FILE_UPLOAD).
    privacidade: "PUBLIC_TO_EVERYONE" | "MUTUAL_FOLLOW_FRIENDS" | "FOLLOWER_OF_CREATOR" | "SELF_ONLY"
    Retorna dict com publish_id.
    """
    video_file = Path(video_path)
    if not video_file.exists():
        raise FileNotFoundError(f"Vídeo não encontrado: {video_path}")

    file_size = video_file.stat().st_size

    # Passo 1: inicializar upload
    init_payload = {
        "post_info": {
            "title": titulo[:150],
            "privacy_level": privacidade,
            "disable_comment": not acesso_comentarios,
            "disable_duet": not acesso_dueto,
            "disable_stitch": not acesso_stitch,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": file_size,
            "chunk_size": file_size,
            "total_chunk_count": 1,
        },
    }

    r = requests.post(
        f"{TIKTOK_API}/post/publish/video/init/",
        headers=_headers(access_token),
        json=init_payload,
        timeout=30,
    )
    r.raise_for_status()
    init_data = r.json().get("data", {})
    publish_id = init_data.get("publish_id")
    upload_url = init_data.get("upload_url")

    if not publish_id or not upload_url:
        raise RuntimeError(f"Falha na inicialização do upload: {r.json()}")

    # Passo 2: fazer upload do arquivo
    with open(video_path, "rb") as f:
        video_bytes = f.read()

    upload_headers = {
        "Content-Type": "video/mp4",
        "Content-Length": str(file_size),
        "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
    }
    upload_r = requests.put(upload_url, headers=upload_headers, data=video_bytes, timeout=120)
    upload_r.raise_for_status()

    return {"publish_id": publish_id, "status": "enviado"}


def verificar_status_publicacao(
    publish_id: str,
    access_token: Optional[str] = None,
) -> dict:
    """Verifica o status de uma publicação em andamento."""
    r = requests.post(
        f"{TIKTOK_API}/post/publish/status/fetch/",
        headers=_headers(access_token),
        json={"publish_id": publish_id},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("data", {})


# ─── PUBLICAÇÃO VIA URL (Pull From URL) ───────────────────────────────────────

def publicar_video_por_url(
    video_url: str,
    titulo: str,
    privacidade: str = "SELF_ONLY",
    access_token: Optional[str] = None,
) -> dict:
    """
    Publica vídeo no TikTok passando uma URL pública (TikTok faz o download).
    Mais simples que upload direto — use quando o vídeo já está hospedado.
    """
    payload = {
        "post_info": {
            "title": titulo[:150],
            "privacy_level": privacidade,
            "disable_comment": False,
            "disable_duet": True,
            "disable_stitch": True,
        },
        "source_info": {
            "source": "PULL_FROM_URL",
            "video_url": video_url,
        },
    }

    r = requests.post(
        f"{TIKTOK_API}/post/publish/video/init/",
        headers=_headers(access_token),
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    data = r.json().get("data", {})
    return {"publish_id": data.get("publish_id"), "status": "publicação_iniciada"}
