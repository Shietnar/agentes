"""
Consulta aos Especialistas — interface unificada.
Detecta automaticamente contas Google Ads, URLs e handles de Instagram no texto.
Modos: Resposta direta ou Debate em rodadas com Síntese do Diretor.
"""
import re
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

_RODADA_ESTILO = {
    "r1":      ("#1565C0", "🔵", "Rodada 1 — Análise Inicial"),
    "r2":      ("#F57F17", "🟡", "Rodada 2 — Debate"),
    "sintese": ("#00CFFD", "🎬", "Síntese do Diretor"),
}


# ─── Terminal de eventos ──────────────────────────────────────────────────────

class Terminal:
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
        visivel = self._linhas[-50:] if self._linhas else ["  aguardando..."]
        self._ph.code("\n".join(visivel), language=None)

    def on_tool(self, agent_key: str, etapa: str, name: str, dados):
        ag = AGENTES.get(agent_key, {})
        nome = ag.get("label", agent_key).split("—")[-1].strip()
        if etapa == "connecting":
            self.add(f"  {self._ts()}  {nome}  →  abrindo sessão...")
        elif etapa == "text_start":
            self.add(f"  {self._ts()}  {nome}  →  ✏️  redigindo resposta...")
        elif etapa == "thinking":
            self.add(f"  {self._ts()}  {nome}  →  💭  processando dados...")
        elif etapa == "start":
            icone, label = _TOOL_LABEL.get(name, ("⚙️", name))
            self.add(f"  {self._ts()}  {nome}  →  {icone}  {label}...")
        elif etapa == "done":
            chars = len(str(dados)) if dados else 0
            _, label = _TOOL_LABEL.get(name, ("⚙️", name))
            self.add(f"  {self._ts()}  {nome}  →  ✓  {label}  ({chars:,} chars)")

    def on_concluido(self, agent_key: str, texto: str):
        ag = AGENTES.get(agent_key, {})
        nome = ag.get("label", agent_key).split("—")[-1].strip()
        palavras = len(texto.split())
        self.add(f"  {self._ts()}  {nome}  →  ✓  concluído  ({palavras} palavras)")
        self.add("")

    def separador(self, label: str):
        self.add(f"  ─────────────────────────────────────────────")
        self.add(f"  {self._ts()}  {label}")
        self.add(f"  ─────────────────────────────────────────────")

    def log_coleta(self, pct: float, label: str):
        self.add(f"  {self._ts()}  📊  {label}  ({pct*100:.0f}%)")


# ─── Detecção de fontes no texto ──────────────────────────────────────────────

def _detectar_fontes(texto: str) -> dict:
    """Detecta URLs, handles Instagram e IDs de conta Google Ads no texto livre."""
    urls = re.findall(r'https?://[^\s<>"\')\]]+', texto)
    instagram = re.findall(r'@([A-Za-z0-9_.]{2,30})', texto)
    # Formato NNN-NNN-NNNN ou 10 dígitos seguidos de keywords
    ads_dash = re.findall(r'\b(\d{3}-\d{3}-\d{4})\b', texto)
    ads_clean = [x.replace('-', '') for x in ads_dash]
    # 10 dígitos após "conta", "account", "ID" etc.
    for m in re.finditer(r'(?:conta|account|customer|ads|ID)[^\d]*(\d{10})\b', texto, re.IGNORECASE):
        cid = m.group(1)
        if cid not in ads_clean:
            ads_clean.append(cid)
    return {
        "urls": list(dict.fromkeys(urls)),
        "instagram": list(dict.fromkeys(instagram)),
        "ads_accounts": list(dict.fromkeys(ads_clean)),
    }


# ─── Chat bubbles ─────────────────────────────────────────────────────────────

def _bubble_usuario(texto: str):
    with st.chat_message("user"):
        st.markdown(texto)


