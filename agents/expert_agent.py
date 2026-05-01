"""
Agente Especialista em Google Ads — UnboundSales
Nível de análise: top tier (metodologia Pedro Sobral)
Capacidades: análise completa + diagnóstico + aplicação de melhorias com confirmação
"""
import json
import sys
import os
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from config.settings import ANTHROPIC_API_KEY, DEFAULT_MODEL

client_ai = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ─── DEFINIÇÃO DAS FERRAMENTAS ─────────────────────────────────────────────────

TOOLS = [
    # ── LEITURA ──────────────────────────────────────────────────────────────
    {
        "name": "buscar_metricas_campanha",
        "description": (
            "Busca métricas gerais da campanha: impressões, cliques, CTR, CPC médio, "
            "custo, conversões, CPA, parcela de impressões de busca e parcela no topo. "
            "Use no início para ter o panorama geral."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string"},
                "dias": {"type": "integer", "enum": [7, 14, 30]},
            },
            "required": ["campaign_id", "dias"],
        },
    },
    {
        "name": "buscar_grupos_anuncios",
        "description": (
            "Busca todos os grupos de anúncios da campanha com métricas e CPC máximo atual. "
            "Essencial para avaliar estrutura e identificar grupos com CPA fora do alvo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string"},
                "dias": {"type": "integer", "enum": [7, 14, 30]},
            },
            "required": ["campaign_id", "dias"],
        },
    },
    {
        "name": "buscar_keywords",
        "description": (
            "Busca palavras-chave com métricas de desempenho E Quality Score completo "
            "(QS geral, QS de anúncio, QS de landing page, CTR esperado). "
            "Fundamental para diagnóstico de relevância e custo inflado."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string"},
                "dias": {"type": "integer", "enum": [7, 14, 30]},
            },
            "required": ["campaign_id", "dias"],
        },
    },
    {
        "name": "buscar_search_terms",
        "description": (
            "Busca os termos de busca REAIS que ativaram os anúncios. "
            "CRÍTICO: identifica termos irrelevantes para negativar e oportunidades de novas keywords. "
            "Sempre use para campanhas com match type Broad ou Phrase."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string"},
                "dias": {"type": "integer", "enum": [7, 14, 30]},
                "limite": {
                    "type": "integer",
                    "description": "Máximo de termos retornados (padrão: 150)",
                },
            },
            "required": ["campaign_id", "dias"],
        },
    },
    {
        "name": "buscar_anuncios",
        "description": (
            "Busca anúncios RSA com Ad Strength e métricas. "
            "Avalia qualidade dos criativos e identifica anúncios fracos (POOR/AVERAGE)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string"},
                "dias": {"type": "integer", "enum": [7, 14, 30]},
            },
            "required": ["campaign_id", "dias"],
        },
    },
    {
        "name": "buscar_performance_dispositivos",
        "description": (
            "Breakdown de performance por dispositivo (MOBILE, DESKTOP, TABLET). "
            "Para serviços de emergência, mobile costuma dominar. "
            "Use para embasar ajustes de bid por dispositivo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string"},
                "dias": {"type": "integer", "enum": [7, 14, 30]},
            },
            "required": ["campaign_id", "dias"],
        },
    },
    {
        "name": "buscar_performance_horarios",
        "description": (
            "Performance hora a hora (0h–23h). "
            "Identifica horários rentáveis e horários de puro desperdício de orçamento."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string"},
                "dias": {"type": "integer", "enum": [7, 14, 30]},
            },
            "required": ["campaign_id", "dias"],
        },
    },
    # ── MUTAÇÃO ──────────────────────────────────────────────────────────────
    {
        "name": "atualizar_orcamento_campanha",
        "description": (
            "Atualiza o orçamento diário da campanha. "
            "Use quando há impressões perdidas por orçamento > 20% "
            "OU quando há oportunidade clara de escala. "
            "Sempre elimine desperdício (negativos) antes de aumentar orçamento."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string"},
                "novo_orcamento_brl": {
                    "type": "number",
                    "description": "Novo orçamento diário em R$",
                },
                "justificativa": {
                    "type": "string",
                    "description": "Motivo específico com dados que embasam a decisão",
                },
            },
            "required": ["campaign_id", "novo_orcamento_brl", "justificativa"],
        },
    },
    {
        "name": "pausar_ativar_keyword",
        "description": (
            "Pausa ou ativa uma palavra-chave. "
            "Pause keywords com custo > 3x CPA meta e zero conversão, "
            "ou com Quality Score < 4 sem chance de melhoria a curto prazo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ad_group_id": {"type": "string"},
                "criterion_id": {"type": "string"},
                "keyword_texto": {
                    "type": "string",
                    "description": "Texto da keyword (para exibição na confirmação)",
                },
                "pausar": {
                    "type": "boolean",
                    "description": "true = pausar | false = ativar",
                },
                "justificativa": {"type": "string"},
            },
            "required": [
                "ad_group_id",
                "criterion_id",
                "keyword_texto",
                "pausar",
                "justificativa",
            ],
        },
    },
    {
        "name": "adicionar_negativos_campanha",
        "description": (
            "Adiciona lista de negativos em nível de campanha (broad negativo). "
            "Use após identificar termos irrelevantes nos search terms: "
            "empregos, cursos, DIY, marcas concorrentes (se não desejado), etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string"},
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de termos a negativar (sem o sinal de menos)",
                },
                "justificativa": {"type": "string"},
            },
            "required": ["campaign_id", "keywords", "justificativa"],
        },
    },
    {
        "name": "atualizar_lance_grupo",
        "description": (
            "Atualiza o CPC máximo de um grupo de anúncios. "
            "Aumente em grupos com bom CPA e parcela de impressão perdida por lances. "
            "Reduza em grupos com CPA muito acima da meta."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ad_group_id": {"type": "string"},
                "ad_group_nome": {
                    "type": "string",
                    "description": "Nome do grupo (para exibição na confirmação)",
                },
                "novo_cpc_brl": {"type": "number"},
                "justificativa": {"type": "string"},
            },
            "required": ["ad_group_id", "ad_group_nome", "novo_cpc_brl", "justificativa"],
        },
    },
]

