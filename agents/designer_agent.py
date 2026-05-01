"""
Agente Designer de Conteúdo — UnboundSales
Gera imagens para posts de Instagram, TikTok, banners e landing pages.
Usa Claude para criar o prompt visual otimizado e depois chama OpenAI ou Gemini.
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from config.settings import ANTHROPIC_API_KEY, DEFAULT_MODEL
from tools.image_generation import gerar_imagem, FORMATOS, OUTPUT_DIR
from pathlib import Path

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Você é o Designer de Conteúdo da UnboundSales.
Você cria briefings visuais precisos para geração de imagens com IA,
focado em serviços locais de emergência no mercado brasileiro.

Seu trabalho é transformar um pedido de imagem em um prompt de geração de IA
que produza uma imagem profissional, clara e que converta bem em anúncios e redes sociais.

━━━ DIRETRIZES DE PROMPT VISUAL ━━━

Para serviços locais de emergência, imagens que convertem:
• Fotos estilo foto real, não ilustração (exceto pedido específico)
• Técnico uniformizado e equipado — transmite profissionalismo
• Ambiente limpo, organizado, depois do serviço
• Cores vibrantes mas sem exagero — azul, verde e vermelho funcionam bem
• Texto mínimo na imagem — a legenda carrega a mensagem
• Sem pessoas genéricas de banco de imagens — devem parecer reais

Para banners e LPs:
• Layout clean com hierarquia clara
• Headline grande e legível
• CTA em destaque (botão ou área colorida)
• Logotipo em posição de autoridade

Para Instagram Feed (quadrado 1:1):
• Composição centrada
• Espaço para legenda visual (texto sobreposto opcional)

Para Stories e TikTok (9:16 vertical):
• Ação no terço superior e inferior
• Meio da tela livre para texto/stickers

IMPORTANTE: Sempre escreva o prompt em inglês para melhores resultados na geração de imagem.
O prompt deve ser detalhado, descritivo e específico. Inclua: sujeito, ação, ambiente,
iluminação, estilo fotográfico, proporção."""

PROMPT_TOOL = {
    "name": "submeter_prompt_visual",
    "description": "Submete o prompt de geração de imagem e metadados",
    "input_schema": {
        "type": "object",
        "properties": {
            "prompt_geracao": {
                "type": "string",
                "description": "Prompt em inglês para o modelo de geração de imagem",
            },
            "prompt_negativo": {
                "type": "string",
                "description": "Elementos a evitar (para uso futuro com modelos que suportam)",
            },
            "justificativa": {
                "type": "string",
                "description": "Explicação das escolhas visuais em português",
            },
            "sugestao_legenda": {
                "type": "string",
                "description": "Sugestão de legenda para o post em português",
            },
            "hashtags": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["prompt_geracao", "justificativa", "sugestao_legenda", "hashtags"],
    },
}


def _criar_prompt_visual(
    descricao: str,
    segmento: str,
    cidade: str,
    formato: str,
    estilo: str = "",
    referencia: str = "",
) -> dict:
    """Usa Claude para criar prompt visual otimizado a partir da descrição do pedido."""
    formato_info = FORMATOS.get(formato, FORMATOS["instagram_feed"])

    prompt = f"""Crie um prompt de geração de imagem para:

CLIENTE: {segmento} — {cidade}
PEDIDO: {descricao}
FORMATO: {formato_info["descricao"]}
ESTILO/REFERÊNCIA: {estilo or "Foto realista profissional"}
OBSERVAÇÃO EXTRA: {referencia or "Nenhuma"}

Crie um prompt detalhado em inglês que produza uma imagem profissional e eficaz
para marketing deste serviço local. Use a ferramenta 'submeter_prompt_visual'."""

    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=[PROMPT_TOOL],
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "submeter_prompt_visual":
            return block.input

    return {"prompt_geracao": descricao, "justificativa": "", "sugestao_legenda": "", "hashtags": []}


def gerar_post(
    descricao: str,
    segmento: str,
    cidade: str,
    formato: str = "instagram_feed",
    provider: str = "openai",
    nome_arquivo: str = "post",
    estilo: str = "",
    referencia: str = "",
) -> dict:
    """
    Gera uma imagem de post do zero.
    1. Claude cria o prompt visual otimizado
    2. OpenAI ou Gemini gera a imagem
    Retorna dict com caminho da imagem e metadados.
    """
    print(f"\n[Designer] Criando prompt visual para: {descricao[:60]}...")

    prompt_data = _criar_prompt_visual(descricao, segmento, cidade, formato, estilo, referencia)
    prompt_geracao = prompt_data.get("prompt_geracao", descricao)

    formato_info = FORMATOS.get(formato, FORMATOS["instagram_feed"])
    tamanho = formato_info.get("tamanho", "1024x1024")

    print(f"[Designer] Gerando imagem via {provider.upper()}...")
    caminho = gerar_imagem(
        prompt=prompt_geracao,
        nome_arquivo=nome_arquivo,
        provider=provider,
        tamanho=tamanho,
        qualidade="standard",
    )

    return {
        "caminho": str(caminho),
        "prompt_usado": prompt_geracao,
        "justificativa": prompt_data.get("justificativa", ""),
        "sugestao_legenda": prompt_data.get("sugestao_legenda", ""),
        "hashtags": prompt_data.get("hashtags", []),
        "formato": formato,
        "provider": provider,
    }


def gerar_variacao(
    caminho_original: str,
    variacao: str,
    provider: str = "openai",
) -> Path:
    """
    Gera uma variação de imagem existente com instrução específica.
    Ex: variacao="versão com fundo azul escuro em vez de branco"
    """
    prompt = (
        f"Create a variation of an image for a Brazilian local service company. "
        f"Variation requested: {variacao}. "
        f"Maintain professional quality, photorealistic style."
    )
    return gerar_imagem(
        prompt=prompt,
        nome_arquivo=Path(caminho_original).stem + "_var",
        provider=provider,
    )


# ─── TEMPLATES DE PEDIDO ──────────────────────────────────────────────────────

TEMPLATES_POST = {
    "antes_depois": "Foto de antes e depois de serviço de {segmento} executado com sucesso. Antes: problema visível. Depois: serviço concluído, ambiente limpo.",
    "tecnico_em_acao": "Técnico profissional uniformizado executando serviço de {segmento} com equipamento especializado.",
    "depoimento_visual": "Post estilo depoimento: cliente satisfeito com serviço de {segmento}, fundo clean, texto de avaliação 5 estrelas.",
    "promocional": "Arte promocional para serviço de {segmento} com destaque no preço, urgência e chamada para ação.",
    "dica_educativa": "Post educativo com dica de prevenção relacionada a {segmento}. Estilo infográfico clean.",
    "equipe": "Foto da equipe de técnicos de {segmento}, uniformizados, com equipamentos, postura profissional.",
}


if __name__ == "__main__":
    resultado = gerar_post(
        descricao="Foto de técnico de desentupimento chegando rápido na residência do cliente, com van da empresa",
        segmento="desentupidora",
        cidade="São Paulo - Zona Sul",
        formato="instagram_feed",
        provider="openai",
        nome_arquivo="desentup_chegada",
    )
    print(f"\nImagem salva em: {resultado['caminho']}")
    print(f"Legenda sugerida: {resultado['sugestao_legenda']}")
    print(f"Hashtags: {' '.join(resultado['hashtags'])}")
