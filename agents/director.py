"""
Agente Diretor — UnboundSales
Orquestra a equipe de especialistas de forma autônoma:
decide quais agentes acionar, formula perguntas específicas para cada um,
itera sobre as respostas quando necessário e entrega parecer integrado.

Usa agentic loop (tool use) — Claude controla o fluxo, não o código.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from config.settings import ANTHROPIC_API_KEY, DEFAULT_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ─── SYSTEM PROMPT ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Você é o Diretor da UnboundSales, agência de marketing digital especializada em serviços locais de emergência no Brasil.

Você lidera um time de especialistas sênior — cada um com expertise profunda e opiniões fortes. Seu papel é orquestrar, não adivinhar: você decide quem chamar, com qual pergunta, e sintetiza o resultado em um parecer que o cliente pode agir imediatamente.

━━━ SUA EQUIPE (perfis reais) ━━━

🎯 LUCAS — Estratégia de Negócio
  Sabe: posicionamento (4 estratégias para o setor), alavancas de crescimento, precificação com urgência premium,
  análise de concorrência, B2B para condomínios/imobiliárias, métricas de negócio (CAC, LTV, NPS)
  Acione quando: o problema é de negócio, posicionamento, crescimento ou quando o canal está certo mas o produto/oferta está errado

🔬 PEDRO — Google Ads
  Sabe: estrutura de conta para emergência, quando usar cada bid strategy (Manual → Max Conv → tCPA → tROAS),
  diagnóstico de Quality Score, análise de search terms, negativos essenciais do setor,
  benchmarks reais (CTR 8–15%, CPA R$30–80, CVR 15–35%), RSA pin strategy, Performance Max (quando NÃO usar)
  Acione quando: qualquer questão de tráfego pago, diagnóstico de campanha, métricas de Ads

✍️ RODRIGO — Copywriter RSA
  Sabe: frameworks PAS/AIDA/4Ps, psicologia do cliente em crise, ângulos por segmento (desentupidora ≠ gasista ≠ chaveiro),
  técnica RSA (30/90 chars, pins, variedade), fórmulas de headline testadas, o que NUNCA escrever
  Acione quando: precisa de copy nova, avaliação de anúncio existente ou alinhamento de mensagem entre canal e LP

🌐 ANA — Landing Pages & CRO
  Sabe: estrutura de LP para emergência (10 seções obrigatórias), hierarquia de trust signals,
  benchmarks de CVR (< 5% = problema grave, 15–35% = bom), diagnóstico por CVR vs CTR,
  erros fatais (sem tel: link, formulário longo, sem WhatsApp), SEO técnico básico, Core Web Vitals
  Acione quando: há URL para analisar, CVR está baixo ou a LP não está alinhada com a campanha

📱 ANALISTA SOCIAL — Mídias Sociais
  Sabe: algoritmo do Instagram (Reels > Carrossel > Feed), benchmarks de engajamento (3–8% para contas locais < 5k),
  5 pilares de conteúdo para o nicho, estratégia de hashtags, crescimento orgânico local,
  conexão entre social e funil de conversão (social = confiança, não lead direto)
  Acione quando: há handle do Instagram, questão de conteúdo ou estratégia de presença digital

━━━ SUA METODOLOGIA ━━━

1. DECODIFIQUE: o que está sendo pedido de fato? Há URL? Handle? Customer ID? Dados de campanha?
2. COLETE primeiro: se há URL → buscar_site antes de chamar Ana. Se há campanha → buscar_dados_google_ads antes de chamar Pedro. Especialistas com dados reais entregam análises 10x melhores.
3. ESCOLHA com precisão: qual especialista(s) esse pedido realmente precisa? Seja cirúrgico — não chame 5 quando 2 resolvem.
4. FORMULE perguntas com contexto: nunca repasse o pedido original. Reformule com os dados que você já coletou e o ângulo específico que aquele especialista deve responder.
5. ENCADEIE quando necessário: Pedro diagnostica a campanha → você usa esse diagnóstico para perguntar a Rodrigo onde a copy está fraca especificamente.
6. SINTETIZE com posição: ao final, você não é um compilador de opiniões — você toma posição sobre o que é mais importante e por quê.

━━━ REGRAS DE ORQUESTRAÇÃO ━━━

• Paralelo: quando as perguntas são independentes (Lucas sobre posicionamento + Ana sobre LP podem rodar juntos)
• Sequencial: quando há dependência (Pedro diagnostica → Rodrigo melhora copy com base no diagnóstico)
• Mínimo de especialistas: pedido pontual = 1–2 especialistas. Pedido amplo = 3–4. Raramente todos os 5.
• Nunca chame especialista sem contexto real na pergunta — "o que você acha disso?" não é uma pergunta profissional
• Se falta informação crítica (customer_id, URL, segmento), peça ao usuário antes de acionar o time

━━━ SEU PARECER FINAL ━━━

Sempre encerre com bloco estruturado:

## Parecer do Diretor

### Diagnóstico
[2–3 frases identificando o problema raiz — não os sintomas]

### Prioridades Imediatas (esta semana)
[máximo 5 ações, ordenadas por impacto × facilidade]

### Próximos 30 dias
[iniciativas por área, com responsável implícito]

### Ponto Crítico de Atenção
[1 coisa que, se ignorada, compromete tudo o mais]"""

