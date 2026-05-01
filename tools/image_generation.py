"""
Geração de imagens — UnboundSales
Suporta OpenAI gpt-image-2 e Google Gemini gemini-3.1-flash-image-preview.
"""
import base64
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import OPENAI_API_KEY, GEMINI_API_KEY

# Diretório padrão para salvar imagens geradas
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "imagens"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ─── OPENAI GPT-IMAGE-2 ────────────────────────────────────────────────────────

def gerar_imagem_openai(
    prompt: str,
    nome_arquivo: str = "imagem",
    tamanho: str = "1024x1024",
    qualidade: str = "standard",
) -> Path:
    """
    Gera imagem via OpenAI gpt-image-2.
    tamanho: "1024x1024" | "1024x1792" (portrait) | "1792x1024" (landscape)
    qualidade: "standard" | "hd"
    Retorna Path para o arquivo PNG salvo.
    """
    import openai

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.images.generate(
        model="gpt-image-2",
        prompt=prompt,
        n=1,
        size=tamanho,
        quality=qualidade,
        response_format="b64_json",
    )

    img_data = base64.b64decode(response.data[0].b64_json)
    caminho = OUTPUT_DIR / f"{nome_arquivo}_openai.png"
    caminho.write_bytes(img_data)
    return caminho


# ─── GOOGLE GEMINI IMAGE ───────────────────────────────────────────────────────

def gerar_imagem_gemini(
    prompt: str,
    nome_arquivo: str = "imagem",
) -> Path:
    """
    Gera imagem via Google Gemini gemini-3.1-flash-image-preview (google-genai SDK).
    Retorna Path para o arquivo PNG salvo.
    """
    from google import genai
    from google.genai import types

    client_gemini = genai.Client(api_key=GEMINI_API_KEY)
    response = client_gemini.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            img_data = part.inline_data.data
            caminho = OUTPUT_DIR / f"{nome_arquivo}_gemini.png"
            caminho.write_bytes(img_data)
            return caminho

    raise RuntimeError("Gemini não retornou imagem na resposta.")


# ─── INTERFACE UNIFICADA ───────────────────────────────────────────────────────

def gerar_imagem(
    prompt: str,
    nome_arquivo: str = "imagem",
    provider: str = "openai",
    tamanho: str = "1024x1024",
    qualidade: str = "standard",
) -> Path:
    """
    Gera imagem pelo provider escolhido.
    provider: "openai" | "gemini"
    Retorna Path do arquivo salvo.
    """
    if provider == "gemini":
        return gerar_imagem_gemini(prompt, nome_arquivo)
    return gerar_imagem_openai(prompt, nome_arquivo, tamanho, qualidade)


# ─── FORMATOS DE DESTINO ───────────────────────────────────────────────────────

FORMATOS = {
    "instagram_feed":    {"tamanho": "1024x1024", "descricao": "Instagram Feed (quadrado 1:1)"},
    "instagram_story":   {"tamanho": "1024x1792", "descricao": "Instagram Story (9:16)"},
    "instagram_retrato": {"tamanho": "1024x1792", "descricao": "Instagram Retrato (4:5)"},
    "banner_horizontal": {"tamanho": "1792x1024", "descricao": "Banner / Capa (16:9)"},
    "quadrado":          {"tamanho": "1024x1024", "descricao": "Quadrado genérico"},
}


if __name__ == "__main__":
    caminho = gerar_imagem(
        prompt="Logotipo moderno para agência de marketing digital, estilo minimalista, cores azul e branco, fundo transparente",
        nome_arquivo="teste_logo",
        provider="openai",
    )
    print(f"Imagem salva em: {caminho}")
