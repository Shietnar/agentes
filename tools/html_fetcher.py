"""
Utilitário para buscar e analisar HTML de landing pages.
Usado pelo landing_agent para análise de URLs existentes.
"""
import sys
import os
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}


def fetch_html(url: str, timeout: int = 12) -> dict:
    """
    Busca o HTML de uma URL. Simula browser mobile.
    Retorna: {"html": str, "status_code": int, "url_final": str}
             ou {"erro": str}
    """
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=timeout, allow_redirects=True)
        return {
            "html": resp.text,
            "status_code": resp.status_code,
            "url_final": resp.url,
        }
    except requests.exceptions.Timeout:
        return {"erro": f"Timeout após {timeout}s ao acessar {url}"}
    except requests.exceptions.ConnectionError:
        return {"erro": f"Não foi possível conectar a {url}"}
    except Exception as e:
        return {"erro": str(e)}


def extrair_metadados(html: str) -> dict:
    """
    Extrai elementos-chave do HTML para análise de landing page.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remoção de scripts/styles antes de extrair texto
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = soup.find("title")
    meta_desc = soup.find("meta", attrs={"name": "description"})
    meta_viewport = soup.find("meta", attrs={"name": "viewport"})
    h1s = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2s = [h.get_text(strip=True) for h in soup.find_all("h2")][:6]

    # Telefone e WhatsApp
    telefones = [
        a.get("href", "")
        for a in soup.find_all("a", href=True)
        if a["href"].startswith("tel:")
    ]
    whatsapp = any(
        "wa.me" in a.get("href", "") or "whatsapp" in a.get("href", "").lower()
        for a in soup.find_all("a", href=True)
    )

    # Formulário de captura
    forms = soup.find_all("form")
    form_inputs = []
    for form in forms:
        form_inputs.extend([i.get("type", "") for i in form.find_all("input")])

    # Imagens sem alt (acessibilidade/SEO)
    imgs = soup.find_all("img")
    imgs_sem_alt = sum(1 for i in imgs if not i.get("alt", "").strip())

    # CTAs (botões + links com texto de ação)
    cta_keywords = ["ligue", "chamar", "contato", "whatsapp", "orçamento", "fale", "solicite"]
    ctas = [
        el.get_text(strip=True)
        for el in soup.find_all(["button", "a"])
        if any(kw in el.get_text(strip=True).lower() for kw in cta_keywords)
    ][:8]

    # Elementos de confiança
    trust_keywords = ["cnpj", "crea", "cro", "certificad", "garantia", "anos de experiência",
                      "clientes", "avaliação", "google", "estrelas"]
    texto_completo = soup.get_text(separator=" ", strip=True).lower()
    trust_encontrados = [kw for kw in trust_keywords if kw in texto_completo]

    return {
        "title": title.get_text(strip=True) if title else None,
        "meta_description": meta_desc.get("content", "").strip() if meta_desc else None,
        "tem_viewport_meta": meta_viewport is not None,
        "h1s": h1s,
        "h2s": h2s,
        "telefones_tel": telefones,
        "tem_whatsapp": whatsapp,
        "formularios": len(forms),
        "tipos_input": list(set(form_inputs)),
        "imagens_sem_alt": imgs_sem_alt,
        "ctas": ctas,
        "trust_elements": trust_encontrados,
        "chars_title": len(title.get_text(strip=True)) if title else 0,
        "chars_meta_desc": len(meta_desc.get("content", "")) if meta_desc else 0,
    }


def extrair_texto_visivel(html: str, max_chars: int = 6000) -> str:
    """
    Retorna o texto visível da página (sem scripts/styles), truncado.
    Usado para enviar ao Claude como contexto.
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()
    texto = soup.get_text(separator="\n", strip=True)
    # Remove linhas em branco consecutivas
    linhas = [l for l in texto.splitlines() if l.strip()]
    return "\n".join(linhas)[:max_chars]