MUTATION_TOOLS = {
    "atualizar_orcamento_campanha",
    "pausar_ativar_keyword",
    "adicionar_negativos_campanha",
    "atualizar_lance_grupo",
}

# ─── SYSTEM PROMPT ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Você é o Agente Especialista em Google Ads da UnboundSales.
Seu nível de rigor analítico e profundidade técnica é equivalente ao de Pedro Sobral — a maior referência em Google Ads no Brasil.

Você é especialista em campanhas de serviços locais de emergência no Brasil:
desentupidoras, gasistas, chaveiros, eletricistas, encanadores, vidraceiros, dedetizadoras e similares.

━━━ SUA METODOLOGIA OBRIGATÓRIA ━━━

▶ FASE 1 — COLETA COMPLETA DE DADOS
Antes de qualquer diagnóstico, colete TUDO usando as ferramentas disponíveis:
  ① Métricas gerais (30 dias) — panorama de eficiência
  ② Grupos de anúncios — estrutura e lances
  ③ Keywords — Quality Score completo + custo + conversão
  ④ Search Terms — OBRIGATÓRIO — a maior fonte de desperdício e oportunidade
  ⑤ Anúncios RSA — Ad Strength e performance
  ⑥ Dispositivos — mobile vs desktop vs tablet
  ⑦ Horários — pico de conversão vs horários de sangria

▶ FASE 2 — DIAGNÓSTICO ESTRUTURADO (com dados concretos)

📊 EFICIÊNCIA DO BUDGET
  • Parcela de impressões perdida por ORÇAMENTO > 20% → aumentar budget (mas só depois de limpar desperdício)
  • Parcela de impressões perdida por LANCES > 30% → CPC muito baixo ou QS ruim
  • Custo vs volume de conversões → calcule o CPA real e compare com benchmarks do segmento

🔑 QUALIDADE DAS KEYWORDS
  • QS ≤ 4 → crítico: pausar ou criar grupo dedicado com anúncio específico para a keyword
  • QS 5–6 → atenção: revisar anúncio e landing page para melhorar relevância
  • QS ≥ 7 → saudável: foco em volume e conversão
  • Keyword com custo > 3× CPA meta e zero conversão → pausar imediatamente
  • Match type BROAD sem negativos robustos → sangria de budget garantida

🔎 SEARCH TERMS — A MINA DE OURO
  • Categorize cada termo: relevante / irrelevante / oportunidade
  • Irrelevantes típicos para serviços de emergência: "emprego", "curso", "faculdade",
    "como fazer", "faça você mesmo", "DIY", "grátis", "preço", nomes de cidades distantes,
    termos de produto (não serviço), etc.
  • Termos irrelevantes com gasto → negativar IMEDIATAMENTE em nível de campanha (broad negativo)
  • Termos relevantes com boas conversões → adicionar como keyword EXACT