def _bubble_agente_inicio(agent_key: str) -> st.empty:
    ag = AGENTES.get(agent_key, {})
    label = ag.get("label", agent_key)
    icone = label.split(" ")[0]
    cor   = ag.get("cor", "#3d5166")
    with st.chat_message("assistant", avatar=icone):
        st.markdown(
            f"<span style='color:{cor};font-weight:700;font-size:13px'>{label}</span>",
            unsafe_allow_html=True,
        )
        ph = st.empty()
    return ph


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
        elif msg["tipo"] == "contexto_info":
            st.markdown(
                f"<div style='font-size:11px;color:#3d5166;padding:4px 10px;"
                f"background:rgba(0,207,253,0.04);border-radius:4px;margin:2px 0'>"
                f"📎 {msg['texto']}</div>",
                unsafe_allow_html=True,
            )


# ─── Execução: resposta direta ────────────────────────────────────────────────

def _executar_chat(agentes_keys: list, mensagem: str, chave: str,
                   terminal: "Terminal | None" = None,
                   hist_extra: list | None = None):
    from agents.consulta import consultar_agentes

    placeholders: dict[str, st.empty] = {}
    for k in agentes_keys:
        ph = _bubble_agente_inicio(k)
        ph.markdown("_aguardando..._")
        placeholders[k] = ph

    if terminal is None:
        _criar_terminal_label()
        terminal = Terminal(st.empty())

    def on_text(agent_key, texto):
        ph = placeholders.get(agent_key)
        if ph:
            ph.markdown(texto + "▌")

    def on_tool(agent_key, etapa, name, dados):
        ph = placeholders.get(agent_key)
        if ph:
            _atualizar_bubble_status(ph, etapa, name)
        terminal.on_tool(agent_key, etapa, name, dados)

    def on_done(agent_key, label, texto):
        ph = placeholders.get(agent_key)
        if ph:
            ph.markdown(texto)
        terminal.on_concluido(agent_key, texto)

    resultados = consultar_agentes(
        agentes_keys, mensagem,
        callback=on_done, on_text=on_text, on_tool=on_tool,
    )

    hist = list(hist_extra or [])
    for r in resultados:
        hist.append({"tipo": "agente", "agent_key": r["agent_key"], "texto": r["texto"]})
    st.session_state[f"{chave}_historico"] = hist
    st.session_state[f"{chave}_agentes_ativos"] = agentes_keys
    st.session_state[f"{chave}_modo"] = "direto"
    st.rerun()


# ─── Execução: debate em rodadas ──────────────────────────────────────────────

