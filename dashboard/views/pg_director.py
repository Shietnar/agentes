"""Diretor — sala de reunião com chat em grupo em tempo real."""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ─── Constantes visuais ────────────────────────────────────────────────────────

_AGENTE_CHAT = {
    "consultar_lucas":  {"nome": "Lucas",   "icon": "🎯", "cor": "#2563EB"},
    "consultar_pedro":  {"nome": "Pedro",   "icon": "🔬", "cor": "#DC2626"},
    "consultar_rodrigo":{"nome": "Rodrigo", "icon": "✍️", "cor": "#16A34A"},
    "consultar_ana":    {"nome": "Ana",     "icon": "🌐", "cor": "#7C3AED"},
    "consultar_social": {"nome": "Social",  "icon": "📱", "cor": "#EA580C"},
}

_TOOL_LABEL = {
    "buscar_site":             ("🌐", "Buscando site"),
    "buscar_dados_google_ads": ("📊", "Coletando dados Google Ads"),
    "buscar_instagram":        ("📸", "Preparando contexto Instagram"),
}

_EXEMPLOS = [
    "Analise o site e me diga como melhorar os resultados de marketing digital.",
    "Campanha Google Ads com CTR de 3% e CPA de R$ 180 — o que otimizar?",
    "Estratégia completa para uma desentupidora em Campinas que está começando.",
    "Compare copy para anúncios de chaveiros vs gasistas.",
    "Como estruturar o funil completo de captação de leads para desentupidora em SP?",
]


# ─── Helpers de chat ──────────────────────────────────────────────────────────

def _msg_usuario(texto: str):
    with st.chat_message("user"):
        st.markdown(texto)


def _msg_diretor_inicio() -> st.empty:
    """Cria bubble do Diretor e retorna placeholder para stream."""
    with st.chat_message("assistant", avatar="🎬"):
        st.markdown(
            "<span style='color:#00CFFD;font-weight:700;font-size:13px'>🎬 Diretor</span>",
            unsafe_allow_html=True,
        )
        ph = st.empty()
    return ph


def _msg_tool_system(icone: str, label: str):
    """Exibe linha de status de coleta de dados."""
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:8px;padding:6px 14px;"
        f"background:rgba(0,207,253,0.05);border-left:2px solid rgba(0,207,253,0.3);"
        f"border-radius:0 6px 6px 0;font-size:12px;color:#3d5166;margin:4px 0'>"
        f"<span style='animation:pulse 1s infinite'>{icone}</span> {label}...</div>",
        unsafe_allow_html=True,
    )


def _msg_agente_inicio(tool_name: str) -> st.empty:
    """Cria bubble de agente e retorna placeholder."""
    info = _AGENTE_CHAT.get(tool_name, {"nome": tool_name, "icon": "🤖", "cor": "#3d5166"})
    with st.chat_message("assistant", avatar=info["icon"]):
        st.markdown(
            f"<span style='color:{info['cor']};font-weight:700;font-size:13px'>"
            f"{info['icon']} {info['nome']}</span>",
            unsafe_allow_html=True,
        )
        ph = st.empty()
    return ph


def _msg_parecer_final(texto: str):
    with st.chat_message("assistant", avatar="📋"):
        st.markdown(
            "<span style='color:#00CFFD;font-weight:700;font-size:13px'>📋 Parecer Final do Diretor</span>",
            unsafe_allow_html=True,
        )
        st.markdown(texto)


# ─── Execução ─────────────────────────────────────────────────────────────────

