"""
Instagram Graph API — UnboundSales
Leitura de insights e publicação de conteúdo via Meta Content Publishing API.

Permissões necessárias no token de acesso:
  instagram_basic, instagram_content_publish,
  pages_read_engagement, pages_show_list
"""
import os
import sys
import requests
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import (
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_ACCOUNT_ID,
)

BASE_URL = "https://graph.facebook.com/v21.0"


def _get(endpoint: str, params: dict, token: Optional[str] = None) -> dict:
    token = token or INSTAGRAM_ACCESS_TOKEN
    params["access_token"] = token
    r = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def _post(endpoint: str, data: dict, token: Optional[str] = None) -> dict:
    token = token or INSTAGRAM_ACCESS_TOKEN
    data["access_token"] = token
    r = requests.post(f"{BASE_URL}/{endpoint}", data=data, timeout=60)
    r.raise_for_status()
    return r.json()


# ─── LEITURA ──────────────────────────────────────────────────────────────────

def obter_perfil(
    account_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> dict:
    """Retorna dados do perfil: username, bio, seguidores, nº de posts."""
    account_id = account_id or INSTAGRAM_ACCOUNT_ID
    return _get(
        account_id,
        {
            "fields": (
                "username,name,biography,website,"
                "followers_count,follows_count,media_count,"
                "profile_picture_url,account_type"
            )
        },
        access_token,
    )


def obter_posts(
    account_id: Optional[str] = None,
    access_token: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """Retorna lista dos posts mais recentes com métricas básicas."""
    account_id = account_id or INSTAGRAM_ACCOUNT_ID
    data = _get(
        f"{account_id}/media",
        {
            "fields": (
                "id,caption,timestamp,media_type,media_url,thumbnail_url,"
                "like_count,comments_count,permalink"
            ),
            "limit": limit,
        },
        access_token,
    )
    return data.get("data", [])


def obter_insights_post(
    media_id: str,
    access_token: Optional[str] = None,
) -> dict:
    """Retorna insights de um post individual (reach, impressions, engagement)."""
    try:
        data = _get(
            f"{media_id}/insights",
            {"metric": "impressions,reach,saved,video_views"},
            access_token,
        )
        return {item["name"]: item["values"][0]["value"] for item in data.get("data", [])}
    except Exception:
        return {}


def obter_insights_conta(
    account_id: Optional[str] = None,
    access_token: Optional[str] = None,
    periodo: str = "day",
) -> dict:
    """Retorna insights agregados da conta (últimos 30 dias)."""
    account_id = account_id or INSTAGRAM_ACCOUNT_ID
    try:
        data = _get(
            f"{account_id}/insights",
            {
                "metric": "impressions,reach,profile_views,follower_count",
                "period": periodo,
                "since": "30 days ago",
            },
            access_token,
        )
        resultado = {}
        for item in data.get("data", []):
            valores = item.get("values", [])
            if valores:
                resultado[item["name"]] = sum(v["value"] for v in valores)
        return resultado
    except Exception:
        return {}


def obter_audiencia(
    account_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> dict:
    """Retorna dados de audiência: faixa etária, gênero, países."""
    account_id = account_id or INSTAGRAM_ACCOUNT_ID
    try:
        data = _get(
            f"{account_id}/insights",
            {"metric": "audience_gender_age,audience_country,audience_city", "period": "lifetime"},
            access_token,
        )
        return {item["name"]: item.get("values", [{}])[0].get("value", {})
                for item in data.get("data", [])}
    except Exception:
        return {}


# ─── PUBLICAÇÃO ───────────────────────────────────────────────────────────────

def publicar_imagem(
    image_url: str,
    caption: str,
    account_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> dict:
    """
    Publica imagem no feed do Instagram.
    image_url deve ser uma URL pública acessível (hospedada).
    Retorna dict com 'id' do media publicado.
    """
    account_id = account_id or INSTAGRAM_ACCOUNT_ID

    # Passo 1: criar container de mídia
    container = _post(
        f"{account_id}/media",
        {"image_url": image_url, "caption": caption},
        access_token,
    )
    container_id = container.get("id")
    if not container_id:
        raise RuntimeError(f"Falha ao criar container: {container}")

    # Passo 2: publicar o container
    resultado = _post(
        f"{account_id}/media_publish",
        {"creation_id": container_id},
        access_token,
    )
    return resultado


def publicar_story(
    image_url: str,
    account_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> dict:
    """Publica imagem como Story no Instagram."""
    account_id = account_id or INSTAGRAM_ACCOUNT_ID

    container = _post(
        f"{account_id}/media",
        {"image_url": image_url, "media_type": "STORIES"},
        access_token,
    )
    container_id = container.get("id")
    if not container_id:
        raise RuntimeError(f"Falha ao criar container de story: {container}")

    return _post(
        f"{account_id}/media_publish",
        {"creation_id": container_id},
        access_token,
    )


# ─── DIAGNÓSTICO ─────────────────────────────────────────────────────────────

def coletar_dados_completos(
    account_id: Optional[str] = None,
    access_token: Optional[str] = None,
    limit_posts: int = 20,
) -> dict:
    """
    Coleta todos os dados necessários para análise da conta:
    perfil + posts + insights dos posts + insights da conta.
    """
    account_id = account_id or INSTAGRAM_ACCOUNT_ID

    perfil = obter_perfil(account_id, access_token)
    posts = obter_posts(account_id, access_token, limit_posts)

    # Enriquece posts com insights individuais
    for post in posts[:10]:  # insights apenas dos 10 mais recentes (cota da API)
        post["insights"] = obter_insights_post(post["id"], access_token)

    insights_conta = obter_insights_conta(account_id, access_token)
    audiencia = obter_audiencia(account_id, access_token)

    # Métricas derivadas
    total_curtidas = sum(p.get("like_count", 0) for p in posts)
    total_comentarios = sum(p.get("comments_count", 0) for p in posts)
    seguidores = perfil.get("followers_count", 1)
    taxa_engajamento = round(
        ((total_curtidas + total_comentarios) / max(len(posts), 1)) / max(seguidores, 1) * 100, 2
    )

    return {
        "perfil": perfil,
        "posts": posts,
        "insights_conta": insights_conta,
        "audiencia": audiencia,
        "metricas": {
            "total_posts_analisados": len(posts),
            "media_curtidas": round(total_curtidas / max(len(posts), 1), 1),
            "media_comentarios": round(total_comentarios / max(len(posts), 1), 1),
            "taxa_engajamento_percent": taxa_engajamento,
        },
    }