def _executar_debate(agentes_keys: list, mensagem: str, chave: str,
                     terminal: "Terminal | None" = None,
                     hist_extra: list | None = None):
    from agents.consulta import debater_agentes

    hist: list[dict] = list(hist_extra or [])

    if terminal is None:
        _criar_terminal_label()
        terminal = Terminal(st.empty())

    placeholders_r1: dict[str, st.empty] = {}
    placeholders_r2: dict[str, st.empty] = {}
    ph_sintese: list = []

    # ── Rodada 1 ──────────────────────────────────────────────────────────────
    terminal.separador("🔵  RODADA 1 — Análises independentes")
    _header_rodada("r1")
    hist.append({"tipo": "header_rodada", "rodada": "r1"})
    for k in agentes_keys:
        ph = _bubble_agente_inicio(k)
        ph.markdown("_aguardando..._")
        placeholders_r1[k] = ph

    r2_header_ph    = st.empty()
    r2_bubbles_ph   = st.empty()
    sintese_hdr_ph  = st.empty()
    sintese_area_ph = st.empty()

    # ── callbacks R1 ──────────────────────────────────────────────────────────
    def on_r1_text(k, t):
        ph = placeholders_r1.get(k)
        if ph:
            ph.markdown(t + "▌")

    def on_r1_done(k, t):
        ph = placeholders_r1.get(k)
        if ph:
            ph.markdown(t)
        hist.append({"tipo": "agente", "agent_key": k, "texto": t})
        terminal.on_concluido(k, t)

    # ── callbacks R2 ──────────────────────────────────────────────────────────
    _r2_iniciada = [False]

    def on_r2_text(k, t):
        if not _r2_iniciada[0]:
            _r2_iniciada[0] = True
            with r2_header_ph.container():
                _header_rodada("r2")
            hist.append({"tipo": "header_rodada", "rodada": "r2"})
            terminal.separador("🟡  RODADA 2 — Debate entre especialistas")
        if k not in placeholders_r2:
            with r2_bubbles_ph.container():
                for ak in agentes_keys:
                    if ak not in placeholders_r2:
                        ph2 = _bubble_agente_inicio(ak)
                        ph2.markdown("_aguardando..._")
                        placeholders_r2[ak] = ph2
                        break
        ph = placeholders_r2.get(k)
        if ph:
            ph.markdown(t + "▌")

    def on_r2_done(k, t):
        if k not in placeholders_r2:
            with r2_bubbles_ph.container():
                ph2 = _bubble_agente_inicio(k)
                placeholders_r2[k] = ph2
        ph = placeholders_r2.get(k)
        if ph:
            ph.markdown(t)
        hist.append({"tipo": "agente", "agent_key": k, "texto": t})
        terminal.on_concluido(k, t)

    # ── callbacks Síntese ─────────────────────────────────────────────────────
    _sint_iniciada = [False]

    def on_sintese_text(t):
        if not _sint_iniciada[0]:
            _sint_iniciada[0] = True
            with sintese_hdr_ph.container():
                _header_rodada("sintese")
            hist.append({"tipo": "header_rodada", "rodada": "sintese"})
            terminal.separador("🎬  SÍNTESE — Diretor consolidando")
            with sintese_area_ph.container():
                with st.chat_message("assistant", avatar="🎬"):
                    st.markdown(
                        "<span style='color:#00CFFD;font-weight:700;font-size:13px'>"
                        "🎬 Síntese do Diretor</span>",
                        unsafe_allow_html=True,
                    )
                    ph_s = st.empty()
                    ph_s.markdown("_consolidando o debate..._")
                    ph_sintese.append(ph_s)
        if ph_sintese:
            ph_sintese[0].markdown(t + "▌")

    def on_sintese_done(t):
        if ph_sintese:
            ph_sintese[0].markdown(t)
        hist.append({"tipo": "sintese", "texto": t})
        terminal.add(f"  {terminal._ts()}  🎬  concluído  ({len(t.split())} palavras)")

    def on_tool(k, etapa, name, dados):
        ph = placeholders_r2.get(k) or placeholders_r1.get(k)
        if ph:
            _atualizar_bubble_status(ph, etapa, name)
        terminal.on_tool(k, etapa, name, dados)

    # ── Executar ──────────────────────────────────────────────────────────────
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

    st.session_state[f"{chave}_historico"]      = hist
    st.session_state[f"{chave}_agentes_ativos"] = agentes_keys
    st.session_state[f"{chave}_modo"]           = "debate"
    st.rerun()


# ─── Helpers internos ────────────────────────────────────────────────────────

def _criar_terminal_label():
    st.markdown(
        "<p style='font-size:11px;font-weight:700;color:#3d5166;"
        "text-transform:uppercase;letter-spacing:1px;margin:16px 0 4px'>"
        "🖥️ Terminal</p>",
        unsafe_allow_html=True,
    )


def _atualizar_bubble_status(ph, etapa: str, name: str):
    if etapa == "connecting":
        ph.markdown("_conectando..._")
    elif etapa == "thinking":
        ph.markdown("_processando dados..._")
    elif etapa == "text_start":
        ph.markdown("_redigindo..._")
    elif etapa == "start":
        _, label = _TOOL_LABEL.get(name, ("⚙️", name))
        ph.markdown(f"_{label}..._")


