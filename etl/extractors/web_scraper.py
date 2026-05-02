"""
Web Scraper — extrai conteúdo de artigos e páginas web.
Usa httpx + BeautifulSoup4.
"""
import httpx
from bs4 import BeautifulSoup
from typing import Optional
import re


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


def extrair_artigo(url: str) -> Optional[dict]:
    """
    Extrai texto principal de um artigo/página web.
    Retorna {url, titulo, conteudo} ou None se falhar.
    """
    try:
        r = httpx.get(url, headers=_HEADERS, timeout=20, follow_redirects=True)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")

        # Remove ruído
        for tag in soup(["script", "style", "nav", "footer", "header",
                          "aside", "form", ".sidebar", ".menu", ".ad", ".cookie"]):
            tag.decompose()

        titulo = _extrair_titulo(soup)
        conteudo = _extrair_conteudo_principal(soup)

        if not conteudo or len(conteudo) < 300:
            return None

        return {"url": url, "titulo": titulo, "conteudo": conteudo}
    except Exception:
        return None


def extrair_blog_index(url: str, max_articles: int = 10) -> list[dict]:
    """
    Extrai artigos de uma página de índice de blog.
    Descobre links de artigos e extrai cada um.
    """
    links = _descobrir_links_artigos(url)
    resultados = []
    for link in links[:max_articles]:
        artigo = extrair_artigo(link)
        if artigo:
            resultados.append(artigo)
    return resultados


def _extrair_titulo(soup: BeautifulSoup) -> str:
    for sel in ["h1", "title", "meta[property='og:title']"]:
        el = soup.select_one(sel)
        if el:
            return (el.get("content") or el.get_text()).strip()[:200]
    return "Sem título"


def _extrair_conteudo_principal(soup: BeautifulSoup) -> str:
    """Extrai o bloco de conteúdo mais relevante da página."""
    # Tenta seletores comuns de conteúdo principal
    seletores = [
        "article",
        "main",
        "[role='main']",
        ".post-content",
        ".entry-content",
        ".article-content",
        ".blog-content",
        ".content-body",
        "#content",
        ".post",
    ]
    for sel in seletores:
        el = soup.select_one(sel)
        if el and len(el.get_text(strip=True)) > 300:
            return _limpar_texto(el.get_text(separator=" "))

    # Fallback: body inteiro
    body = soup.find("body")
    if body:
        return _limpar_texto(body.get_text(separator=" "))
    return ""


def _limpar_texto(texto: str) -> str:
    texto = re.sub(r'\s+', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    return texto.strip()[:30_000]  # máximo 30k chars por artigo


def _descobrir_links_artigos(base_url: str) -> list[str]:
    """Descobre links de artigos em uma página de índice."""
    try:
        r = httpx.get(base_url, headers=_HEADERS, timeout=20, follow_redirects=True)
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "html.parser")

        from urllib.parse import urljoin, urlparse
        base_domain = urlparse(base_url).netloc

        links = set()
        for a in soup.find_all("a", href=True):
            href = urljoin(base_url, a["href"])
            parsed = urlparse(href)
            # Só links do mesmo domínio, com path > base_url
            if (parsed.netloc == base_domain
                    and parsed.path != urlparse(base_url).path
                    and not any(x in href for x in ["#", "?page=", "tag/", "category/", "author/"])
                    and len(parsed.path) > 5):
                links.add(href)

        return sorted(links)[:50]  # retorna até 50 candidatos
    except Exception:
        return []