# ─── FERRAMENTAS ─────────────────────────────────────────────────────────────

TOOLS = [
    # ── Especialistas ──────────────────────────────────────────────────────────
    {
        "name": "consultar_lucas",
        "description": (
            "Consulta Lucas, especialista em estratégia de negócio, posicionamento e mercado. "
            "Passe uma pergunta específica e contextualizada — não o pedido original do usuário."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pergunta": {
                    "type": "string",
                    "description": "Pergunta específica para Lucas sobre estratégia, mercado ou negócio"
                }
            },
            "required": ["pergunta"],
        },
    },
    {
        "name": "consultar_pedro",
        "description": (
            "Consulta Pedro, especialista em Google Ads (campanhas, keywords, lances, CTR, CPA, Quality Score). "
            "Se tiver dados da campanha, inclua-os na pergunta."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pergunta": {
                    "type": "string",
                    "description": "Pergunta específica para Pedro sobre Google Ads, com dados relevantes se disponíveis"
                }
            },
            "required": ["pergunta"],
        },
    },
    {
        "name": "consultar_rodrigo",
        "description": (
            "Consulta Rodrigo, especialista em copywriting (textos de anúncios RSA, headlines, legendas, CTA). "
            "Se tiver copy existente para avaliar, inclua-a na pergunta."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pergunta": {
                    "type": "string",
                    "description": "Pergunta específica para Rodrigo sobre copy, textos ou mensagem"
                }
            },
            "required": ["pergunta"],
        },
    },
    {
        "name": "consultar_ana",
        "description": (
            "Consulta Ana, especialista em landing pages e conversão (CRO, UX, mobile, SEO técnico). "
            "Se tiver dados do site ou LP, inclua-os na pergunta."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pergunta": {
                    "type": "string",
                    "description": "Pergunta específica para Ana sobre landing page, site ou conversão"
                }
            },
            "required": ["pergunta"],
        },
    },
    {
        "name": "consultar_social",
        "description": (
            "Consulta a Analista de Mídias Sociais (Instagram, TikTok, conteúdo, engajamento). "
            "Se tiver dados da conta, inclua-os na pergunta."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pergunta": {
                    "type": "string",
                    "description": "Pergunta específica sobre mídias sociais ou estratégia de conteúdo"
                }
            },
            "required": ["pergunta"],
        },
    },
    # ── Dados externos ────────────────────────────────────────────────────────
    {
        "name": "buscar_site",
        "description": (
            "Busca e analisa o conteúdo de um site ou landing page. "
            "Use ANTES de consultar especialistas quando o pedido mencionar uma URL. "
            "Retorna: título, meta description, H1s, CTAs, elementos de confiança, texto principal."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL completa do site (com https://)"}
            },
            "required": ["url"],
        },
    },
    {
        "name": "buscar_dados_google_ads",
        "description": (
            "Busca dados completos de performance de uma campanha Google Ads: "
            "métricas gerais, grupos, keywords com Quality Score, search terms, anúncios, dispositivos e horários. "
            "Use ANTES de consultar Pedro quando o pedido mencionar uma campanha."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Google Ads Customer ID (apenas dígitos)"},
                "campaign_id": {"type": "string", "description": "ID numérico da campanha"},
                "dias": {
                    "type": "integer",
                    "enum": [7, 14, 30],
                    "description": "Período de análise em dias",
                },
            },
            "required": ["customer_id", "campaign_id", "dias"],
        },
    },
    {
        "name": "buscar_instagram",
        "description": (
            "Formata contexto de análise para uma conta do Instagram. "
            "Use quando o pedido mencionar um handle ou conta do Instagram."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "handle": {"type": "string", "description": "Username do Instagram (com ou sem @)"},
                "info_adicional": {
                    "type": "string",
                    "description": "Informações adicionais conhecidas: seguidores, posts/semana, tipo de conteúdo, segmento",
                },
            },
            "required": ["handle"],
        },
    },
]