def _botoes_sessao_ativa(chave: str, agentes_ativos: list, modo: str):
    col_nova, col_info = st.columns([1, 3])
    col_nova.markdown("<br>", unsafe_allow_html=True)
    if col_nova.button("🔄 Nova conversa", key=f"nova_{chave}", use_container_width=True):
        for k in [f"{chave}_historico", f"{chave}_agentes_ativos", f"{chave}_modo"]:
            st.session_state.pop(k, None)
        st.rerun()
    nomes = ", ".join(AGENTES[k]["label"].split("—")[-1].strip() for k in agentes_ativos)
    modo_label = "🔄 Debate" if modo == "debate" else "💬 Direto"
    col_info.caption(f"{modo_label} · {nomes}")


def _modo_radio(chave_suffix: str) -> str:
    return st.radio(
        "Modo de resposta:",
        ["💬 Resposta direta", "🔄 Debate + Síntese do Diretor"],
        horizontal=True,
        key=f"modo_radio_{chave_suffix}",
    )


def _eh_debate(modo: str) -> bool:
    return "Debate" in modo


def _disparar(modo: str, agentes: list, mensagem: str, chave: str,
              chat_area, terminal=None, hist_extra=None):
    with chat_area:
        _bubble_usuario(mensagem[:400] + ("..." if len(mensagem) > 400 else ""))
    if _eh_debate(modo):
        with chat_area:
            _executar_debate(agentes, mensagem, chave, terminal=terminal,
                             hist_extra=hist_extra)
    else:
        with chat_area:
            _executar_chat(agentes, mensagem, chave, terminal=terminal,
                           hist_extra=hist_extra)


# ─── RENDER PRINCIPAL ─────────────────────────────────────────────────────────