📝 ANÚNCIOS RSA
  • Ad Strength POOR ou AVERAGE → problema urgente: falta diversidade de títulos/descrições
  • CTR < 5% para pesquisa de alta intenção → anúncio sem urgência ou relevância
  • Títulos bons para emergências: keyword no início, urgência (24h, Agora, Imediato), benefício (Orçamento Grátis)
  • Descrições: prova social (anos de experiência, X clientes) + garantia + CTA forte
  • Sitelinks: mínimo 4 ativos (Sobre nós, Serviços, Contato, Área de cobertura)

📱 DISPOSITIVOS
  • Mobile para serviços de emergência: geralmente 65–80% do volume — NORMAL
  • Se CPA mobile > CPA desktop em > 40%: bid adjustment negativo em mobile (ex: -20%)
  • Se CPA mobile < CPA desktop: bid adjustment positivo em mobile (ex: +20%)
  • Tablet com custo alto e zero conversão: -100% bid adjustment (excluir)

⏰ HORÁRIOS
  • Identifique as 6h de maior conversão → essas são as horas de ouro
  • Identifique horários com gasto > R$ 10 e zero conversão ao longo de 30 dias → candidatos a redução
  • Para serviços 24h: geralmente 6h–22h têm melhor performance; madrugada pode ter CPA alto

▶ FASE 3 — RECOMENDAÇÕES PRIORIZADAS
Ordene por IMPACTO IMEDIATO × FACILIDADE DE IMPLEMENTAÇÃO:
  1. 🔴 CRÍTICO: Negativos (eliminam desperdício instantaneamente)
  2. 🔴 CRÍTICO: Pausar keywords que só gastam (CPA inaceitável)
  3. 🟡 IMPORTANTE: Ajuste de orçamento (se há impressões perdidas)
  4. 🟡 IMPORTANTE: Ajuste de lances por grupo (bid management)
  5. 🟢 MELHORIA: Feedback sobre anúncios RSA (orientação para o usuário melhorar)
  6. 🟢 MELHORIA: Recomendações estruturais (novos grupos, keywords a adicionar)

▶ FASE 4 — APLICAÇÃO
  • Use as ferramentas de mutação para cada melhoria aprovada
  • Após cada aplicação, informe o impacto esperado com números
  • Ao final, gere um resumo executivo: o que foi feito, o que está pendente, próximos passos

━━━ BENCHMARKS DO MERCADO BRASILEIRO — SERVIÇOS LOCAIS DE EMERGÊNCIA ━━━
  • CTR bom: > 6% | excelente: > 10%
  • CPA desentupidoras/gasistas: R$ 25–70 (depende do ticket médio)
  • CPA chaveiros/eletricistas: R$ 15–45
  • Quality Score mínimo aceitável para keywords principais: 7/10
  • Orçamento mínimo para dados confiáveis: R$ 30/dia

━━━ REGRAS QUE VOCÊ NUNCA QUEBRA ━━━
  • Nunca aumenta orçamento antes de limpar negativos — seria jogar dinheiro fora
  • Negativos sempre em nível de CAMPANHA (não apenas grupo), tipo broad
  • Decisões de pausar keywords: baseadas em dados, não em suposições
  • Sempre prefere 30 dias para decisões estruturais; 7 dias para tendências recentes
  • Apresenta cada recomendação com o dado que a justifica