def _executar_diretor(pedido: str, contexto_cliente: str = "", mensagens_anteriores=None):
    from agents.director import rodar_diretor

    pedido_final = f"{contexto_cliente}\n\n{pedido}".strip() if contexto_cliente else pedido

    # ── Bubble do usuário ──────────────────────────────────────────────────────
    _msg_usuario(pedido)

    # ── Estado para callbacks ──────────────────────────────────────────────────
    estado = {
        "diretor_ph":  None,    # placeholder texto do Diretor
        "diretor_buf": "",      # buffer acumulado do Diretor
        "agente_ph":   None,    # placeholder do agente atual
        "agente_buf":  "",      # buffer acumulado do agente
        "agente_tool": None,    # ferramenta ativa
    }

    # ── Callback: streaming token a token do Diretor ───────────────────────────
    def on_token_diretor(token: str):
        if estado["diretor_ph"] is None:
            estado["diretor_ph"] = _msg_diretor_inicio()
        estado["diretor_buf"] += token
        estado["diretor_ph"].markdown(estado["diretor_buf"] + "▌")

    # ── Callback: eventos de progresso (tool_start / tool_done) ───────────────
    def on_progress(etapa: str, tool_name: str, info: dict):
        if etapa == "inicio":
            return

        if etapa == "director_text":
            # Texto do Diretor (modo não-streaming, ex: continuação)
            ph = _msg_diretor_inicio()
            ph.markdown(info.get("text", ""))

        elif etapa == "tool_start":
            estado["agente_tool"] = tool_name
            if tool_name in _TOOL_LABEL:
                icone, label = _TOOL_LABEL[tool_name]
                _msg_tool_system(icone, label)
            elif tool_name.startswith("consultar_"):
                # Mostra pergunta que o Diretor fez ao agente
                pergunta = info.get("params", {}).get("pergunta", "")
                info_ag = _AGENTE_CHAT.get(tool_name, {})
                if pergunta:
                    st.markdown(
                        f"<div style='font-size:11px;color:#3d5166;padding:4px 14px;"
                        f"margin:2px 0;border-left:2px solid {info_ag.get('cor','#3d5166')}40'>"
                        f"Diretor perguntou a {info_ag.get('nome','?')}: "
                        f"<em>{pergunta[:180]}{'...' if len(pergunta)>180 else ''}</em></div>",
                        unsafe_allow_html=True,
                    )
                # Cria bubble do agente com "digitando..."
                estado["agente_ph"] = _msg_agente_inicio(tool_name)
                estado["agente_buf"] = ""
                estado["agente_ph"].markdown("_digitando..._")

        elif etapa == "tool_done":
            if tool_name.startswith("consultar_") and estado["agente_ph"]:
                output = info.get("output", "")
                if isinstance(output, str) and output.strip():
                    estado["agente_ph"].markdown(output)
                estado["agente_ph"]  = None
                estado["agente_buf"] = ""
                estado["agente_tool"] = None

        elif etapa == "fim":
            # Finaliza bubble do Diretor se ainda estiver aberto
            if estado["diretor_ph"]:
                estado["diretor_ph"].markdown(estado["diretor_buf"])
                estado["diretor_ph"] = None
                estado["diretor_buf"] = ""

    # ── Execução ───────────────────────────────────────────────────────────────
    resultado = rodar_diretor(
        pedido_final,
        progress_cb=on_progress,
        text_stream_cb=on_token_diretor,
        mensagens_anteriores=mensagens_anteriores,
    )

    # Finaliza o bubble do Diretor se a resposta veio sem tool_calls
    if estado["diretor_ph"]:
        estado["diretor_ph"].markdown(estado["diretor_buf"])

    # Só exibe bloco final se o parecer não foi streamado já pelo Diretor
    parecer = resultado.get("parecer_final", "")
    if not estado["diretor_buf"] and parecer:
        _msg_parecer_final(parecer)

    return resultado


# ─── RENDER PRINCIPAL ─────────────────────────────────────────────────────────