def render(cliente=None):
    st.markdown(
        "<h2 style='margin-bottom:4px'>💬 Consulta aos Especialistas</h2>"
        "<p style='color:#3d5166;font-size:13px;margin-bottom:16px'>"
        "Escreva livremente — detectamos contas Google Ads, URLs e @handles automaticamente.</p>",
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


# ─── ABA: PERGUNTA LIVRE (com detecção de fontes) ────────────────────────────

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
        modo_atual   = st.session_state.get(f"{chave}_modo", "direto")
        agentes_at   = st.session_state.get(f"{chave}_agentes_ativos", todos_keys[:2])
        _botoes_sessao_ativa(chave, agentes_at, modo_atual)

        ci_key = f"ci_{chave}"
        followup = st.chat_input(
            "Continue o debate ou faça nova pergunta...", key=ci_key
        )
        if followup and followup.strip():
            _disparar(
                "debate" if modo_atual == "debate" else "direto",
                agentes_at, followup.strip(), chave, chat_area,
            )
        return

    # ── Formulário ────────────────────────────────────────────────────────────
    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        sel_labels = st.multiselect(
            "Especialistas:", options=todos_labels,
            default=todos_labels[:2], key=f"sel_{chave}",
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Todos", key=f"todos_{chave}", use_container_width=True):
            st.session_state[f"sel_{chave}"] = todos_labels
            st.rerun()

    agentes = [label_para_key[l] for l in sel_labels if l in label_para_key]

    modo = _modo_radio(chave)

    if _eh_debate(modo):
        st.markdown(
            "<div style='background:rgba(0,207,253,0.05);border:1px solid rgba(0,207,253,0.18);"
            "border-radius:8px;padding:8px 14px;font-size:12px;color:#64748b;margin-bottom:6px'>"
            "<strong style='color:#00CFFD'>Debate:</strong> "
            "Rodada 1 — análise independente · "
            "Rodada 2 — cada especialista lê e debate os colegas · "
            "Diretor sintetiza em plano integrado."
            "</div>",
            unsafe_allow_html=True,
        )

    pergunta = st.text_area(
        "Sua pergunta / contexto:",
        height=140,
        key=f"perg_{chave}",
        placeholder=(
            "Escreva livremente. Exemplos:\n"
            "• Compare a conta 123-456-7890 com a 987-654-3210 e me diga onde está o desperdício\n"
            "• Analise https://www.site.com.br e sugira melhorias para converter mais\n"
            "• @empresacliente tem 2k seguidores e 2% engajamento — o que fazer?\n"
            "• Estratégia completa para desentupidora em Campinas com R$100/dia de budget"
        ),
    )

    # Detecção de fontes em tempo real
    fontes = _detectar_fontes(pergunta) if pergunta else {"urls": [], "instagram": [], "ads_accounts": []}
    fontes_detectadas = fontes["urls"] + [f"@{h}" for h in fontes["instagram"]] + fontes["ads_accounts"]

    if fontes_detectadas:
        st.markdown(
            "<p style='font-size:11px;font-weight:700;color:#3d5166;"
            "text-transform:uppercase;letter-spacing:1px;margin:4px 0 2px'>Fontes detectadas</p>",
            unsafe_allow_html=True,
        )
        for f in fontes_detectadas:
            icone = "🌐" if f.startswith("http") else ("📱" if f.startswith("@") else "📊")
            tipo  = "site" if f.startswith("http") else ("Instagram" if f.startswith("@") else "Google Ads conta")
            st.markdown(
                f"<div style='font-size:12px;color:#94a3b8;padding:2px 8px'>"
                f"{icone} <code>{f}</code> <span style='color:#3d5166'>→ {tipo}</span></div>",
                unsafe_allow_html=True,
            )

    # ── Fontes adicionais manuais ─────────────────────────────────────────────
    with st.expander("➕ Adicionar fontes manualmente (URL, conta Ads, Instagram)", expanded=False):
        col_a, col_b = st.columns(2)
        url_extra = col_a.text_input(
            "URL adicional", placeholder="https://...", key=f"url_extra_{chave}"
        )
        handle_extra = col_b.text_input(
            "Instagram handle", placeholder="@empresa", key=f"insta_extra_{chave}"
        )
        # Google Ads: seletor de conta/campanha
        st.caption("Para adicionar dados do Google Ads, use a aba **📊 Google Ads** ao lado.")

    col_btn_main, _ = st.columns([1, 2])
    if col_btn_main.button("🚀 Enviar", type="primary", use_container_width=True, key=f"btn_{chave}"):
        if not agentes:
            st.error("Selecione pelo menos um especialista.")
        elif not pergunta.strip():
            st.error("Digite uma pergunta.")
        else:
            # Coleta contexto das fontes detectadas + manuais
            todas_urls = list(fontes["urls"])
            if url_extra and url_extra.strip().startswith("http"):
                todas_urls.append(url_extra.strip())
            todos_handles = list(fontes["instagram"])
            if handle_extra and handle_extra.strip():
                todos_handles.append(handle_extra.strip().lstrip("@"))

            contexto_extra = ""
            hist_extra = [{"tipo": "user", "texto": pergunta.strip()}]

            if todas_urls or todos_handles:
                with st.status("Coletando dados das fontes detectadas...", expanded=True) as s:
                    from agents.consulta import preparar_contexto_site, preparar_contexto_instagram
                    partes = []
                    for url in todas_urls:
                        st.write(f"🌐 Buscando {url[:60]}...")
                        ctx = preparar_contexto_site(url)
                        partes.append(f"=== SITE: {url} ===\n{ctx}")
                        hist_extra.append({"tipo": "contexto_info", "texto": f"Site incluído: {url}"})
                    for handle in todos_handles:
                        st.write(f"📱 Contextualizando @{handle}...")
                        ctx = preparar_contexto_instagram(handle)
                        partes.append(f"=== INSTAGRAM: @{handle} ===\n{ctx}")
                        hist_extra.append({"tipo": "contexto_info", "texto": f"Instagram incluído: @{handle}"})
                    contexto_extra = "\n\n".join(partes)
                    s.update(label="Fontes coletadas!", state="complete")

            mensagem_final = pergunta.strip()
            if contexto_extra:
                mensagem_final += f"\n\n{contexto_extra}"

            _disparar(modo, agentes, mensagem_final, chave, chat_area,
                      hist_extra=hist_extra)


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
        modo_atual = st.session_state.get(f"{chave}_modo", "direto")
        agentes_at = st.session_state.get(f"{chave}_agentes_ativos", ["ana", "lucas"])
        _botoes_sessao_ativa(chave, agentes_at, modo_atual)
        followup = st.chat_input("Pergunta de acompanhamento sobre o site...", key=f"ci_{chave}")
        if followup and followup.strip():
            _disparar("debate" if modo_atual == "debate" else "direto",
                      agentes_at, followup.strip(), chave, chat_area)
        return

    sel_labels = st.multiselect(
        "Especialistas:", options=todos_labels,
        default=[AGENTES["ana"]["label"], AGENTES["lucas"]["label"]],
        key=f"sel_{chave}",
    )
    agentes = [label_para_key[l] for l in sel_labels if l in label_para_key]
    modo = _modo_radio(chave)

    url = st.text_input("URL do site:", placeholder="https://www.exemplo.com.br", key=f"url_{chave}")
    urls_extra = st.text_area(
        "Sites de referência / concorrentes (um por linha, opcional):",
        height=60, key=f"urls_extra_{chave}",
        placeholder="https://concorrente1.com.br\nhttps://referencia.com",
    )
    pergunta_custom = st.text_area(
        "Pergunta específica (opcional):", height=60, key=f"perg_{chave}",
        placeholder="Ex: Compare com os sites de referência. Onde perdemos conversões?",
    )

    if st.button("🔍 Analisar", type="primary", use_container_width=True, key=f"btn_{chave}"):
        if not agentes:
            st.error("Selecione pelo menos um especialista.")
        elif not url.strip():
            st.error("Informe a URL.")
        else:
            partes = []
            hist_extra = [{"tipo": "user", "texto": pergunta_custom or url}]
            with st.status("Buscando conteúdo dos sites...", expanded=True) as s:
                from agents.consulta import preparar_contexto_site
                st.write(f"🌐 {url[:70]}...")
                partes.append(f"=== SITE PRINCIPAL: {url} ===\n{preparar_contexto_site(url)}")
                hist_extra.append({"tipo": "contexto_info", "texto": f"Site: {url}"})
                for u in (urls_extra or "").splitlines():
                    u = u.strip()
                    if u.startswith("http"):
                        st.write(f"🌐 {u[:70]}...")
                        partes.append(f"=== REFERÊNCIA: {u} ===\n{preparar_contexto_site(u)}")
                        hist_extra.append({"tipo": "contexto_info", "texto": f"Referência: {u}"})
                s.update(label="Sites coletados!", state="complete")

            pergunta = (pergunta_custom or
                        "Analise este site na sua área de especialidade. "
                        "Identifique problemas, oportunidades e dê recomendações concretas.")
            if len(partes) > 1:
                pergunta += "\n\nFaça uma análise COMPARATIVA com os sites de referência."
            mensagem = f"TAREFA: {pergunta}\n\n" + "\n\n".join(partes)
            _disparar(modo, agentes, mensagem, chave, chat_area, hist_extra=hist_extra)


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
        modo_atual = st.session_state.get(f"{chave}_modo", "direto")
        agentes_at = st.session_state.get(f"{chave}_agentes_ativos", ["social"])
        _botoes_sessao_ativa(chave, agentes_at, modo_atual)
        followup = st.chat_input("Pergunta de acompanhamento...", key=f"ci_{chave}")
        if followup and followup.strip():
            _disparar("debate" if modo_atual == "debate" else "direto",
                      agentes_at, followup.strip(), chave, chat_area)
        return

    sel_labels = st.multiselect(
        "Especialistas:", options=todos_labels,
        default=[AGENTES["social"]["label"]],
        key=f"sel_{chave}",
    )
    agentes = [label_para_key[l] for l in sel_labels if l in label_para_key]
    modo = _modo_radio(chave)

    col1, col2 = st.columns(2)
    handle   = col1.text_input("Handle do Instagram:", placeholder="@empresa", key=f"handle_{chave}")
    segmento = col2.text_input("Segmento:", placeholder="desentupidora, gasista...", key=f"seg_{chave}")
    info = st.text_area(
        "Dados da conta:", height=60, key=f"info_{chave}",
        placeholder="Ex: 850 seguidores, 2x semana, fotos antes/depois, zona sul SP",
    )
    pergunta_custom = st.text_area(
        "Pergunta específica (opcional):", height=55, key=f"perg_{chave}",
        placeholder="Ex: Como aumentar engajamento? Qual conteúdo priorizar?",
    )

    if st.button("📱 Analisar", type="primary", use_container_width=True, key=f"btn_{chave}"):
        if not agentes:
            st.error("Selecione pelo menos um especialista.")
        elif not handle.strip():
            st.error("Informe o handle do Instagram.")
        else:
            from agents.consulta import preparar_contexto_instagram
            ctx = preparar_contexto_instagram(handle, f"Segmento: {segmento}. {info}")
            pergunta = pergunta_custom or (
                "Analise a presença no Instagram e dê seu parecer na sua especialidade."
            )
            mensagem = f"TAREFA: {pergunta}\n\n{ctx}"
            hist_extra = [
                {"tipo": "user", "texto": pergunta_custom or handle},
                {"tipo": "contexto_info", "texto": f"Instagram: {handle}"},
            ]
            _disparar(modo, agentes, mensagem, chave, chat_area, hist_extra=hist_extra)


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
        modo_atual  = st.session_state.get(f"{chave}_modo", "direto")
        agentes_at  = st.session_state.get(f"{chave}_agentes_ativos", ["pedro", "lucas"])
        ctx_salvo   = st.session_state.get("ads_contexto_texto", "")
        _botoes_sessao_ativa(chave, agentes_at, modo_atual)
        followup = st.chat_input("Pergunta de acompanhamento sobre a campanha...", key=f"ci_{chave}")
        if followup and followup.strip():
            mensagem = f"PERGUNTA DE ACOMPANHAMENTO: {followup.strip()}"
            if ctx_salvo:
                mensagem += f"\n\nCONTEXTO DOS DADOS (já coletados):\n{ctx_salvo[:4000]}"
            _disparar("debate" if modo_atual == "debate" else "direto",
                      agentes_at, mensagem, chave, chat_area)
        return

    # ── Seleção ───────────────────────────────────────────────────────────────
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
        col_r, _ = st.columns([1, 3])
        if col_r.button("↺ Tentar novamente", use_container_width=True):
            _carregar_contas_mcc.clear()
            st.session_state.pop("ads_contas_mcc", None)
            st.rerun()
        return

    if "ads_selecao" not in st.session_state:
        st.session_state["ads_selecao"] = []

    col_conta, col_camp, col_dias, col_add = st.columns([3, 3, 1, 1])
    conta_opcoes   = {f"{c['nome']} ({c['id']})": c for c in contas_mcc}
    conta_lbl      = col_conta.selectbox("Conta", list(conta_opcoes.keys()), key="ads_sel_conta")
    conta_sel      = conta_opcoes[conta_lbl]

    campanhas = []
    try:
        campanhas = _carregar_campanhas_conta(conta_sel["id"])
    except Exception as e:
        st.error(f"Erro ao carregar campanhas: {e}")

    camp_ativas = [c for c in campanhas if c["status"] == "ENABLED"]
    camp_opcoes = {f"{c['nome']} — R${c['orcamento_diario_brl']:.0f}/dia": c
                  for c in camp_ativas} if camp_ativas else {}

    if camp_opcoes:
        camp_lbl = col_camp.selectbox("Campanha", list(camp_opcoes.keys()), key="ads_sel_camp")
        camp_sel = camp_opcoes[camp_lbl]
    else:
        col_camp.selectbox("Campanha", ["—"], key="ads_sel_camp", disabled=True)
        camp_sel = None

    dias_sel = col_dias.selectbox("Período", [7, 14, 30], index=2, key="ads_sel_dias")
    col_add.markdown("<br>", unsafe_allow_html=True)
    if col_add.button("＋", use_container_width=True, key="ads_add_btn",
                      disabled=camp_sel is None):
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
        st.caption("Adicione pelo menos uma campanha com ＋.")

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
                "Ex: Onde está o maior desperdício?\n"
                "Ex: Compare as campanhas e diga qual tem melhor potencial de escala."
            ),
        )

    modo = _modo_radio("ads")

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
            _executar_ads_analise(selecao, agentes_keys, pergunta_ads, modo, chat_area, chave)


