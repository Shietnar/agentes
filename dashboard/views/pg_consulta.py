"""Consulta Livre — chat em grupo com os especialistas em tempo real."""
import streamlit as st
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.consulta import AGENTES


# ─── Helpers de chat ──────────────────────────────────────────────────────────

def _bubble_usuario(texto: str):
    with st.chat_message("user"):
        st.markdown(texto)


def _bubble_agente_inicio(agent_key: str) -> st.empty:
    """Cria chat bubble do agente e retorna placeholder para o texto."""
    ag = AGENTES.get(agent_key, {})
    label = ag.get("label", agent_key)
    icone = label.split(" ")[0]
    nome  = label.split("—")[-1].strip() if "—" in label else label
    cor   = ag.get("cor", "#3d5166")

    with st.chat_message("assistant", avatar=icone):
        st.markdown(
            f"<span style='color:{cor};font-weight:700;font-size:13px'>{label}</span>",
            unsafe_allow_html=True,
        )
        ph = st.empty()
    return ph


def _exibir_historico(historico: list):
    for msg in historico:
        if msg["tipo"] == "user":
            _bubble_usuario(msg["texto"])
        elif msg["tipo"] == "agente":
            ag = AGENTES.get(msg["agent_key"], {})
            label = ag.get("label", msg["agent_key"])
            icone = label.split(" ")[0]
            cor   = ag.get("cor", "#3d5166")
            with st.chat_message("assistant", avatar=icone):
                st.markdown(
                    f"<span style='color:{cor};font-weight:700;font-size:13px'>{label}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(msg["texto"])


# ─── Execução genérica com streaming ──────────────────────────────────────────

def _executar_chat(agentes_keys: list, mensagem: str, chave: str):
    """Chama agentes em sequência, exibindo cada resposta via streaming."""
    from agents.consulta import consultar_agentes

    _bubble_usuario(mensagem[:300] + ("..." if len(mensagem) > 300 else ""))

    placeholders: dict[str, st.empty] = {}

    # Cria todos os bubbles antecipadamente (mostram "digitando...")
    for k in agentes_keys:
        ph = _bubble_agente_inicio(k)
        ph.markdown("_digitando..._")
        placeholders[k] = ph

    def on_text(agent_key: str, texto_acumulado: str):
        ph = placeholders.get(agent_key)
        if ph:
            ph.markdown(texto_acumulado + "▌")

    def on_done(agent_key: str, label: str, texto: str):
        ph = placeholders.get(agent_key)
        if ph:
            ph.markdown(texto)

    resultados = consultar_agentes(
        agentes_keys,
        mensagem,
        callback=on_done,
        on_text=on_text,
    )

    # Salva histórico
    hist = st.session_state.get(f"{chave}_historico", [])
    hist.append({"tipo": "user", "texto": mensagem[:300]})
    for r in resultados:
        hist.append({"tipo": "agente", "agent_key": r["agent_key"], "texto": r["texto"]})
    st.session_state[f"{chave}_historico"] = hist
    st.session_state[f"{chave}_agentes_ativos"] = agentes_keys
    st.rerun()


# ─── RENDER PRINCIPAL ─────────────────────────────────────────────────────────

def render(cliente=None):
    st.markdown(
        "<h2 style='margin-bottom:4px'>💬 Consulta aos Especialistas</h2>"
        "<p style='color:#3d5166;font-size:13px;margin-bottom:16px'>"
        "Converse com a equipe em tempo real — veja cada resposta aparecer enquanto é gerada.</p>",
        unsafe_allow_html=True,
    )

    tab_livre, tab_site, tab_insta, tab_ads = st.tabs([
        "💬 Pergunta Livre",
        "🌐 Analisar Site",
        "📱 Analisar Instagram",
        "📊 Google Ads",
    ])

    with tab_livre:
        _render_livre()

    with tab_site:
        _render_site()

    with tab_insta:
        _render_instagram()

    with tab_ads:
        _render_google_ads()


# ─── ABA: PERGUNTA LIVRE ──────────────────────────────────────────────────────

def _render_livre():
    chave = "livre"
    todos_keys  = list(AGENTES.keys())
    todos_labels = [AGENTES[k]["label"] for k in todos_keys]
    label_para_key = {AGENTES[k]["label"]: k for k in todos_keys}

    # Área de chat
    chat_area = st.container()
    with chat_area:
        historico = st.session_state.get(f"{chave}_historico", [])
        _exibir_historico(historico)

    # Controles
    if historico:
        # Sessão ativa — mostra input de follow-up
        agentes_ativos = st.session_state.get(f"{chave}_agentes_ativos", todos_keys[:2])
        col_nova, col_info = st.columns([1, 3])
        col_nova.markdown("<br>", unsafe_allow_html=True)
        if col_nova.button("🔄 Nova conversa", key=f"nova_{chave}", use_container_width=True):
            st.session_state.pop(f"{chave}_historico", None)
            st.session_state.pop(f"{chave}_agentes_ativos", None)
            st.rerun()
        col_info.caption(
            f"Respondendo: {', '.join(AGENTES[k]['label'].split('—')[-1].strip() for k in agentes_ativos)}"
        )
        followup = st.chat_input("Faça uma pergunta de acompanhamento...", key=f"ci_{chave}")
        if followup and followup.strip():
            with chat_area:
                _executar_chat(agentes_ativos, followup.strip(), chave)
    else:
        # Sessão nova — mostra formulário
        col_sel, col_btn = st.columns([3, 1])
        with col_sel:
            sel_labels = st.multiselect(
                "Especialistas:", options=todos_labels, default=todos_labels[:2], key=f"sel_{chave}"
            )
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Todos", key=f"todos_{chave}", use_container_width=True):
                st.session_state[f"sel_{chave}"] = todos_labels
                st.rerun()

        agentes = [label_para_key[l] for l in sel_labels if l in label_para_key]

        pergunta = st.text_area(
            "Sua pergunta:",
            height=120,
            key=f"perg_{chave}",
            placeholder=(
                "Ex: Qual a melhor estratégia de Google Ads para desentupidora em SP com R$80/dia?\n"
                "Ex: Avalie esta copy: 'Desentupimento 24h • 45 min • Orçamento grátis'\n"
                "Ex: Como escalar uma conta que já tem CPA de R$45 mas está limitada por orçamento?"
            ),
        )

        if st.button("🚀 Consultar", type="primary", use_container_width=True, key=f"btn_{chave}"):
            if not agentes:
                st.error("Selecione pelo menos um especialista.")
            elif not pergunta.strip():
                st.error("Digite uma pergunta.")
            else:
                with chat_area:
                    _executar_chat(agentes, pergunta.strip(), chave)


# ─── ABA: ANALISAR SITE ───────────────────────────────────────────────────────

def _render_site():
    chave = "site"
    todos_keys   = list(AGENTES.keys())
    todos_labels = [AGENTES[k]["label"] for k in todos_keys]
    label_para_key = {AGENTES[k]["label"]: k for k in todos_keys}

    chat_area = st.container()
    with chat_area:
        _exibir_historico(st.session_state.get(f"{chave}_historico", []))

    if st.session_state.get(f"{chave}_historico"):
        col1, col2 = st.columns([1, 3])
        col1.markdown("<br>", unsafe_allow_html=True)
        if col1.button("🔄 Nova análise", key=f"nova_{chave}", use_container_width=True):
            st.session_state.pop(f"{chave}_historico", None)
            st.session_state.pop(f"{chave}_agentes_ativos", None)
            st.rerun()
        followup = st.chat_input("Pergunta de acompanhamento sobre o site...", key=f"ci_{chave}")
        agentes_ativos = st.session_state.get(f"{chave}_agentes_ativos", ["ana", "lucas"])
        if followup and followup.strip():
            with chat_area:
                _executar_chat(agentes_ativos, followup.strip(), chave)
        return

    sel_labels = st.multiselect(
        "Especialistas:", options=todos_labels,
        default=[AGENTES["ana"]["label"], AGENTES["lucas"]["label"]],
        key=f"sel_{chave}",
    )
    agentes = [label_para_key[l] for l in sel_labels if l in label_para_key]

    url = st.text_input("URL do site:", placeholder="https://www.exemplo.com.br", key=f"url_{chave}")
    pergunta_custom = st.text_area(
        "Pergunta específica (opcional):", height=60, key=f"perg_{chave}",
        placeholder="Ex: O que está faltando para aumentar a conversão?",
    )

    if st.button("🔍 Analisar site", type="primary", use_container_width=True, key=f"btn_{chave}"):
        if not agentes:
            st.error("Selecione pelo menos um especialista.")
        elif not url.strip():
            st.error("Informe a URL.")
        else:
            with st.spinner(f"Buscando conteúdo de {url}..."):
                from agents.consulta import preparar_contexto_site
                conteudo = preparar_contexto_site(url)
            pergunta = pergunta_custom or (
                "Analise este site na sua área de especialidade. "
                "Identifique os principais problemas, oportunidades e dê recomendações concretas."
            )
            mensagem = f"TAREFA: {pergunta}\n\n{conteudo}"
            with chat_area:
                _executar_chat(agentes, mensagem, chave)


# ─── ABA: ANALISAR INSTAGRAM ──────────────────────────────────────────────────

def _render_instagram():
    chave = "insta"
    todos_keys   = list(AGENTES.keys())
    todos_labels = [AGENTES[k]["label"] for k in todos_keys]
    label_para_key = {AGENTES[k]["label"]: k for k in todos_keys}

    chat_area = st.container()
    with chat_area:
        _exibir_historico(st.session_state.get(f"{chave}_historico", []))

    if st.session_state.get(f"{chave}_historico"):
        col1, _ = st.columns([1, 3])
        col1.markdown("<br>", unsafe_allow_html=True)
        if col1.button("🔄 Nova análise", key=f"nova_{chave}", use_container_width=True):
            st.session_state.pop(f"{chave}_historico", None)
            st.session_state.pop(f"{chave}_agentes_ativos", None)
            st.rerun()
        followup = st.chat_input("Pergunta de acompanhamento...", key=f"ci_{chave}")
        agentes_ativos = st.session_state.get(f"{chave}_agentes_ativos", ["social"])
        if followup and followup.strip():
            with chat_area:
                _executar_chat(agentes_ativos, followup.strip(), chave)
        return

    sel_labels = st.multiselect(
        "Especialistas:", options=todos_labels,
        default=[AGENTES["social"]["label"]],
        key=f"sel_{chave}",
    )
    agentes = [label_para_key[l] for l in sel_labels if l in label_para_key]

    col1, col2 = st.columns(2)
    handle  = col1.text_input("Handle do Instagram:", placeholder="@empresa", key=f"handle_{chave}")
    segmento = col2.text_input("Segmento:", placeholder="desentupidora, gasista...", key=f"seg_{chave}")
    info = st.text_area(
        "Informações adicionais:", height=60, key=f"info_{chave}",
        placeholder="Ex: 850 seguidores, 2x semana, fotos de antes/depois, zona sul SP",
    )
    pergunta_custom = st.text_area(
        "Pergunta específica (opcional):", height=55, key=f"perg_{chave}",
        placeholder="Ex: Como aumentar engajamento? Qual conteúdo priorizar?",
    )

    if st.button("📱 Analisar Instagram", type="primary", use_container_width=True, key=f"btn_{chave}"):
        if not agentes:
            st.error("Selecione pelo menos um especialista.")
        elif not handle.strip():
            st.error("Informe o handle do Instagram.")
        else:
            from agents.consulta import preparar_contexto_instagram
            ctx = preparar_contexto_instagram(handle, f"Segmento: {segmento}. {info}")
            pergunta = pergunta_custom or (
                "Analise a presença no Instagram desta empresa e dê seu parecer na sua especialidade."
            )
            mensagem = f"TAREFA: {pergunta}\n\n{ctx}"
            with chat_area:
                _executar_chat(agentes, mensagem, chave)


# ─── ABA: GOOGLE ADS ─────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def _carregar_contas_mcc():
    from config.settings import GOOGLE_ADS_LOGIN_CUSTOMER_ID
    from tools.google_ads import listar_contas_mcc
    mcc_id = (GOOGLE_ADS_LOGIN_CUSTOMER_ID or "").replace("-", "").strip()
    return listar_contas_mcc(mcc_id) if mcc_id else []


@st.cache_data(ttl=120, show_spinner=False)
def _carregar_campanhas_conta(customer_id: str):
    from tools.google_ads import listar_campanhas
    return listar_campanhas(customer_id)


def _render_google_ads():
    chave = "ads"
    todos_keys   = list(AGENTES.keys())
    label_para_key = {AGENTES[k]["label"]: k for k in todos_keys}

    chat_area = st.container()
    with chat_area:
        _exibir_historico(st.session_state.get(f"{chave}_historico", []))

    if st.session_state.get(f"{chave}_historico"):
        col1, col2 = st.columns([1, 3])
        col1.markdown("<br>", unsafe_allow_html=True)
        if col1.button("🔄 Nova análise", key=f"nova_{chave}", use_container_width=True):
            for k in [f"{chave}_historico", f"{chave}_agentes_ativos",
                      "ads_selecao", "ads_dados_raw"]:
                st.session_state.pop(k, None)
            st.rerun()
        followup = st.chat_input("Pergunta de acompanhamento sobre a campanha...", key=f"ci_{chave}")
        agentes_ativos = st.session_state.get(f"{chave}_agentes_ativos", ["pedro", "lucas"])
        contexto_salvo = st.session_state.get("ads_contexto_texto", "")
        if followup and followup.strip():
            mensagem = f"PERGUNTA DE ACOMPANHAMENTO: {followup.strip()}"
            if contexto_salvo:
                mensagem += f"\n\nCONTEXTO DOS DADOS (já coletados):\n{contexto_salvo[:4000]}"
            with chat_area:
                _executar_chat(agentes_ativos, mensagem, chave)
        return

    # ── Seleção de campanhas ──────────────────────────────────────────────────
    st.markdown(
        "<p style='font-size:11px;font-weight:700;text-transform:uppercase;"
        "letter-spacing:1px;color:#3d5166;margin-bottom:6px'>Selecionar contas e campanhas</p>",
        unsafe_allow_html=True,
    )

    if "ads_contas_mcc" not in st.session_state:
        with st.spinner("Carregando contas da MCC..."):
            try:
                st.session_state["ads_contas_mcc"] = _carregar_contas_mcc()
            except Exception as e:
                st.error(f"Erro ao acessar MCC: {e}")
                st.session_state["ads_contas_mcc"] = []

    contas_mcc = st.session_state.get("ads_contas_mcc", [])

    if not contas_mcc:
        st.warning("Nenhuma conta encontrada na MCC. Verifique as credenciais no `.env`.")
        return

    if "ads_selecao" not in st.session_state:
        st.session_state["ads_selecao"] = []

    col_conta, col_camp, col_dias, col_add = st.columns([3, 3, 1, 1])
    conta_opcoes = {f"{c['nome']} ({c['id']})": c for c in contas_mcc}
    conta_label_sel = col_conta.selectbox("Conta", list(conta_opcoes.keys()), key="ads_sel_conta")
    conta_sel = conta_opcoes[conta_label_sel]

    campanhas = []
    try:
        campanhas = _carregar_campanhas_conta(conta_sel["id"])
    except Exception as e:
        st.error(f"Erro ao carregar campanhas: {e}")

    camp_ativas  = [c for c in campanhas if c["status"] == "ENABLED"]
    camp_opcoes  = {
        f"{c['nome']} — R${c['orcamento_diario_brl']:.0f}/dia": c for c in camp_ativas
    } if camp_ativas else {}

    if camp_opcoes:
        camp_sel_label = col_camp.selectbox("Campanha", list(camp_opcoes.keys()), key="ads_sel_camp")
        camp_sel = camp_opcoes[camp_sel_label]
    else:
        col_camp.selectbox("Campanha", ["Nenhuma campanha ativa"], key="ads_sel_camp", disabled=True)
        camp_sel = None

    dias_sel = col_dias.selectbox("Período", [7, 14, 30], index=2, key="ads_sel_dias")
    col_add.markdown("<br>", unsafe_allow_html=True)
    if col_add.button("＋", use_container_width=True, key="ads_add_btn", disabled=camp_sel is None):
        nova = {
            "customer_id": conta_sel["id"],
            "campaign_id": camp_sel["id"],
            "label": f"{conta_sel['nome']} › {camp_sel['nome']}",
            "dias": dias_sel,
        }
        existentes = [(c["customer_id"], c["campaign_id"]) for c in st.session_state["ads_selecao"]]
        if (nova["customer_id"], nova["campaign_id"]) not in existentes:
            st.session_state["ads_selecao"].append(nova)
            st.rerun()

    selecao = st.session_state["ads_selecao"]
    for i, item in enumerate(selecao):
        col_info, col_rm = st.columns([5, 1])
        col_info.markdown(
            f"<div style='padding:6px 10px;background:#0f1117;"
            f"border:1px solid rgba(0,207,253,0.15);border-radius:6px;"
            f"font-size:12px;color:#94a3b8'>"
            f"<span style='color:#00CFFD;font-weight:600'>{item['label']}</span>"
            f" · {item['dias']} dias</div>",
            unsafe_allow_html=True,
        )
        if col_rm.button("✕", key=f"rm_{i}", use_container_width=True):
            st.session_state["ads_selecao"].pop(i)
            st.rerun()

    if not selecao:
        st.caption("Adicione pelo menos uma campanha acima.")

    st.divider()

    # ── Agentes e pergunta ────────────────────────────────────────────────────
    col_ag, col_q = st.columns([1, 2])
    with col_ag:
        sel_labels = st.multiselect(
            "Especialistas:",
            options=[AGENTES[k]["label"] for k in todos_keys],
            default=[AGENTES["pedro"]["label"], AGENTES["lucas"]["label"]],
            key="ads_agentes",
        )
    with col_q:
        pergunta_ads = st.text_area(
            "Pergunta específica (opcional):", height=80, key="ads_pergunta",
            placeholder=(
                "Ex: Onde está o maior desperdício de budget?\n"
                "Ex: Quais keywords devem ser pausadas imediatamente?"
            ),
        )

    col_btn1, col_btn2 = st.columns(2)
    iniciar = col_btn1.button(
        "📊 Analisar agora", type="primary", use_container_width=True,
        key="ads_analisar", disabled=not selecao,
    )
    if col_btn2.button("↺ Recarregar contas", use_container_width=True, key="ads_reload"):
        _carregar_contas_mcc.clear()
        _carregar_campanhas_conta.clear()
        st.session_state.pop("ads_contas_mcc", None)
        st.rerun()

    if iniciar:
        agentes_keys = [label_para_key[l] for l in sel_labels if l in label_para_key]
        if not agentes_keys:
            st.error("Selecione pelo menos um especialista.")
        else:
            _executar_ads_chat(selecao, agentes_keys, pergunta_ads, chat_area, chave)


def _executar_ads_chat(contas, agentes_keys, pergunta, chat_area, chave):
    from agents.consulta import comparar_contas_ads, coletar_e_formatar_ads

    barra = st.progress(0.0, text="Coletando dados da campanha...")
    todas_dados = []
    contexto_ads = ""

    try:
        if len(contas) == 1:
            conta = contas[0]
            dados, contexto_ads = coletar_e_formatar_ads(
                customer_id=conta["customer_id"],
                campaign_id=conta["campaign_id"],
                label=conta.get("label", ""),
                dias=conta.get("dias", 30),
                progress_cb=lambda p, l: barra.progress(p * 0.8, text=f"Coletando {l}..."),
            )
            todas_dados = [{"conta": conta, "dados": dados}]
        else:
            todas_dados, contexto_ads = comparar_contas_ads(
                contas,
                progress_cb=lambda p, l: barra.progress(p * 0.8, text=l),
            )
    except Exception as e:
        barra.empty()
        st.error(f"Erro ao coletar dados Google Ads: {e}")
        return

    barra.empty()
    st.session_state["ads_dados_raw"]    = todas_dados
    st.session_state["ads_contexto_texto"] = contexto_ads

    pergunta_final = pergunta or (
        "Analise os dados do Google Ads abaixo na sua área de especialidade. "
        "Identifique os principais problemas, oportunidades e priorize as ações."
    )
    if len(contas) > 1:
        pergunta_final += (
            "\n\nFaça uma análise COMPARATIVA das contas. "
            "Qual está mais eficiente? Onde está o maior desperdício?"
        )

    mensagem = f"TAREFA: {pergunta_final}\n\n{contexto_ads}"

    with chat_area:
        _executar_chat(agentes_keys, mensagem, chave)
