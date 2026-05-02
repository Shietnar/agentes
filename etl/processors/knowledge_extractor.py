"""
Knowledge Extractor — usa Claude para transformar texto bruto em conhecimento estruturado.
Recebe transcrição/artigo e retorna conteúdo .md pronto para injeção no system prompt.
"""
import anthropic
import os
from typing import Optional

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


_PROMPT_EXTRAIR = """Você é um extrator de conhecimento especializado em marketing digital para serviços locais de emergência (desentupidoras, gasistas, chaveiros, eletricistas) no mercado brasileiro.

Receberá texto bruto (transcrição de vídeo ou artigo) e deverá extrair o CONHECIMENTO ACIONÁVEL relevante para o agente indicado.

**Agente alvo:** {agente}
**Tópico:** {topico}
**Fonte:** {fonte}

**Regras de extração:**
1. Extraia apenas o que for diretamente aplicável ao agente alvo e ao contexto de serviços locais brasileiros
2. Mantenha números, percentuais e benchmarks concretos
3. Converta para formato Markdown limpo com headers, bullets e tabelas quando apropriado
4. Adapte linguagem para pt-BR quando o original for em inglês
5. Máximo 3.000 palavras no output
6. Se o conteúdo não for relevante para o agente, retorne apenas: "## [sem conteúdo relevante]"
7. Inclua no topo: `# {titulo}` e uma linha com a fonte

**Texto bruto para processar:**
---
{texto}
---

Retorne apenas o Markdown extraído, sem explicações adicionais."""


def extrair_conhecimento(
    texto: str,
    agente: str,
    topico: str,
    fonte: str,
    titulo: str,
    model: str = "claude-sonnet-4-6",
) -> Optional[str]:
    """
    Usa Claude para extrair conhecimento estruturado de texto bruto.
    Retorna string Markdown ou None se texto muito curto.
    """
    if len(texto) < 200:
        return None

    # Limita input para controlar custo (primeiros 40k chars)
    texto_truncado = texto[:40_000]
    if len(texto) > 40_000:
        texto_truncado += "\n\n[... texto truncado para processamento ...]"

    prompt = _PROMPT_EXTRAIR.format(
        agente=agente,
        topico=topico,
        fonte=fonte,
        titulo=titulo,
        texto=texto_truncado,
    )

    try:
        client = _get_client()
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        conteudo = response.content[0].text.strip()

        # Descarta se o modelo indicou que não há conteúdo relevante
        if "[sem conteúdo relevante]" in conteudo:
            return None

        return conteudo
    except Exception as e:
        print(f"  [erro extração] {e}")
        return None


def consolidar_conhecimento(
    textos: list[dict],
    agente: str,
    topico: str,
    model: str = "claude-sonnet-4-6",
) -> Optional[str]:
    """
    Consolida múltiplos textos (ex: vídeos de uma playlist) em um único .md coerente.
    Cada item de textos deve ter {titulo, conteudo/transcricao}.
    """
    if not textos:
        return None

    partes = []
    for item in textos:
        titulo = item.get("titulo", "Sem título")
        corpo = item.get("transcricao") or item.get("conteudo", "")
        if corpo and len(corpo) > 200:
            partes.append(f"### {titulo}\n{corpo[:8_000]}")

    if not partes:
        return None

    texto_combinado = "\n\n---\n\n".join(partes)

    prompt = f"""Você é um extrator de conhecimento especializado em marketing digital para serviços locais de emergência no mercado brasileiro.

Receberá múltiplos textos (transcrições/artigos) sobre um mesmo tópico e deverá criar um documento de conhecimento consolidado em Markdown.

**Agente alvo:** {agente}
**Tópico:** {topico}

**Regras:**
1. Consolide insights repetidos (não duplique)
2. Mantenha números, percentuais e benchmarks concretos
3. Organize com headers claros, bullets e tabelas
4. Linguagem pt-BR
5. Máximo 4.000 palavras
6. Comece com `# {topico.replace("_", " ").title()} — Conhecimento Consolidado`

**Textos para consolidar:**
---
{texto_combinado[:50_000]}
---

Retorne apenas o Markdown consolidado."""

    try:
        client = _get_client()
        response = client.messages.create(
            model=model,
            max_tokens=5000,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"  [erro consolidação] {e}")
        return None
