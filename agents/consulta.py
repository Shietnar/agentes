"""
Consulta Livre — UnboundSales
Chama qualquer agente com uma pergunta aberta, sem vínculo com cliente.
Suporta agentes Managed (via Anthropic API) e agentes diretos (client.messages.create).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from config.settings import (
    ANTHROPIC_API_KEY,
    MANAGED_AGENTS_ENVIRONMENT_ID,
    AGENT_LUCAS_ID,
    AGENT_PEDRO_ID,
    AGENT_RODRIGO_ID,
    AGENT_ANA_ID,
    AGENT_MODERADOR_ID,
    DEFAULT_MODEL,
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ─── CATÁLOGO DE AGENTES ─────────────────────────────────────────────────────

AGENTES = {
    "lucas": {
        "label": "🎯 Lucas — Estratégia de Negócio",
        "cor": "#1565C0",
        "tipo": "managed",
        "agent_id_key": "AGENT_LUCAS_ID",
    },
    "pedro": {
        "label": "🔬 Pedro — Google Ads",
        "cor": "#C62828",
        "tipo": "managed",
        "agent_id_key": "AGENT_PEDRO_ID",
    },
    "rodrigo": {
        "label": "✍️ Rodrigo — Copywriter RSA",
        "cor": "#2E7D32",
        "tipo": "managed",
        "agent_id_key": "AGENT_RODRIGO_ID",
    },
    "ana": {
        "label": "🌐 Ana — Landing Pages & Web",
        "cor": "#6A1B9A",
        "tipo": "managed",
        "agent_id_key": "AGENT_ANA_ID",
    },
    "moderador": {
        "label": "📋 Moderador — Síntese",
        "cor": "#37474F",
        "tipo": "managed",
        "agent_id_key": "AGENT_MODERADOR_ID",
    },
    "social": {
        "label": "📱 Analista de Mídias Sociais",
        "cor": "#E65100",
        "tipo": "direto",
        "system": None,  # carregado lazy de social_agent.py
    },
}

_AGENT_ID_MAP = {
    "AGENT_LUCAS_ID":     AGENT_LUCAS_ID,
    "AGENT_PEDRO_ID":     AGENT_PEDRO_ID,
    "AGENT_RODRIGO_ID":   AGENT_RODRIGO_ID,
    "AGENT_ANA_ID":       AGENT_ANA_ID,
    "AGENT_MODERADOR_ID": AGENT_MODERADOR_ID,
}


# ─── EXECUÇÃO DE TOOLS DOS AGENTES MANAGED ───────────────────────────────────

def _executar_tool_agent(tool_name: str, tool_input: dict) -> str:
    """Executa uma ferramenta chamada por um agente managed e retorna resultado como string."""
    try:
        if tool_name == "buscar_site":
            return preparar_contexto_site(tool_input["url"])

        if tool_name == "buscar_dados_campanha":
            from agents.expert_agent import coletar_dados_campanha
            import json as _json
            dados = coletar_dados_campanha(
                tool_input["customer_id"],
                tool_input["campaign_id"],
            )
            return _json.dumps(dados, ensure_ascii=False, default=str)

        if tool_name == "buscar_instagram":
            return preparar_contexto_instagram(
                tool_input["handle"],
                tool_input.get("info_adicional", ""),
            )

        return f"[Ferramenta '{tool_name}' não reconhecida]"

    except Exception as exc:
        return f"[Erro ao executar '{tool_name}': {exc}]"


def _extrair_tool_calls(stop_reason) -> list[dict]:
    """
    Extrai chamadas de ferramentas do stop_reason de um evento requires_action.
    Tenta múltiplos formatos possíveis da API (defensivo).
    Retorna lista de dicts: [{tool_use_id, name, input}]
    """
    calls = []

    # Formato 1: stop_reason.actions = [Action(tool_use_id, name, input)]
    for action in getattr(stop_reason, "actions", []) or []:
        tid  = getattr(action, "tool_use_id", None) or getattr(action, "id", None)
        name = getattr(action, "name", None)
        inp  = getattr(action, "input", {}) or {}
        if name:
            calls.append({"tool_use_id": tid, "name": name, "input": inp})

    if calls:
        return calls

    # Formato 2: stop_reason.action (singular)
    action = getattr(stop_reason, "action", None)
    if action:
        tid  = getattr(action, "tool_use_id", None) or getattr(action, "id", None)
        name = getattr(action, "name", None)
        inp  = getattr(action, "input", {}) or {}
        if name:
            calls.append({"tool_use_id": tid, "name": name, "input": inp})

    if calls:
        return calls

    # Formato 3: stop_reason.content = [block] onde block.type == "tool_use"
    for block in getattr(stop_reason, "content", []) or []:
        if getattr(block, "type", None) == "tool_use":
            calls.append({
                "tool_use_id": getattr(block, "id", None),
                "name": getattr(block, "name", None),
                "input": getattr(block, "input", {}) or {},
            })

    return calls


# ─── EXECUÇÃO VIA MANAGED AGENTS ─────────────────────────────────────────────

def _chamar_managed(agent_id: str, mensagem: str, on_text=None, on_tool=None) -> str:
    """
    Cria sessão efêmera, envia mensagem e retorna resposta completa do agente.
    on_text(texto_acumulado): chamado a cada novo token de texto.
    on_tool(etapa, name, dados):
        "connecting"  — sessão criada, aguardando primeiro evento
        "start"       — ferramenta chamada pelo agente
        "done"        — ferramenta retornou
        "thinking"    — agente processando resultado da ferramenta
        "text_start"  — agente começou a redigir resposta
    """
    if on_tool:
        on_tool("connecting", "", {})

    session = client.beta.sessions.create(
        agent=agent_id,
        environment_id=MANAGED_AGENTS_ENVIRONMENT_ID,
    )

    texto = ""
    _primeira_mensagem = True

    with client.beta.sessions.events.stream(session_id=session.id) as stream:
        client.beta.sessions.events.send(
            session_id=session.id,
            events=[{
                "type": "user.message",
                "content": [{"type": "text", "text": mensagem}],
            }],
        )
        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if block.type == "text":
                        if _primeira_mensagem and on_tool:
                            on_tool("text_start", "", {})
                            _primeira_mensagem = False
                        texto += block.text
                        if on_text:
                            on_text(texto)

            elif event.type == "session.status_terminated":
                break

            elif event.type == "session.status_idle":
                stop_reason = getattr(event, "stop_reason", None)
                stop_type   = getattr(stop_reason, "type", None)

                if stop_type == "requires_action":
                    tool_calls = _extrair_tool_calls(stop_reason)
                    if not tool_calls:
                        break

                    resultados = []
                    for tc in tool_calls:
                        if on_tool:
                            on_tool("start", tc["name"], tc["input"])
                        resultado_str = _executar_tool_agent(tc["name"], tc["input"])
                        if on_tool:
                            on_tool("done", tc["name"], resultado_str)
                        resultados.append({
                            "type": "tool_result",
                            "tool_use_id": tc["tool_use_id"],
                            "content": resultado_str,
                        })

                    _primeira_mensagem = True  # próximo bloco de texto é novo
                    if on_tool:
                        on_tool("thinking", "", {})

                    client.beta.sessions.events.send(
                        session_id=session.id,
                        events=resultados,
                    )
                else:
                    break

    return texto


# ─── EXECUÇÃO VIA API DIRETA ──────────────────────────────────────────────────

def _chamar_direto(system_prompt: str, mensagem: str) -> str:
    """Chama Claude com system prompt próprio (para agentes não-managed)."""
    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": mensagem}],
    )
    return response.content[0].text


# ─── INTERFACE PRINCIPAL ──────────────────────────────────────────────────────

def chamar_agente(agent_key: str, mensagem: str, cliente_id: int = None,
                  on_text=None, on_tool=None) -> str:
    """
    Chama um agente pelo key e retorna a resposta como texto.
    agent_key: "lucas" | "pedro" | "rodrigo" | "ana" | "moderador" | "social"
    cliente_id: se informado, injeta memória do cliente + permite salvar aprendizados
    """
    from agents.memory import carregar as carregar_memoria

    agente = AGENTES.get(agent_key)
    if not agente:
        raise ValueError(f"Agente '{agent_key}' não encontrado. Disponíveis: {list(AGENTES.keys())}")

    # Injeta memória persistente no início da mensagem
    memoria = carregar_memoria(agent_key, cliente_id)
    mensagem_completa = f"{memoria}\n\n{mensagem}" if memoria else mensagem

    if agente["tipo"] == "managed":
        agent_id = _AGENT_ID_MAP.get(agente["agent_id_key"])
        if not agent_id:
            raise ValueError(
                f"ID do agente {agent_key} não configurado no .env. "
                "Execute agents/setup_agents.py."
            )
        return _chamar_managed(agent_id, mensagem_completa, on_text=on_text, on_tool=on_tool)

    elif agente["tipo"] == "direto" and agent_key == "social":
        from agents.social_agent import SYSTEM_PROMPT
        if on_text:
            # Streaming via messages.stream for direct agents
            with client.messages.stream(
                model=DEFAULT_MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": mensagem_completa}],
            ) as stream:
                accumulated = ""
                for chunk in stream.text_stream:
                    accumulated += chunk
                    on_text(accumulated)
            return accumulated
        return _chamar_direto(SYSTEM_PROMPT, mensagem_completa)

    raise ValueError(f"Tipo de agente '{agente['tipo']}' não suportado.")


def debater_agentes(
    agent_keys: list[str],
    mensagem: str,
    on_r1_text=None,
    on_r1_done=None,
    on_r2_text=None,
    on_r2_done=None,
    on_sintese_text=None,
    on_sintese_done=None,
    on_tool=None,
) -> dict:
    """
    Debate em 3 etapas:
      Rodada 1 — cada agente responde de forma independente
      Rodada 2 — cada agente lê as respostas dos colegas e debate/complementa
      Síntese   — o Moderador consolida tudo num parecer integrado

    Callbacks:
      on_r1_text(agent_key, texto_acumulado)
      on_r1_done(agent_key, texto)
      on_r2_text(agent_key, texto_acumulado)
      on_r2_done(agent_key, texto)
      on_sintese_text(texto_acumulado)
      on_sintese_done(texto)
      on_tool(agent_key, etapa, name, dados)
    """
    # ── Rodada 1 ──────────────────────────────────────────────────────────────
    prompt_r1 = (
        "RODADA 1 — Análise Inicial Independente\n\n"
        f"{mensagem}\n\n"
        "Dê seu diagnóstico completo na sua área de especialidade. "
        "Seja direto e específico."
    )

    respostas_r1: dict[str, str] = {}
    for key in agent_keys:
        def _ot(t, k=key):
            if on_r1_text:
                on_r1_text(k, t)
        def _tool(etapa, name, dados, k=key):
            if on_tool:
                on_tool(k, etapa, name, dados)

        texto = chamar_agente(key, prompt_r1, on_text=_ot, on_tool=_tool)
        respostas_r1[key] = texto
        if on_r1_done:
            on_r1_done(key, texto)

    # ── Rodada 2 ──────────────────────────────────────────────────────────────
    respostas_r2: dict[str, str] = {}
    for key in agent_keys:
        outros_txt = "\n\n".join(
            f"**{AGENTES[k]['label']}:**\n{v}"
            for k, v in respostas_r1.items() if k != key
        )
        prompt_r2 = (
            "RODADA 2 — Debate com seus Colegas\n\n"
            f"PERGUNTA ORIGINAL:\n{mensagem}\n\n"
            f"SUA ANÁLISE DA RODADA 1:\n{respostas_r1[key]}\n\n"
            f"O QUE SEUS COLEGAS DISSERAM:\n{outros_txt}\n\n"
            "Agora debata diretamente com seus colegas:\n"
            "• Você concorda com o diagnóstico deles?\n"
            "• Há algum ponto que discorda ou quer aprofundar?\n"
            "• O que a análise deles muda ou complementa na sua visão?\n"
            "• Existe alguma interdependência entre as áreas que precisa ser resolvida junto?\n"
            "Seja direto — cite o colega pelo nome quando concordar ou discordar."
        )

        def _ot2(t, k=key):
            if on_r2_text:
                on_r2_text(k, t)
        def _tool2(etapa, name, dados, k=key):
            if on_tool:
                on_tool(k, etapa, name, dados)

        texto = chamar_agente(key, prompt_r2, on_text=_ot2, on_tool=_tool2)
        respostas_r2[key] = texto
        if on_r2_done:
            on_r2_done(key, texto)

    # ── Síntese do Diretor ────────────────────────────────────────────────────
    r1_fmt = "\n\n".join(f"**{AGENTES[k]['label']}:**\n{v}" for k, v in respostas_r1.items())
    r2_fmt = "\n\n".join(f"**{AGENTES[k]['label']}:**\n{v}" for k, v in respostas_r2.items())

    prompt_sintese = (
        "SÍNTESE FINAL — Parecer do Diretor\n\n"
        f"PERGUNTA ORIGINAL:\n{mensagem}\n\n"
        f"=== RODADA 1 — Análises Iniciais ===\n{r1_fmt}\n\n"
        f"=== RODADA 2 — Debate ===\n{r2_fmt}\n\n"
        "Com base em todo o debate acima, produza um parecer final integrado:\n"
        "1. Consensos — o que o time concorda como prioridade\n"
        "2. Divergências relevantes — onde as visões diferem e qual prevalece\n"
        "3. Plano de ação integrado — as ações concretas em ordem de prioridade, "
        "conectando as contribuições de cada área\n\n"
        "Seja decisivo. Este é o parecer final que guia a execução."
    )

    def _ot_s(t):
        if on_sintese_text:
            on_sintese_text(t)
    def _tool_s(etapa, name, dados):
        if on_tool:
            on_tool("moderador", etapa, name, dados)

    sintese = chamar_agente("moderador", prompt_sintese, on_text=_ot_s, on_tool=_tool_s)
    if on_sintese_done:
        on_sintese_done(sintese)

    return {"r1": respostas_r1, "r2": respostas_r2, "sintese": sintese}


def consultar_agentes(
    agent_keys: list[str],
    mensagem: str,
    callback=None,
    on_text=None,
    on_tool=None,
) -> list[dict]:
    """
    Chama múltiplos agentes em sequência com a mesma mensagem.
    callback(agent_key, label, texto): chamado após cada resposta completa.
    on_text(agent_key, texto_acumulado): streaming token a token.
    on_tool(agent_key, etapa, name, dados): eventos de ferramenta/status.
    """
    resultados = []
    for key in agent_keys:
        agente = AGENTES[key]

        def _on_text(t, k=key):
            if on_text:
                on_text(k, t)

        def _on_tool(etapa, name, dados, k=key):
            if on_tool:
                on_tool(k, etapa, name, dados)

        texto = chamar_agente(
            key, mensagem,
            on_text=_on_text if on_text else None,
            on_tool=_on_tool if on_tool else None,
        )
        resultados.append({
            "agent_key": key,
            "label": agente["label"],
            "cor": agente["cor"],
            "texto": texto,
        })
        if callback:
            callback(key, agente["label"], texto)
    return resultados


# ─── PREPARAÇÃO DE CONTEXTO ───────────────────────────────────────────────────

def preparar_contexto_site(url: str) -> str:
    """
    Busca o conteúdo de um site e formata como contexto para os agentes.
    Retorna string pronta para incluir no prompt.
    """
    from tools.html_fetcher import fetch_html, extrair_metadados, extrair_texto_visivel

    resultado = fetch_html(url)
    if "erro" in resultado:
        return f"[ERRO ao acessar o site: {resultado['erro']}]"

    html = resultado["html"]
    meta = extrair_metadados(html)
    texto = extrair_texto_visivel(html, max_chars=5000)

    linhas = [
        f"URL ANALISADA: {resultado.get('url_final', url)}",
        f"Título: {meta.get('title') or 'Não encontrado'}",
        f"Meta description: {meta.get('meta_description') or 'Ausente'}",
        f"H1s: {', '.join(meta.get('h1s', [])) or 'Nenhum'}",
        f"H2s: {', '.join(meta.get('h2s', [])) or 'Nenhum'}",
        f"Tem WhatsApp: {'Sim' if meta.get('tem_whatsapp') else 'Não'}",
        f"Telefones: {', '.join(meta.get('telefones_tel', [])) or 'Nenhum'}",
        f"Formulários: {meta.get('formularios', 0)}",
        f"CTAs encontrados: {', '.join(meta.get('ctas', [])) or 'Nenhum'}",
        f"Elementos de confiança: {', '.join(meta.get('trust_elements', [])) or 'Nenhum'}",
        f"Mobile-friendly: {'Sim' if meta.get('tem_viewport_meta') else 'Não'}",
        "",
        "─── TEXTO PRINCIPAL DA PÁGINA ───",
        texto,
    ]
    return "\n".join(linhas)


def preparar_contexto_instagram(handle: str, info_adicional: str = "") -> str:
    """
    Formata contexto para análise de uma conta do Instagram (modo manual, sem API).
    """
    return (
        f"CONTA DO INSTAGRAM A ANALISAR: @{handle.lstrip('@')}\n"
        f"Informações adicionais: {info_adicional or 'Não informadas'}\n\n"
        "Analise esta conta do Instagram com base no que você sabe sobre "
        "estratégias de social media para serviços locais no Brasil. "
        "Se não tiver dados específicos, forneça um diagnóstico e recomendações "
        "baseadas nas melhores práticas para o segmento informado."
    )


# ─── GOOGLE ADS ───────────────────────────────────────────────────────────────

def coletar_e_formatar_ads(
    customer_id: str,
    campaign_id: str,
    label: str = "",
    dias: int = 30,
    progress_cb=None,
) -> tuple[dict, str]:
    """
    Coleta todos os dados de uma campanha Google Ads e formata como texto para o prompt.
    Retorna (dados_raw, texto_formatado).
    progress_cb(pct, label) para barra de progresso do Streamlit.
    """
    import json
    from agents.expert_agent import coletar_dados_campanha

    dados = coletar_dados_campanha(customer_id, campaign_id, progress_cb)

    metricas = dados.get("metricas", {})
    grupos = dados.get("grupos", [])
    keywords = dados.get("keywords", [])
    search_terms = dados.get("search_terms", [])

    # Resumo compacto para o topo do contexto
    resumo = [
        f"{'─'*50}",
        f"CONTA: {label or customer_id}",
        f"Customer ID: {customer_id} | Campaign ID: {campaign_id} | Período: {dias} dias",
        f"{'─'*50}",
    ]
    if metricas:
        custo = metricas.get("custo_total_brl", 0)
        conv = metricas.get("conversoes", 0)
        resumo += [
            f"Custo: R$ {custo:.2f} | Cliques: {metricas.get('cliques', 0)} | "
            f"CTR: {metricas.get('ctr_pct', 0):.1f}%",
            f"Conversões: {conv} | CPA: R$ {metricas.get('cpa_brl', 0):.2f} | "
            f"CPC médio: R$ {metricas.get('cpc_medio_brl', 0):.2f}",
        ]

    qs_ruins = [k for k in keywords if isinstance(k.get("quality_score"), int) and k["quality_score"] <= 4]
    sem_conv = [k for k in keywords if k.get("custo_total_brl", 0) > 20 and k.get("conversoes", 0) == 0]
    resumo += [
        f"Keywords: {len(keywords)} | QS ≤ 4: {len(qs_ruins)} | "
        f"Keywords com gasto sem conversão: {len(sem_conv)}",
        f"Search terms analisados: {len(search_terms)}",
        f"Grupos de anúncios: {len(grupos)}",
        "",
    ]

    texto = "\n".join(resumo) + "\n\nDADOS COMPLETOS:\n" + json.dumps(dados, ensure_ascii=False, default=str)
    return dados, texto


def comparar_contas_ads(
    contas: list[dict],
    progress_cb=None,
) -> tuple[list[dict], str]:
    """
    Coleta dados de múltiplas contas/campanhas e gera contexto comparativo.
    contas: [{"customer_id": str, "campaign_id": str, "label": str, "dias": int}]
    Retorna (lista_de_dados_raw, texto_comparativo).
    """
    import json

    todas_dados = []
    blocos = []

    total = len(contas)
    for i, conta in enumerate(contas):
        if progress_cb:
            progress_cb(i / total, f"Coletando {conta.get('label', conta['customer_id'])}...")
        dados, texto = coletar_e_formatar_ads(
            customer_id=conta["customer_id"],
            campaign_id=conta["campaign_id"],
            label=conta.get("label", ""),
            dias=conta.get("dias", 30),
        )
        todas_dados.append({"conta": conta, "dados": dados})
        blocos.append(texto)

    if progress_cb:
        progress_cb(1.0, "Coleta concluída")

    contexto = "ANÁLISE COMPARATIVA DE MÚLTIPLAS CONTAS GOOGLE ADS\n\n"
    contexto += "\n\n".join(blocos)
    return todas_dados, contexto


def analisar_ads_com_pedro(
    contexto_ads: str,
    pergunta_adicional: str = "",
    customer_id: str = "",
    campaign_id: str = "",
) -> dict:
    """
    Envia os dados do Google Ads para o Pedro (Especialista Google Ads) via Managed Agent.
    Retorna texto de análise livre (para uso na consulta).
    Para análise estruturada com recomendações aplicáveis, use expert_agent.gerar_recomendacoes_json().
    """
    mensagem = (
        "Analise os dados abaixo do Google Ads na sua área de especialidade.\n"
    )
    if pergunta_adicional:
        mensagem += f"\nPERGUNTA ESPECÍFICA: {pergunta_adicional}\n"
    mensagem += f"\n{contexto_ads}"

    texto = _chamar_managed(_AGENT_ID_MAP["AGENT_PEDRO_ID"], mensagem)
    return {"label": AGENTES["pedro"]["label"], "cor": AGENTES["pedro"]["cor"], "texto": texto}
