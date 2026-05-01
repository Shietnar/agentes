"""
Agente Publicador de Conteúdo — UnboundSales
Publica posts diretamente no Instagram e TikTok.
Integra com tools/instagram_api.py e tools/tiktok_api.py.
"""
import sys
import os
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import (
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_ACCOUNT_ID,
    TIKTOK_ACCESS_TOKEN,
)


# ─── HOSPEDAGEM TEMPORÁRIA ────────────────────────────────────────────────────
# A Instagram Graph API exige uma URL pública para a imagem.
# Para uso interno/testes, usamos imgbb.com (upload gratuito).
# Em produção, use S3, Cloudflare R2 ou qualquer CDN.

def _fazer_upload_imgbb(caminho_imagem: str, imgbb_api_key: str) -> str:
    """Faz upload da imagem no imgbb e retorna URL pública."""
    import requests
    import base64

    with open(caminho_imagem, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    r = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": imgbb_api_key, "image": img_b64},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["data"]["url"]


# ─── INSTAGRAM ────────────────────────────────────────────────────────────────

def publicar_instagram(
    caminho_imagem: str,
    legenda: str,
    account_id: Optional[str] = None,
    access_token: Optional[str] = None,
    imgbb_api_key: Optional[str] = None,
    image_url: Optional[str] = None,
) -> dict:
    """
    Publica imagem no Instagram Feed.

    Parâmetros:
        caminho_imagem: path local da imagem (usado se image_url não fornecida)
        legenda: texto do post (suporta quebras de linha e hashtags)
        account_id: ID da conta Instagram Business (padrão: .env)
        access_token: token de acesso (padrão: .env)
        imgbb_api_key: chave imgbb para hospedar a imagem (padrão: .env)
        image_url: URL pública da imagem (opcional — bypass do upload)

    Retorna dict com id do post publicado.
    """
    from tools.instagram_api import publicar_imagem
    from config.settings import IMGBB_API_KEY

    account_id = account_id or INSTAGRAM_ACCOUNT_ID
    access_token = access_token or INSTAGRAM_ACCESS_TOKEN
    imgbb_api_key = imgbb_api_key or IMGBB_API_KEY

    if not image_url:
        if not imgbb_api_key:
            raise ValueError(
                "IMGBB_API_KEY não configurada. Adicione ao .env ou passe image_url diretamente."
            )
        print("[Publisher] Fazendo upload da imagem...")
        image_url = _fazer_upload_imgbb(caminho_imagem, imgbb_api_key)
        print(f"[Publisher] Imagem hospedada em: {image_url}")

    print("[Publisher] Publicando no Instagram...")
    resultado = publicar_imagem(image_url, legenda, account_id, access_token)
    print(f"[Publisher] Post publicado! ID: {resultado.get('id')}")
    return resultado


def publicar_story_instagram(
    caminho_imagem: str,
    account_id: Optional[str] = None,
    access_token: Optional[str] = None,
    imgbb_api_key: Optional[str] = None,
    image_url: Optional[str] = None,
) -> dict:
    """Publica imagem como Story no Instagram."""
    from tools.instagram_api import publicar_story
    from config.settings import IMGBB_API_KEY

    account_id = account_id or INSTAGRAM_ACCOUNT_ID
    access_token = access_token or INSTAGRAM_ACCESS_TOKEN
    imgbb_api_key = imgbb_api_key or IMGBB_API_KEY

    if not image_url:
        if not imgbb_api_key:
            raise ValueError("IMGBB_API_KEY não configurada.")
        image_url = _fazer_upload_imgbb(caminho_imagem, imgbb_api_key)

    return publicar_story(image_url, account_id, access_token)


# ─── TIKTOK ───────────────────────────────────────────────────────────────────

def publicar_tiktok(
    caminho_video: str,
    titulo: str,
    privacidade: str = "SELF_ONLY",
    access_token: Optional[str] = None,
) -> dict:
    """
    Publica vídeo no TikTok via upload direto.
    privacidade: "PUBLIC_TO_EVERYONE" | "MUTUAL_FOLLOW_FRIENDS" | "FOLLOWER_OF_CREATOR" | "SELF_ONLY"
    """
    from tools.tiktok_api import publicar_video

    access_token = access_token or TIKTOK_ACCESS_TOKEN
    if not Path(caminho_video).exists():
        raise FileNotFoundError(f"Vídeo não encontrado: {caminho_video}")

    print("[Publisher] Publicando no TikTok...")
    resultado = publicar_video(caminho_video, titulo, privacidade, access_token=access_token)
    print(f"[Publisher] TikTok publish_id: {resultado.get('publish_id')}")
    return resultado


# ─── FLUXO COMPLETO: DESIGNER → PUBLISHER ─────────────────────────────────────

def gerar_e_publicar_instagram(
    descricao: str,
    legenda: str,
    segmento: str,
    cidade: str,
    formato: str = "instagram_feed",
    provider: str = "openai",
    account_id: Optional[str] = None,
    access_token: Optional[str] = None,
    imgbb_api_key: Optional[str] = None,
) -> dict:
    """
    Fluxo completo: gera imagem com o Designer Agent e publica no Instagram.
    """
    from agents.designer_agent import gerar_post

    # 1. Gerar imagem
    post = gerar_post(
        descricao=descricao,
        segmento=segmento,
        cidade=cidade,
        formato=formato,
        provider=provider,
        nome_arquivo=f"instagram_{segmento.replace(' ', '_')}",
    )

    # 2. Montar legenda completa
    hashtags_str = " ".join(post["hashtags"])
    legenda_completa = f"{legenda}\n\n{hashtags_str}" if hashtags_str else legenda

    # 3. Publicar
    resultado_pub = publicar_instagram(
        caminho_imagem=post["caminho"],
        legenda=legenda_completa,
        account_id=account_id,
        access_token=access_token,
        imgbb_api_key=imgbb_api_key,
    )

    return {
        "imagem": post["caminho"],
        "legenda_publicada": legenda_completa,
        "instagram": resultado_pub,
        "prompt_usado": post["prompt_usado"],
    }