def render(cliente=None):
    st.markdown(
        "<h2 style='margin-bottom:4px'>🎬 Diretor — Sala de Reunião</h2>"
        "<p style='color:#3d5166;font-size:13px;margin-bottom:20px'>"
        "Acompanhe cada especialista em tempo real e participe da conversa.</p>",
        unsafe_allow_html=True,
    )

    # ── Contexto do cliente ────────────────────────────────────────────────────
    contexto_cliente = ""
    if cliente:
        with st.expander(f"Contexto ativo: {cliente.nome}", expanded=False):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Empresa:** {cliente.nome}")
            c2.markdown(f"**Segmento:** {cliente.segmento}")
            c3.markdown(f"**Cidade:** {cliente.cidade or '—'}")
        contexto_cliente = (
            f"CLIENTE: {cliente.nome} | Segmento: {cliente.segmento} | "
            f"Cidade: {cliente.cidade or 'não informada'}"
        )

    # ── Área do chat ───────────────────────────────────────────────────────────
    chat_area = st.container()

    with chat_area:
        # Exibe histórico de mensagens já processadas
        historico = st.session_state.get("dir_historico", [])
        for msg in historico:
            if msg["tipo"] == "user":
                _msg_usuario(msg["texto"])
            elif msg["tipo"] == "parecer":
                _msg_parecer_final(msg["texto"])
            elif msg["tipo"] == "agente":
                info = _AGENTE_CHAT.get(msg.get("tool", ""), {"nome": msg.get("nome", "Agente"), "icon": "🤖", "cor": "#3d5166"})
                with st.chat_message("assistant", avatar=info["icon"]):
                    st.markdown(
                        f"<span style='color:{info['cor']};font-weight:700;font-size:13px'>"
                        f"{info['icon']} {info['nome']}</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(msg["texto"])

    # ── Input inicial (se nenhuma sessão ativa) ────────────────────────────────
    if "dir_mensagens_api" not in st.session_state:
        col_ex, col_input = st.columns([1, 4], gap="large")
        with col_ex:
            st.markdown(
                "<p style='font-size:11px;font-weight:700;color:#3d5166;margin-bottom:6px'>"
                "EXEMPLOS</p>",
                unsafe_allow_html=True,
            )
            for i, ex in enumerate(_EXEMPLOS):
                if st.button(f"#{i+1}", key=f"ex_{i}", use_container_width=True, help=ex):
                    st.session_state["dir_pedido_pre"] = ex
                    st.rerun()

        with col_input:
            pedido_pre = st.session_state.pop("dir_pedido_pre", "")
            pedido = st.text_area(
                "Pedido ao Diretor:",
                value=pedido_pre,
                height=130,
                placeholder=(
                    "Ex: Analise a campanha e o site deste cliente — quais são as 3 melhorias "
                    "mais urgentes para aumentar as conversões esta semana?"
                ),
                key="dir_pedido_area",
            )
            if st.button("🎬 Acionar Diretor", type="primary", use_container_width=True,
                         disabled=not (pedido or "").strip()):
                with chat_area:
                    resultado = _executar_diretor(pedido.strip(), contexto_cliente)
                # Salva estado para continuação
                st.session_state["dir_mensagens_api"] = resultado.get("mensagens", [])
                parecer = resultado.get("parecer_final", "")
                st.session_state["dir_historico"] = [
                    {"tipo": "user", "texto": pedido.strip()},
                    {"tipo": "parecer", "texto": parecer},
                ]
                st.rerun()

    # ── Chat input para follow-up (sessão ativa) ───────────────────────────────
    else:
        col_btn, col_info = st.columns([1, 3])
        col_btn.markdown("<br>", unsafe_allow_html=True)
        if col_btn.button("🔄 Nova reunião", use_container_width=True):
            for k in ["dir_mensagens_api", "dir_historico"]:
                st.session_state.pop(k, None)
            st.rerun()
        col_info.caption(
            "A reunião está ativa. O Diretor lembra de tudo que foi discutido. "
            "Adicione contexto, redirecione o foco ou peça aprofundamento."
        )

        followup = st.chat_input("Participe da reunião — adicione contexto ou redirecione o foco")
        if followup and followup.strip():
            mensagens_api = st.session_state.get("dir_mensagens_api", [])
            with chat_area:
                resultado = _executar_diretor(
                    followup.strip(),
                    mensagens_anteriores=mensagens_api,
                )
            # Atualiza histórico
            hist = st.session_state.get("dir_historico", [])
            hist.append({"tipo": "user", "texto": followup.strip()})
            hist.append({"tipo": "parecer", "texto": resultado.get("parecer_final", "")})
            st.session_state["dir_historico"] = hist
            st.session_state["dir_mensagens_api"] = resultado.get("mensagens", [])
            st.rerun()