def _executar_ads_analise(contas, agentes_keys, pergunta, modo, chat_area, chave):
    """Coleta dados via st.status (visível imediatamente) e depois aciona os agentes."""
    from agents.consulta import coletar_e_formatar_ads, comparar_contas_ads

    todas_dados = []
    contexto_ads = ""
    hist_extra = [{"tipo": "user", "texto": pergunta or "Análise Google Ads"}]

    # ── Coleta com st.status (garante visibilidade imediata) ──────────────────
    with st.status("📊 Coletando dados das campanhas...", expanded=True) as coleta_status:
        try:
            if len(contas) == 1:
                conta = contas[0]
                st.write(f"Iniciando coleta: {conta['label']}...")

                etapas_log = []

                def progress_cb(p, l):
                    etapas_log.append(f"  {p*100:.0f}%  {l}")
                    st.write(f"  {'▓' * int(p*20)}{'░' * (20-int(p*20))}  {l}")

                dados, contexto_ads = coletar_e_formatar_ads(
                    customer_id=conta["customer_id"],
                    campaign_id=conta["campaign_id"],
                    label=conta.get("label", ""),
                    dias=conta.get("dias", 30),
                    progress_cb=progress_cb,
                )
                todas_dados = [{"conta": conta, "dados": dados}]
                hist_extra.append({"tipo": "contexto_info",
                                   "texto": f"Google Ads: {conta['label']}"})
            else:
                for i, conta in enumerate(contas):
                    st.write(f"  {i+1}/{len(contas)}  {conta['label']}...")
                todas_dados, contexto_ads = comparar_contas_ads(
                    contas,
                    progress_cb=lambda p, l: st.write(f"  {p*100:.0f}%  {l}"),
                )
                for c in contas:
                    hist_extra.append({"tipo": "contexto_info",
                                       "texto": f"Google Ads: {c['label']}"})

            chars = len(contexto_ads)
            coleta_status.update(
                label=f"✓ Dados coletados — {chars:,} chars",
                state="complete",
            )
        except Exception as e:
            coleta_status.update(label=f"Erro na coleta: {e}", state="error")
            st.error(f"Erro ao coletar dados Google Ads: {e}")
            return

    st.session_state["ads_dados_raw"]     = todas_dados
    st.session_state["ads_contexto_texto"] = contexto_ads

    pergunta_final = pergunta or (
        "Analise os dados do Google Ads na sua área de especialidade. "
        "Identifique problemas, oportunidades e priorize as ações."
    )
    if len(contas) > 1:
        pergunta_final += (
            "\n\nFaça uma análise COMPARATIVA. "
            "Qual conta está mais eficiente? Onde está o maior desperdício?"
        )

    mensagem = f"TAREFA: {pergunta_final}\n\n{contexto_ads}"

    # Terminal unificado para a fase de análise
    _criar_terminal_label()
    terminal = Terminal(st.empty())
    terminal.add(f"  {0.0:5.1f}s  Dados coletados. Enviando para os especialistas...")

    with chat_area:
        _bubble_usuario(pergunta or f"Análise de {len(contas)} campanha(s)")

    if _eh_debate(modo):
        with chat_area:
            _executar_debate(agentes_keys, mensagem, chave,
                             terminal=terminal, hist_extra=hist_extra)
    else:
        with chat_area:
            _executar_chat(agentes_keys, mensagem, chave,
                           terminal=terminal, hist_extra=hist_extra)