Seja direto. Use dados reais. Quantifique tudo. O cliente paga por resultados, não por análises bonitas."""


# ─── EXECUÇÃO DAS FERRAMENTAS ──────────────────────────────────────────────────

def _executar_ferramenta(nome: str, parametros: dict, customer_id: str):
    from google.ads.googleads.errors import GoogleAdsException
    from tools.google_ads import (
        obter_metricas_campanha,
        obter_dados_grupos,
        obter_dados_keywords,
        obter_search_terms,
        obter_dados_anuncios,
        obter_performance_dispositivos,
        obter_performance_horarios,
        atualizar_orcamento_campanha,
        pausar_ativar_keyword,
        adicionar_keywords_negativas_campanha,
        atualizar_lance_grupo,
    )

    try:
        dispatch = {
            "buscar_metricas_campanha": lambda p: obter_metricas_campanha(
                customer_id, p["campaign_id"], p["dias"]
            ),
            "buscar_grupos_anuncios": lambda p: obter_dados_grupos(
                customer_id, p["campaign_id"], p["dias"]
            ),
            "buscar_keywords": lambda p: obter_dados_keywords(
                customer_id, p["campaign_id"], p["dias"]
            ),
            "buscar_search_terms": lambda p: obter_search_terms(
                customer_id, p["campaign_id"], p["dias"], p.get("limite", 150)
            ),
            "buscar_anuncios": lambda p: obter_dados_anuncios(
                customer_id, p["campaign_id"], p["dias"]
            ),
            "buscar_performance_dispositivos": lambda p: obter_performance_dispositivos(
                customer_id, p["campaign_id"], p["dias"]
            ),
            "buscar_performance_horarios": lambda p: obter_performance_horarios(
                customer_id, p["campaign_id"], p["dias"]
            ),
            "atualizar_orcamento_campanha": lambda p: atualizar_orcamento_campanha(
                customer_id, p["campaign_id"], p["novo_orcamento_brl"]
            ),
            "pausar_ativar_keyword": lambda p: pausar_ativar_keyword(
                customer_id, p["ad_group_id"], p["criterion_id"], p["pausar"]
            ),
            "adicionar_negativos_campanha": lambda p: adicionar_keywords_negativas_campanha(
                customer_id, p["campaign_id"], p["keywords"]
            ),
            "atualizar_lance_grupo": lambda p: atualizar_lance_grupo(
                customer_id, p["ad_group_id"], p["novo_cpc_brl"]
            ),
        }

        if nome not in dispatch:
            return {"erro": f"Ferramenta desconhecida: {nome}"}

        return dispatch[nome](parametros)

    except GoogleAdsException as e:
        return {"erro": f"Google Ads API: {e.failure.errors[0].message}"}
    except Exception as e:
        return {"erro": str(e)}


# ─── CONFIRMAÇÃO DE MUTAÇÕES ───────────────────────────────────────────────────

def _solicitar_confirmacao(nome: str, parametros: dict) -> bool:
    """Exibe a melhoria proposta e pede confirmação antes de aplicar."""
    SEP = "─" * 62

    print(f"\n{SEP}")
    print("  🔧 MELHORIA PROPOSTA PELO ESPECIALISTA")
    print(SEP)

    if nome == "atualizar_orcamento_campanha":
        print(f"  Ação      : Atualizar orçamento diário")
        print(f"  Campanha  : {parametros['campaign_id']}")
        print(f"  Novo valor: R$ {parametros['novo_orcamento_brl']:.2f}/dia")

    elif nome == "pausar_ativar_keyword":
        acao = "PAUSAR" if parametros["pausar"] else "ATIVAR"
        print(f"  Ação      : {acao} keyword")
        print(f"  Keyword   : [{parametros['keyword_texto']}]")
        print(f"  Grupo ID  : {parametros['ad_group_id']}")

    elif nome == "adicionar_negativos_campanha":
        kws = parametros["keywords"]
        print(f"  Ação      : Adicionar {len(kws)} negativo(s) à campanha")
        print(f"  Campanha  : {parametros['campaign_id']}")
        for kw in kws:
            print(f"    ✗ {kw}")

    elif nome == "atualizar_lance_grupo":
        print(f"  Ação      : Atualizar CPC máximo do grupo")
        print(f"  Grupo     : {parametros.get('ad_group_nome', parametros['ad_group_id'])}")
        print(f"  Novo CPC  : R$ {parametros['novo_cpc_brl']:.2f}")

    justificativa = parametros.get("justificativa", "")
    if justificativa:
        print(f"\n  Por quê   : {justificativa}")

    print(SEP)
    resp = input("\n  Aplicar esta melhoria? (s/N): ").strip().lower()
    return resp == "s"


# ─── LOOP PRINCIPAL DO AGENTE ──────────────────────────────────────────────────

def rodar_especialista(customer_id: str, campaign_id: str, nome_cliente: str):
    """
    Executa o agente especialista em modo interativo.
    O agente coleta dados, diagnostica e aplica melhorias aprovadas pelo usuário.
    """
    SEP = "═" * 62

    print(f"\n{SEP}")
    print(f"  AGENTE ESPECIALISTA GOOGLE ADS — {nome_cliente}")
    print(f"  Customer ID : {customer_id}")
    print(f"  Campaign ID : {campaign_id}")
    print(SEP)
    print(
        "\n  O agente irá coletar todos os dados da campanha e apresentar\n"
        "  diagnóstico completo. Para cada melhoria proposta, você decide\n"
        "  se quer aplicar ou não antes de qualquer alteração.\n"
        "\n  Digite 'sair' a qualquer momento para encerrar.\n"
    )

    mensagens = [
        {
            "role": "user",
            "content": (
                f"Analise COMPLETAMENTE a campanha do cliente '{nome_cliente}'.\n\n"
                f"Customer ID: {customer_id}\n"
                f"Campaign ID: {campaign_id}\n\n"
                "Sua missão:\n"
                "1. Colete TODOS os dados disponíveis (métricas, grupos, keywords, "
                "search terms, anúncios, dispositivos, horários).\n"
                "2. Faça um diagnóstico profundo e priorizado.\n"
                "3. Proponha e aplique as melhorias aprovadas, em ordem de impacto.\n\n"
                "Comece pela coleta de dados — não pule nenhuma fonte antes de concluir."
            ),
        }
    ]

    melhorias_aplicadas = []
    melhorias_recusadas = 0

    while True:
        resposta = client_ai.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=mensagens,
        )

        # Exibe texto do agente
        for bloco in resposta.content:
            if hasattr(bloco, "text") and bloco.text:
                print(f"\n{bloco.text}")

        if resposta.stop_reason == "end_turn":
            break

        if resposta.stop_reason != "tool_use":
            break

        # Registra a resposta do assistente (incluindo tool_use blocks)
        mensagens.append({"role": "assistant", "content": resposta.content})

        tool_results = []
        for bloco in resposta.content:
            if bloco.type != "tool_use":
                continue

            nome = bloco.name
            params = bloco.input

            if nome in MUTATION_TOOLS:
                confirmado = _solicitar_confirmacao(nome, params)
                if confirmado:
                    print("  Aplicando...", end="", flush=True)
                    resultado = _executar_ferramenta(nome, params, customer_id)
                    if "erro" not in resultado:
                        print(" ✅")
                        melhorias_aplicadas.append(
                            params.get(
                                "keyword_texto",
                                params.get(
                                    "ad_group_nome",
                                    nome.replace("_", " "),
                                ),
                            )
                        )
                    else:
                        print(f" ❌ {resultado['erro']}")
                else:
                    resultado = {"cancelado": True, "motivo": "Usuário recusou."}
                    melhorias_recusadas += 1
                    print("  ↩  Não aplicado.")
            else:
                print(f"  [coleta] {nome}...", end="", flush=True)
                resultado = _executar_ferramenta(nome, params, customer_id)
                qtd = len(resultado) if isinstance(resultado, list) else "ok"
                print(f" {qtd}")

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": bloco.id,
                    "content": json.dumps(resultado, ensure_ascii=False, default=str),
                }
            )

        mensagens.append({"role": "user", "content": tool_results})

    # Resumo final
    print(f"\n{SEP}")
    print(f"  SESSÃO ENCERRADA — {nome_cliente}")
    print(f"  Melhorias aplicadas : {len(melhorias_aplicadas)}")
    if melhorias_aplicadas:
        for m in melhorias_aplicadas:
            print(f"    ✅ {m}")
    print(f"  Melhorias recusadas : {melhorias_recusadas}")
    print(SEP)


# ─── MODO DASHBOARD (sem input(), retorna estruturas para o Streamlit) ─────────

_DASHBOARD_ANALYSIS_TOOL = {
    "name": "submeter_analise_dashboard",
    "description": "Submete análise estruturada da campanha com recomendações aplicáveis via API",
    "input_schema": {
        "type": "object",
        "properties": {
            "resumo_executivo": {"type": "string"},
            "score_campanha": {"type": "integer", "minimum": 1, "maximum": 10},
            "pontos_criticos": {"type": "array", "items": {"type": "string"}},
            "pontos_positivos": {"type": "array", "items": {"type": "string"}},
            "recomendacoes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "prioridade": {
                            "type": "string",
                            "enum": ["CRITICO", "IMPORTANTE", "MELHORIA"],
                        },
                        "categoria": {"type": "string"},
                        "titulo": {"type": "string"},
                        "justificativa": {"type": "string"},
                        "impacto_esperado": {"type": "string"},
                        "acao": {"type": "string"},
                        "parametros": {"type": "object"},
                    },
                    "required": ["id", "prioridade", "titulo", "justificativa",
                                 "impacto_esperado", "acao"],
                },
            },
        },
        "required": ["resumo_executivo", "score_campanha", "pontos_criticos",
                     "pontos_positivos", "recomendacoes"],
    },
}


def coletar_dados_campanha(customer_id: str, campaign_id: str,
                            progress_cb=None) -> dict:
    """
    Coleta todos os 7 conjuntos de dados da campanha via API Google Ads.
    progress_cb(pct: float, label: str) é chamado a cada etapa (para Streamlit progress bar).
    Retorna dict com todas as chaves: metricas, grupos, keywords, search_terms,
    anuncios, dispositivos, horarios.
    """
    from tools.google_ads import (
        obter_metricas_campanha,
        obter_dados_grupos,
        obter_dados_keywords,
        obter_search_terms,
        obter_dados_anuncios,
        obter_performance_dispositivos,
        obter_performance_horarios,
    )

    etapas = [
        ("métricas gerais",    lambda: obter_metricas_campanha(customer_id, campaign_id, 30)),
        ("grupos de anúncios", lambda: obter_dados_grupos(customer_id, campaign_id, 30)),
        ("keywords",           lambda: obter_dados_keywords(customer_id, campaign_id, 30)),
        ("search terms",       lambda: obter_search_terms(customer_id, campaign_id, 30)),
        ("anúncios RSA",       lambda: obter_dados_anuncios(customer_id, campaign_id, 30)),
        ("dispositivos",       lambda: obter_performance_dispositivos(customer_id, campaign_id, 30)),
        ("horários",           lambda: obter_performance_horarios(customer_id, campaign_id, 30)),
    ]
    chaves = ["metricas", "grupos", "keywords", "search_terms",
              "anuncios", "dispositivos", "horarios"]

    dados = {}
    total = len(etapas)
    for i, (label, fn) in enumerate(etapas):
        if progress_cb:
            progress_cb(i / total, label)
        dados[chaves[i]] = fn()

    if progress_cb:
        progress_cb(1.0, "concluído")

    return dados


def gerar_recomendacoes_json(dados: dict, nome_cliente: str,
                              campaign_id: str) -> dict:
    """
    Chama Claude com todos os dados coletados e força retorno de JSON estruturado
    via tool_use. Ideal para o dashboard (sem loops de input).
    Retorna o dict de análise completo.
    """
    prompt = (
        f"Analise os dados da campanha do cliente '{nome_cliente}' (ID: {campaign_id}).\n\n"
        f"DADOS COMPLETOS DA CAMPANHA (30 dias):\n"
        f"{json.dumps(dados, ensure_ascii=False, default=str)}\n\n"
        "Use a ferramenta 'submeter_analise_dashboard' com a análise completa.\n"
        "Para cada recomendação aplicável via API, preencha 'acao' com o nome exato da função "
        "(adicionar_negativos_campanha, pausar_ativar_keyword, atualizar_orcamento_campanha, "
        "atualizar_lance_grupo) e 'parametros' com todos os campos necessários para a chamada.\n"
        "Para recomendações informativas (ex: melhorar anúncios), use acao='informativo'.\n"
        "Seja específico: mencione valores reais (R$, %, IDs) em cada justificativa."
    )

    response = client_ai.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[_DASHBOARD_ANALYSIS_TOOL],
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in response.content:
        if (block.type == "tool_use"
                and block.name == "submeter_analise_dashboard"):
            return {
                "cliente": nome_cliente,
                "campaign_id": campaign_id,
                **block.input,
            }

    return {"erro": "Claude não gerou análise estruturada"}


def aplicar_melhorias(customer_id: str, recomendacoes_selecionadas: list) -> list:
    """
    Executa as mutações nas recomendações aprovadas pelo usuário no dashboard.
    Retorna lista de resultados: [{"id": ..., "titulo": ..., "sucesso": bool, "resultado": ...}]
    """
    resultados = []
    for rec in recomendacoes_selecionadas:
        acao = rec.get("acao", "informativo")
        if not acao or acao == "informativo":
            continue

        resultado = _executar_ferramenta(acao, rec.get("parametros", {}), customer_id)
        resultados.append({
            "id": rec.get("id", ""),
            "titulo": rec.get("titulo", acao),
            "sucesso": "erro" not in resultado,
            "resultado": resultado,
        })

    return resultados


# ─── EXECUÇÃO DIRETA ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    from config.settings import GOOGLE_ADS_LOGIN_CUSTOMER_ID

    cid = input("Customer ID (Enter para usar o padrão do .env): ").strip()
    customer_id = cid or GOOGLE_ADS_LOGIN_CUSTOMER_ID
    campaign_id = input("Campaign ID: ").strip()
    nome = input("Nome do cliente: ").strip() or "Cliente"

    rodar_especialista(customer_id, campaign_id, nome)