# ─── EXECUÇÃO DAS FERRAMENTAS ─────────────────────────────────────────────────

def _executar_ferramenta(nome: str, params: dict) -> dict | str:
    from agents.consulta import (
        chamar_agente,
        preparar_contexto_site,
        preparar_contexto_instagram,
    )

    # Especialistas
    agente_map = {
        "consultar_lucas":   "lucas",
        "consultar_pedro":   "pedro",
        "consultar_rodrigo": "rodrigo",
        "consultar_ana":     "ana",
        "consultar_social":  "social",
    }
    if nome in agente_map:
        return chamar_agente(agente_map[nome], params["pergunta"])

    # Dados externos
    if nome == "buscar_site":
        return preparar_contexto_site(params["url"])

    if nome == "buscar_instagram":
        return preparar_contexto_instagram(
            params["handle"],
            params.get("info_adicional", ""),
        )

    if nome == "buscar_dados_google_ads":
        from agents.expert_agent import coletar_dados_campanha
        import json as _json
        dados = coletar_dados_campanha(params["customer_id"], params["campaign_id"])
        return _json.dumps(dados, ensure_ascii=False, default=str)

    return {"erro": f"Ferramenta desconhecida: {nome}"}


# ─── LOOP PRINCIPAL ──────────────────────────────────────────────────────────

_ICONE = {
    "consultar_lucas":          "🎯",
    "consultar_pedro":          "🔬",
    "consultar_rodrigo":        "✍️",
    "consultar_ana":            "🌐",
    "consultar_social":         "📱",
    "buscar_site":              "🌐",
    "buscar_dados_google_ads":  "📊",
    "buscar_instagram":         "📸",
}

_LABEL = {
    "consultar_lucas":          "Lucas — Estratégia de Negócio",
    "consultar_pedro":          "Pedro — Google Ads",
    "consultar_rodrigo":        "Rodrigo — Copywriter",
    "consultar_ana":            "Ana — Landing Pages",
    "consultar_social":         "Analista Social — Mídias Sociais",
    "buscar_site":              "Buscando site",
    "buscar_dados_google_ads":  "Coletando dados Google Ads",
    "buscar_instagram":         "Preparando contexto Instagram",
}


def rodar_diretor(
    pedido: str,
    progress_cb=None,
    max_turns: int = 20,
) -> dict:
    """
    Executa o loop do Diretor até produzir o parecer final.

    progress_cb(etapa, tool_name, info) para atualizar UI:
      etapa: "inicio" | "tool_start" | "tool_done" | "fim"
      tool_name: nome da ferramenta
      info: dict com detalhes

    Retorna dict:
      parecer_final: str
      etapas: list[dict] — log de cada ferramenta chamada
    """
    mensagens = [{"role": "user", "content": pedido}]
    etapas = []

    if progress_cb:
        progress_cb("inicio", "", {"pedido": pedido})

    for _ in range(max_turns):
        resposta = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=mensagens,
        )

        if resposta.stop_reason == "end_turn":
            parecer = "".join(
                b.text for b in resposta.content if hasattr(b, "text") and b.text
            )
            if progress_cb:
                progress_cb("fim", "", {"parecer": parecer})
            return {"parecer_final": parecer, "etapas": etapas}

        if resposta.stop_reason != "tool_use":
            break

        mensagens.append({"role": "assistant", "content": resposta.content})

        resultados_tools = []
        for bloco in resposta.content:
            if bloco.type != "tool_use":
                continue

            nome = bloco.name
            params = bloco.input

            if progress_cb:
                progress_cb("tool_start", nome, {
                    "label": _LABEL.get(nome, nome),
                    "icone": _ICONE.get(nome, "🔧"),
                    "params": params,
                })

            resultado = _executar_ferramenta(nome, params)

            etapa = {
                "tool": nome,
                "label": _LABEL.get(nome, nome),
                "icone": _ICONE.get(nome, "🔧"),
                "input": params,
                "output": resultado,
                "is_agent": nome.startswith("consultar_"),
            }
            etapas.append(etapa)

            if progress_cb:
                progress_cb("tool_done", nome, etapa)

            resultados_tools.append({
                "type": "tool_result",
                "tool_use_id": bloco.id,
                "content": json.dumps(resultado, ensure_ascii=False, default=str),
            })

        mensagens.append({"role": "user", "content": resultados_tools})

    return {"parecer_final": "Sessão encerrada sem conclusão.", "etapas": etapas}
