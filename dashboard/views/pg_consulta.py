"""Consulta Livre — chat em grupo com os especialistas em tempo real."""
import time
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.consulta import AGENTES


# ─── Labels de ferramentas ────────────────────────────────────────────────────

_TOOL_LABEL = {
    "buscar_site":             ("🌐", "buscando site"),
    "buscar_dados_campanha":   ("📊", "consultando Google Ads"),
    "buscar_instagram":        ("📸", "coletando dados Instagram"),
    "buscar_dados_google_ads": ("📊", "consultando Google Ads"),
}


# ─── Terminal de eventos ──────────────────────────────────────────────────────

class Terminal:
    """
    Terminal ao vivo que mostra cada etapa da execução dos agentes.
    Atualiza um st.empty() com um bloco de código monoespaçado.
    """
    def __init__(self, placeholder):
        self._ph = placeholder
        self._linhas: list[str] = []
        self._t0 = time.time()
        self._render()

    def _ts(self) -> str:
        return f"{time.time() - self._t0:5.1f}s"

    def add(self, linha: str):
        self._linhas.append(linha)
        self._render()

    def _render(self):
        visivel = self._linhas[-40:] if self._linhas else ["  aguardando..."]
        self._ph.code("\n".join(visivel), language=None)

    # ── Callbacks de evento ───────────────────────────────────────────────────

    def on_tool(self, agent_key: str, etapa: str, name: str, dados):
        ag = AGENTES.get(agent_key, {})
        nome = ag.get("label", agent_key).split("—")[-1].strip()

        if etapa == "connecting":
            self.add(f"  {self._ts()}  {nome}  →  abrindo sessão...")

        elif etapa == "text_start":
            self.add(f"  {self._ts()}  {nome}  →  ✏️  redigindo resposta...")

        elif etapa == "thinking":
            self.add(f"  {self._ts()}  {nome}  →  💭  processando dados recebidos...")

        elif etapa == "start":
            icone, label = _TOOL_LABEL.get(name, ("⚙️", name))
            self.add(f"  {self._ts()}  {nome}  →  {icone}  {label}...")

        elif etapa == "done":
            chars = len(str(dados)) if dados else 0
            icone, label = _TOOL_LABEL.get(name, ("⚙️", name))
            self.add(f"  {self._ts()}  {nome}  →  ✓  {label}  ({chars:,} chars)")

    def on_concluido(self, agent_key: str, texto: str):
        ag = AGENTES.get(agent_key, {})
        nome = ag.get("label", agent_key).split("—")[-1].strip()
        palavras = len(texto.split())
        self.add(f"  {self._ts()}  {nome}  →  ✓  concluído  ({palavras} palavras)")
        self.add("")

    def log_coleta(self, pct: float, label: str):
        self.add(f"  {self._ts()}  📊  {label}  ({pct*100:.0f}%)")


# ─── Helpers de chat ──────────────────────────────────────────────────────────

def _bubble_usuario(texto: str):
    with st.chat_message("user"):
        st.markdown(texto)


def _bubble_agente_inicio(agent_key: str) -> st.empty:
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


_RODADA_ESTILO = {
    "r1":     ("#1565C0", "🔵", "Rodada 1 — Análise Inicial"),
    "r2":     ("#F57F17", "🟡", "Rodada 2 — Debate"),
    "sintese":("#00CFFD", "🎬", "Síntese do Diretor"),
}


