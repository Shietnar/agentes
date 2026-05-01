"""Diretor — orquestra a equipe de especialistas autonomamente."""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dashboard.components import page_header, section_title, tool_step, empty_state, badge

_EXEMPLOS = [
    "Analise o site e me diga como melhorar os resultados de marketing digital.",
    "Campanha Google Ads com CTR de 3% e CPA de R$ 180 — o que otimizar?",
    "Estratégia completa para uma desentupidora em Campinas que está começando.",
    "Compare copy para anúncios de chaveiros vs gasistas.",
    "Como estruturar o funil completo de captação de leads para desentupidora em SP?",
]

_ICONE = {
    "consultar_lucas":         "🎯",
    "consultar_pedro":         "🔬",
    "consultar_rodrigo":       "✍️",
    "consultar_ana":           "🌐",
    "consultar_social":        "📱",
    "buscar_site":             "🌐",
    "buscar_dados_google_ads": "📊",
    "buscar_instagram":        "📸",
}

_COR = {
    "consultar_lucas":         "#2563EB",
    "consultar_pedro":         "#DC2626",
    "consultar_rodrigo":       "#16A34A",
    "consultar_ana":           "#7C3AED",
    "consultar_social":        "#EA580C",
    "buscar_site":             "#0F766E",
    "buscar_dados_google_ads": "#0369A1",
    "buscar_instagram":        "#BE185D",
}


def render(cliente=None):
    st.markdown(
        page_header("🎬", "Diretor",
                    "Orquestra a equipe autonomamente e entrega um parecer integrado"),
        unsafe_allow_html=True,
    )

    # ── Contexto do cliente ───────────────────────────────────────────────────
    contexto_cliente = ""
    if cliente:
        with st.expander(f"Contexto: {cliente.nome}", expanded=False):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Empresa:** {cliente.nome}")
            c2.markdown(f"**Segmento:** {cliente.segmento}")
            c3.markdown(f"**Cidade:** {cliente.cidade or '—'}")
        contexto_cliente = (
            f"CLIENTE: {cliente.nome} | Segmento: {cliente.segmento} | "
            f"Cidade: {cliente.cidade or 'não informada'}"
        )

    # ── Input ─────────────────────────────────────────────────────────────────
    st.markdown(section_title("Pedido"), unsafe_allow_html=True)

    col_input, col_ex = st.columns([3, 1], gap="large")

    with col_ex:
        st.markdown(
            "<p style='font-size:11px;font-weight:700;text-transform:uppercase;"
            "letter-spacing:0.8px;color:#94A3B8;margin-bottom:8px'>Exemplos</p>",
            unsafe_allow_html=True,
        )
        for i, ex in enumerate(_EXEMPLOS):
            if st.button(f"#{i+1}", key=f"ex_{i}", use_container_width=True,
                         help=ex):
                st.session_state["director_pedido"] = ex
                st.rerun()

    with col_input:
        pedido = st.text_area(
            "Descreva o pedido para o Diretor",
            value=st.session_state.get("director_pedido", ""),
            height=148,
            placeholder=(
                "Ex: Analise o site e os anúncios deste cliente e me diga as 3 melhorias "
                "mais urgentes para aumentar as conversões esta semana."
            ),
            key="director_pedido_area",
        )

        col_btn, col_clear = st.columns([4, 1])
        with col_btn:
            iniciar = st.button("🎬  Acionar Diretor", type="primary",
                                use_container_width=True,
                                disabled=not (pedido or "").strip())
        with col_clear:
            if st.button("Limpar", use_container_width=True):
                for k in ["director_pedido", "director_resultado", "director_etapas"]:
                    st.session_state.pop(k, None)
                st.rerun()

    # ── Execução ──────────────────────────────────────────────────────────────
    if iniciar and (pedido or "").strip():
        pedido_final = pedido.strip()
        if contexto_cliente:
            pedido_final = f"{contexto_cliente}\n\n{pedido_final}"
        st.session_state.pop("director_resultado", None)
        st.session_state.pop("director_etapas", None)
        _executar(pedido_final)

    # ── Resultado ─────────────────────────────────────────────────────────────
    if "director_resultado" in st.session_state:
        _exibir()


