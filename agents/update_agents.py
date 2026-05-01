"""
Update Agents — UnboundSales
Adiciona ferramentas próprias a cada agente managed já existente.
Execute após o setup inicial:
    python agents/update_agents.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from config.settings import (
    ANTHROPIC_API_KEY,
    AGENT_LUCAS_ID,
    AGENT_PEDRO_ID,
    AGENT_RODRIGO_ID,
    AGENT_ANA_ID,
    AGENT_MODERADOR_ID,
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ─── FERRAMENTAS POR AGENTE ───────────────────────────────────────────────────

# Pedro: acesso direto a dados de Google Ads
_TOOLS_PEDRO = [
    {
        "type": "custom",
        "name": "buscar_dados_campanha",
        "description": (
            "Busca métricas completas de uma campanha Google Ads: "
            "custo, cliques, CTR, CPA, conversões, keywords com Quality Score, "
            "search terms e anúncios. Use quando receber customer_id e campaign_id."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Google Ads Customer ID (somente dígitos)",
                },
                "campaign_id": {
                    "type": "string",
                    "description": "ID numérico da campanha Google Ads",
                },
                "dias": {
                    "type": "integer",
                    "enum": [7, 14, 30],
                    "description": "Período de análise em dias (padrão: 30)",
                },
            },
            "required": ["customer_id", "campaign_id", "dias"],
        },
    },
]

# Ana: acesso direto ao conteúdo de sites e landing pages
_TOOLS_ANA = [
    {
        "type": "custom",
        "name": "buscar_site",
        "description": (
            "Busca e analisa o conteúdo de um site ou landing page. "
            "Retorna: título, meta description, H1s, H2s, CTAs, elementos de confiança, "
            "presença de WhatsApp/telefone, formulários e texto principal. "
            "Use quando receber uma URL para análise."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL completa do site (com https://)",
                },
            },
            "required": ["url"],
        },
    },
]

# Social (se for migrada para managed): acesso a contexto de Instagram
_TOOLS_SOCIAL = [
    {
        "type": "custom",
        "name": "buscar_instagram",
        "description": (
            "Formata contexto para análise de uma conta do Instagram. "
            "Use quando receber um username/handle para analisar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "handle": {
                    "type": "string",
                    "description": "Username do Instagram (com ou sem @)",
                },
                "info_adicional": {
                    "type": "string",
                    "description": "Informações extras: seguidores, posts/semana, tipo de conteúdo, segmento",
                },
            },
            "required": ["handle"],
        },
    },
]

# Lucas, Rodrigo e Moderador: sem tools específicas (análise e síntese por raciocínio)
_TOOLS_SEM = []

# ─── MAPA DE AGENTES → TOOLS ──────────────────────────────────────────────────

CONFIGURACOES = [
    {"nome": "Pedro (Google Ads)",    "id": AGENT_PEDRO_ID,     "tools": _TOOLS_PEDRO},
    {"nome": "Ana (Landing Pages)",   "id": AGENT_ANA_ID,       "tools": _TOOLS_ANA},
    {"nome": "Lucas (Negócio)",       "id": AGENT_LUCAS_ID,     "tools": _TOOLS_SEM},
    {"nome": "Rodrigo (Copywriter)",  "id": AGENT_RODRIGO_ID,   "tools": _TOOLS_SEM},
    {"nome": "Moderador (Síntese)",   "id": AGENT_MODERADOR_ID, "tools": _TOOLS_SEM},
]

# ─── ATUALIZAÇÃO ──────────────────────────────────────────────────────────────

def atualizar_agente(nome: str, agent_id: str, tools: list) -> bool:
    if not agent_id:
        print(f"  ⚠️  {nome}: ID não configurado no .env — pulando")
        return False
    try:
        # Busca versão atual (obrigatória para update)
        agente_atual = client.beta.agents.retrieve(agent_id)
        versao = agente_atual.version

        update_kwargs = {"version": versao}
        if tools:
            update_kwargs["tools"] = tools

        client.beta.agents.update(agent_id, **update_kwargs)
        descricao = f"{len(tools)} tool(s)" if tools else "sem tools (reasoning puro)"
        print(f"  ✅ {nome}: v{versao} → atualizado — {descricao}")
        return True
    except Exception as e:
        print(f"  ❌ {nome}: erro — {e}")
        return False


if __name__ == "__main__":
    print("\n=== UNBOUND SALES — ATUALIZAÇÃO DE AGENTES ===\n")
    print("Adicionando ferramentas independentes a cada especialista...\n")

    ok = 0
    for cfg in CONFIGURACOES:
        if atualizar_agente(cfg["nome"], cfg["id"], cfg["tools"]):
            ok += 1

    print(f"\n{'='*48}")
    print(f"  {ok}/{len(CONFIGURACOES)} agentes atualizados com sucesso.")
    if ok < len(CONFIGURACOES):
        print("  Verifique os IDs no .env e tente novamente.")
    print(f"{'='*48}\n")