def _header_rodada(tipo: str):
    cor, icone, label = _RODADA_ESTILO.get(tipo, ("#3d5166", "•", tipo))
    st.markdown(
        f"<div style='margin:20px 0 10px;padding:8px 16px;"
        f"border-left:4px solid {cor};background:{cor}12;"
        f"border-radius:0 6px 6px 0;font-size:13px;font-weight:700;color:{cor}'>"
        f"{icone} {label}</div>",
        unsafe_allow_html=True,
    )


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
        elif msg["tipo"] == "header_rodada":
            _header_rodada(msg["rodada"])
        elif msg["tipo"] == "sintese":
            with st.chat_message("assistant", avatar="🎬"):
                st.markdown(
                    "<span style='color:#00CFFD;font-weight:700;font-size:13px'>"
                    "🎬 Síntese do Diretor</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(msg["texto"])


# ─── Execução com streaming + terminal ────────────────────────────────────────

def _executar_chat(agentes_keys: list, mensagem: str, chave: str, terminal: "Terminal | None" = None):
    """
    Chama agentes em sequência com streaming de texto e eventos de ferramentas.
    terminal: instância Terminal já criada (para reutilizar no fluxo de ads).
    """
    from agents.consulta import consultar_agentes

    _bubble_usuario(mensagem[:400] + ("..." if len(mensagem) > 400 else ""))

    # Cria bubbles antecipadamente
    placeholders: dict[str, st.empty] = {}
    for k in agentes_keys:
        ph = _bubble_agente_inicio(k)
        ph.markdown("_aguardando..._")
        placeholders[k] = ph

    # Terminal inline se não veio de fora
    if terminal is None:
        term_ph = st.empty()
        terminal = Terminal(term_ph)

    # ── Callbacks ────────────────────────────────────────────────────────────

    def on_text(agent_key: str, texto: str):
        ph = placeholders.get(agent_key)
        if ph:
            ph.markdown(texto + "▌")

    def on_tool(agent_key: str, etapa: str, name: str, dados):
        ph = placeholders.get(agent_key)
        ag = AGENTES.get(agent_key, {})

        # Atualiza bubble do agente com status visual
        if ph:
            if etapa == "connecting":
                ph.markdown("_conectando..._")
            elif etapa == "thinking":
                ph.markdown("_processando dados..._")
            elif etapa == "text_start":
                ph.markdown("_redigindo..._")
            elif etapa == "start":
                _, label = _TOOL_LABEL.get(name, ("⚙️", name))
                ph.markdown(f"_{label}..._")
            # "done" não altera bubble (texto de streaming substituirá)

        terminal.on_tool(agent_key, etapa, name, dados)

    def on_done(agent_key: str, label: str, texto: str):
        ph = placeholders.get(agent_key)
        if ph:
            ph.markdown(texto)
        terminal.on_concluido(agent_key, texto)

    # ── Execução ──────────────────────────────────────────────────────────────
    resultados = consultar_agentes(
        agentes_keys,
        mensagem,
        callback=on_done,
        on_text=on_text,
        on_tool=on_tool,
    )

    # Salva histórico
    hist = st.session_state.get(f"{chave}_historico", [])
    hist.append({"tipo": "user", "texto": mensagem[:400]})
    for r in resultados:
        hist.append({"tipo": "agente", "agent_key": r["agent_key"], "texto": r["texto"]})
    st.session_state[f"{chave}_historico"] = hist
    st.session_state[f"{chave}_agentes_ativos"] = agentes_keys
    st.rerun()


# ─── Debate em rodadas ────────────────────────────────────────────────────────

def _executar_debate(agentes_keys: list, mensagem: str, chave: str):
    """Rodada 1 → Rodada 2 (cada agente lê os colegas) → Síntese do Diretor."""
    from agents.consulta import debater_agentes

    _bubble_usuario(mensagem[:400] + ("..." if len(mensagem) > 400 else ""))

    hist: list[dict] = [{"tipo": "user", "texto": mensagem[:400]}]

    # Terminal
    st.markdown(
        "<p style='font-size:11px;font-weight:700;color:#3d5166;"
        "text-transform:uppercase;letter-spacing:1px;margin:8px 0 4px'>"
        "🖥️ Terminal</p>",
        unsafe_allow_html=True,
    )
    terminal = Terminal(st.empty())

    # ── estado de placeholders por rodada ─────────────────────────────────────
    placeholders_r1: dict[str, st.empty] = {}
    placeholders_r2: dict[str, st.empty] = {}
    ph_sintese: list = []          # lista de 1 elemento para mutabilidade em closure

    # ── Rodada 1 ──────────────────────────────────────────────────────────────
    _header_rodada("r1")
    hist.append({"tipo": "header_rodada", "rodada": "r1"})
    for k in agentes_keys:
        ph = _bubble_agente_inicio(k)
        ph.markdown("_aguardando..._")
        placeholders_r1[k] = ph

    # ── Rodada 2 (placeholders criados antecipadamente, ocultos via placeholder vazio) ─
    r2_header_ph = st.empty()      # onde vai aparecer o header da R2
    r2_bubbles_ph = st.empty()     # container para as bubbles da R2 (preenchido dinamicamente)
    sintese_header_ph = st.empty()
    sintese_bubble_area = st.empty()

    # ── Callbacks R1 ──────────────────────────────────────────────────────────
    def on_r1_text(agent_key, texto):
        ph = placeholders_r1.get(agent_key)
        if ph:
            ph.markdown(texto + "▌")

    def on_r1_done(agent_key, texto):
        ph = placeholders_r1.get(agent_key)
        if ph:
            ph.markdown(texto)
        hist.append({"tipo": "agente", "agent_key": agent_key, "texto": texto})
        terminal.on_concluido(agent_key, texto)

    # ── Callbacks R2 ──────────────────────────────────────────────────────────
    _r2_iniciada = [False]

    def on_r2_text(agent_key, texto):
        if not _r2_iniciada[0]:
            _r2_iniciada[0] = True
            # Renderiza header R2 no placeholder reservado
            with r2_header_ph.container():
                _header_rodada("r2")
            hist.append({"tipo": "header_rodada", "rodada": "r2"})
            terminal.add("")
            terminal.add("  ─────────────────────────────────────────────")
            terminal.add(f"  {terminal._ts()}  🟡  RODADA 2 — Debate entre especialistas")
            terminal.add("  ─────────────────────────────────────────────")

        if agent_key not in placeholders_r2:
            with r2_bubbles_ph.container():
                for k in agentes_keys:
                    if k not in placeholders_r2:
                        ph = _bubble_agente_inicio(k)
                        ph.markdown("_aguardando..._")
                        placeholders_r2[k] = ph
                        break

        ph = placeholders_r2.get(agent_key)
        if ph:
            ph.markdown(texto + "▌")

    def on_r2_done(agent_key, texto):
        if agent_key not in placeholders_r2:
            with r2_bubbles_ph.container():
                ph = _bubble_agente_inicio(agent_key)
                placeholders_r2[agent_key] = ph
        ph = placeholders_r2.get(agent_key)
        if ph:
            ph.markdown(texto)
        hist.append({"tipo": "agente", "agent_key": agent_key, "texto": texto})
        terminal.on_concluido(agent_key, texto)

    # ── Callbacks Síntese ─────────────────────────────────────────────────────
    _sintese_iniciada = [False]

    def on_sintese_text(texto):
        if not _sintese_iniciada[0]:
            _sintese_iniciada[0] = True
            with sintese_header_ph.container():
                _header_rodada("sintese")
            hist.append({"tipo": "header_rodada", "rodada": "sintese"})
            terminal.add("")
            terminal.add("  ─────────────────────────────────────────────")
            terminal.add(f"  {terminal._ts()}  🎬  SÍNTESE — Diretor consolidando...")
            terminal.add("  ─────────────────────────────────────────────")

            with sintese_bubble_area.container():
                with st.chat_message("assistant", avatar="🎬"):
                    st.markdown(
                        "<span style='color:#00CFFD;font-weight:700;font-size:13px'>"
                        "🎬 Síntese do Diretor</span>",
                        unsafe_allow_html=True,
                    )
                    ph = st.empty()
                    ph.markdown("_consolidando o debate..._")
                    ph_sintese.append(ph)

        if ph_sintese:
            ph_sintese[0].markdown(texto + "▌")

    def on_sintese_done(texto):
        if ph_sintese:
            ph_sintese[0].markdown(texto)
        hist.append({"tipo": "sintese", "texto": texto})
        palavras = len(texto.split())
        terminal.add(f"  {terminal._ts()}  🎬  Síntese concluída  ({palavras} palavras)")

    # ── on_tool unificado ─────────────────────────────────────────────────────
    def on_tool(agent_key, etapa, name, dados):
        ph = placeholders_r2.get(agent_key) or placeholders_r1.get(agent_key)
        if ph:
            if etapa == "connecting":
                ph.markdown("_conectando..._")
            elif etapa == "thinking":
                ph.markdown("_processando dados..._")
            elif etapa == "text_start":
                ph.markdown("_redigindo..._")
            elif etapa == "start":
                _, label = _TOOL_LABEL.get(name, ("⚙️", name))
                ph.markdown(f"_{label}..._")
        terminal.on_tool(agent_key, etapa, name, dados)

    # ── Executar ──────────────────────────────────────────────────────────────
    terminal.add(f"  {0.0:5.1f}s  🔵  RODADA 1 — Análises independentes")
    terminal.add("  ─────────────────────────────────────────────")

    debater_agentes(
        agent_keys=agentes_keys,
        mensagem=mensagem,
        on_r1_text=on_r1_text,
        on_r1_done=on_r1_done,
        on_r2_text=on_r2_text,
        on_r2_done=on_r2_done,
        on_sintese_text=on_sintese_text,
        on_sintese_done=on_sintese_done,
        on_tool=on_tool,
    )

    # Salva histórico
    st.session_state[f"{chave}_historico"]      = hist
    st.session_state[f"{chave}_agentes_ativos"] = agentes_keys
    st.session_state[f"{chave}_modo"]           = "debate"
    st.rerun()


# ─── RENDER PRINCIPAL ─────────────────────────────────────────────────────────

def render(cliente=None):
    st.markdown(
        "<h2 style='margin-bottom:4px'>💬 Consulta aos Especialistas</h2>"
        "<p style='color:#3d5166;font-size:13px;margin-bottom:16px'>"
        "Converse com a equipe em tempo real — veja cada etapa no terminal ao vivo.</p>",
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
    todos_keys   = list(AGENTES.keys())
    todos_labels = [AGENTES[k]["label"] for k in todos_keys]
    label_para_key = {AGENTES[k]["label"]: k for k in todos_keys}

    chat_area = st.container()
    with chat_area:
        historico = st.session_state.get(f"{chave}_historico", [])
        _exibir_historico(historico)

    if historico:
        modo_atual = st.session_state.get(f"{chave}_modo", "direto")
        agentes_ativos = st.session_state.get(f"{chave}_agentes_ativos", todos_keys[:2])

        col_nova, col_info = st.columns([1, 3])
        col_nova.markdown("<br>", unsafe_allow_html=True)
        if col_nova.button("🔄 Nova conversa", key=f"nova_{chave}", use_container_width=True):
            for k in [f"{chave}_historico", f"{chave}_agentes_ativos", f"{chave}_modo"]:
                st.session_state.pop(k, None)
            st.rerun()

        nomes = ", ".join(AGENTES[k]["label"].split("—")[-1].strip() for k in agentes_ativos)
        col_info.caption(f"{'🔄 Debate' if modo_atual == 'debate' else '💬 Direto'} · {nomes}")

        # Follow-up só no modo direto (debate já tem síntese própria)
        if modo_atual == "direto":
            followup = st.chat_input("Faça uma pergunta de acompanhamento...", key=f"ci_{chave}")
            if followup and followup.strip():
                with chat_area:
                    _executar_chat(agentes_ativos, followup.strip(), chave)
        else:
            followup = st.chat_input(
                "Nova pergunta para debate (inicia uma nova rodada)...", key=f"ci_{chave}"
            )
            if followup and followup.strip():
                for k in [f"{chave}_historico", f"{chave}_agentes_ativos", f"{chave}_modo"]:
                    st.session_state.pop(k, None)
                with chat_area:
                    _executar_debate(agentes_ativos, followup.strip(), chave)
        return

    # ── Formulário inicial ────────────────────────────────────────────────────
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

    # ── Modo de resposta ──────────────────────────────────────────────────────
    modo = st.radio(
        "Modo:",
        ["💬 Resposta direta", "🔄 Debate entre especialistas + Síntese do Diretor"],
        horizontal=True,
        key=f"modo_{chave}",
    )

    if "debate" in modo:
        st.markdown(
            "<div style='background:rgba(0,207,253,0.06);border:1px solid rgba(0,207,253,0.2);"
            "border-radius:8px;padding:10px 14px;font-size:12px;color:#64748b;margin-bottom:8px'>"
            "<strong style='color:#00CFFD'>Como funciona:</strong> "
            "Rodada 1 — cada especialista analisa de forma independente. "
            "Rodada 2 — cada um lê as respostas dos colegas e debate, concorda ou discorda. "
            "O Diretor consolida tudo num parecer final integrado."
            "</div>",
            unsafe_allow_html=True,
        )

    pergunta = st.text_area(
        "Sua pergunta:",
        height=120,
        key=f"perg_{chave}",
        placeholder=(
            "Ex: Comparar duas contas com CPA diferente — qual a causa raiz da diferença?\n"
            "Ex: Como escalar uma conta que já tem CPA de R$45 mas está limitada por orçamento?\n"
            "Ex: Qual a melhor estratégia de Google Ads para desentupidora em SP com R$80/dia?"
        ),
    )

    col_btn1, col_btn2 = st.columns(2)

    if col_btn1.button("🚀 Enviar", type="primary", use_container_width=True, key=f"btn_{chave}"):
        if not agentes:
            st.error("Selecione pelo menos um especialista.")
        elif not pergunta.strip():
            st.error("Digite uma pergunta.")
        elif "debate" in modo:
            with chat_area:
                _executar_debate(agentes, pergunta.strip(), chave)
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
    handle   = col1.text_input("Handle do Instagram:", placeholder="@empresa", key=f"handle_{chave}")
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
                      "ads_selecao", "ads_dados_raw", "ads_contexto_texto"]:
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

    # Terminal unificado para coleta de dados + análise dos agentes
    st.markdown(
        "<p style='font-size:11px;font-weight:700;color:#3d5166;"
        "text-transform:uppercase;letter-spacing:1px;margin-bottom:4px'>"
        "🖥️ Terminal</p>",
        unsafe_allow_html=True,
    )
    term_ph = st.empty()
    terminal = Terminal(term_ph)
    terminal.add(f"  {0.0:5.1f}s  Iniciando coleta de dados Google Ads...")

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
                progress_cb=lambda p, l: terminal.log_coleta(p, l),
            )
            todas_dados = [{"conta": conta, "dados": dados}]
        else:
            todas_dados, contexto_ads = comparar_contas_ads(
                contas,
                progress_cb=lambda p, l: terminal.log_coleta(p, l),
            )
    except Exception as e:
        terminal.add(f"  ERRO na coleta: {e}")
        st.error(f"Erro ao coletar dados Google Ads: {e}")
        return

    terminal.add("")
    metricas_count = len(str(contexto_ads))
    terminal.add(f"  {terminal._ts()}  ✓  Dados coletados ({metricas_count:,} chars). Enviando para análise...")
    terminal.add("")

    st.session_state["ads_dados_raw"]     = todas_dados
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
        _executar_chat(agentes_keys, mensagem, chave, terminal=terminal)