def _executar(pedido: str):
    from agents.director import rodar_diretor

    st.markdown(section_title("Equipe em ação"), unsafe_allow_html=True)
    progresso = st.container()

    def cb(etapa, tool_name, info):
        if etapa == "tool_start":
            with progresso:
                st.markdown(
                    tool_step(_ICONE.get(tool_name, "🔧"),
                              info.get("label", tool_name), state="loading"),
                    unsafe_allow_html=True,
                )
        elif etapa == "tool_done":
            output = info.get("output", "")
            preview = ""
            if info.get("is_agent") and isinstance(output, str) and output:
                preview = output[:200]
            with progresso:
                st.markdown(
                    tool_step(_ICONE.get(tool_name, "🔧"),
                              info.get("label", tool_name), state="done",
                              preview=preview),
                    unsafe_allow_html=True,
                )

    with st.spinner("Coordenando especialistas..."):
        resultado = rodar_diretor(pedido, progress_cb=cb)

    st.session_state["director_resultado"] = resultado["parecer_final"]
    st.session_state["director_etapas"]    = resultado["etapas"]
    st.rerun()


def _exibir():
    parecer = st.session_state["director_resultado"]
    etapas  = st.session_state.get("director_etapas", [])

    st.divider()

    col_parecer, col_log = st.columns([3, 1], gap="large")

    with col_parecer:
        st.markdown(section_title("Parecer do Diretor"), unsafe_allow_html=True)
        st.markdown(
            "<div style='background:#0f1117;border:1px solid rgba(0,207,253,0.18);"
            "border-top:2px solid #00CFFD;border-radius:0 12px 12px 12px;"
            "padding:24px 28px;box-shadow:0 0 30px rgba(0,207,253,0.06)'>",
            unsafe_allow_html=True,
        )
        st.markdown(parecer)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.download_button("⬇️  Baixar parecer", data=parecer,
                           file_name="parecer_diretor.txt", mime="text/plain")

    with col_log:
        st.markdown(section_title("Equipe acionada"), unsafe_allow_html=True)

        if not etapas:
            st.markdown(
                empty_state("🔧", "Nenhuma ferramenta", ""),
                unsafe_allow_html=True,
            )
        else:
            dados   = [e for e in etapas if not e.get("is_agent")]
            agentes = [e for e in etapas if e.get("is_agent")]

            if dados:
                st.markdown(
                    "<p style='font-size:10px;font-weight:700;color:#3d5166;"
                    "text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>"
                    "Dados coletados</p>",
                    unsafe_allow_html=True,
                )
                for e in dados:
                    cor = _COR.get(e["tool"], "#3d5166")
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:8px;padding:8px 10px;"
                        f"border-left:2px solid {cor};background:#0f1117;"
                        f"border-radius:0 6px 6px 0;margin-bottom:4px;"
                        f"font-size:12px;color:#94a3b8'>"
                        f"{e['icone']} {e['label']}</div>",
                        unsafe_allow_html=True,
                    )

            if agentes:
                st.markdown(
                    "<p style='font-size:10px;font-weight:700;color:#3d5166;"
                    "text-transform:uppercase;letter-spacing:1px;margin:12px 0 6px'>"
                    "Especialistas consultados</p>",
                    unsafe_allow_html=True,
                )
                for e in agentes:
                    cor = _COR.get(e["tool"], "#00CFFD")
                    with st.expander(f"{e['icone']} {e['label']}", expanded=False):
                        pergunta_ag = e["input"].get("pergunta", "—")
                        st.markdown(
                            f"<div style='border-left:2px solid {cor}40;padding:8px 12px;"
                            f"border-radius:0 6px 6px 0;background:#0a0a0f;"
                            f"font-size:12px;color:#3d5166;margin-bottom:10px'>"
                            f"<strong style='color:#3d5166'>Pergunta:</strong><br>"
                            f"<span style='color:#94a3b8'>{pergunta_ag}</span></div>",
                            unsafe_allow_html=True,
                        )
                        output = e.get("output", "")
                        if isinstance(output, str) and output:
                            st.markdown(output)
                        elif output:
                            st.json(output)

            n_ag  = len(agentes)
            n_dad = len(dados)
            st.markdown(
                f"<p style='font-size:11px;color:#3d5166;margin-top:12px'>"
                f"{n_ag} especialista(s) · {n_dad} fonte(s)</p>",
                unsafe_allow_html=True,
            )
