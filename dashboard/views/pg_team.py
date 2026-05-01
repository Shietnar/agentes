"""
Página de Reunião de Time — UnboundSales Dashboard
Orquestra os 4 especialistas discutindo juntos sobre o cliente.
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.team_session import TeamSession, TIPOS_REUNIAO

# Cores por persona
_CORES = {
    "🎯 Lucas — Estratégia de Negócio": "#1565C0",
    "🔬 Pedro — Google Ads":            "#C62828",
    "✍️ Rodrigo — Copywriter RSA":      "#2E7D32",
    "🌐 Ana — Landing Pages & Web":     "#6A1B9A",
    "📋 Moderador — Plano Final":       "#37474F",
}

_ETAPA_LABEL = {
    "rodada_1": "Rodada 1 — Análise Inicial",
    "rodada_2": "Rodada 2 — Debate e Complementos",
    "sintese":  "Síntese Final",
}


def _card_contribuicao(agente: str, texto: str, etapa: str):
    cor = _CORES.get(agente, "#424242")
    icone = agente.split(" ")[0]
    nome = agente.split("—")[-1].strip() if "—" in agente else agente
    st.markdown(
        f"""
        <div style="
            border-left: 4px solid {cor};
            background: #fafafa;
            border-radius: 0 8px 8px 0;
            padding: 14px 18px;
            margin-bottom: 12px;
        ">
          <div style="font-size:13px;font-weight:700;color:{cor};margin-bottom:6px">
            {icone} {nome}
            <span style="font-size:11px;font-weight:400;color:#999;margin-left:8px">
              {_ETAPA_LABEL.get(etapa,etapa)}
            </span>
          </div>
          <div style="font-size:14px;color:#212121;line-height:1.6;white-space:pre-wrap">{texto}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render(cliente):
    st.markdown("## 🤝 Reunião de Time")
    st.caption(
        "Os 4 especialistas discutem juntos a melhor estratégia para o cliente. "
        "2 rodadas de debate + síntese final pelo moderador."
    )

    # ── Formulário de configuração ─────────────────────────────────────────────
    with st.form("form_reuniao"):
        col1, col2 = st.columns(2)

        opcoes_tipo = {v["label"]: k for k, v in TIPOS_REUNIAO.items()}
        tipo_label = col1.selectbox(
            "Tipo de Reunião",
            list(opcoes_tipo.keys()),
        )
        tipo_key = opcoes_tipo[tipo_label]
        descricao = TIPOS_REUNIAO[tipo_key]["descricao"]
        col2.markdown(f"<br><small style='color:#666'>{descricao}</small>", unsafe_allow_html=True)

        briefing = st.text_area(
            "Briefing / Contexto do Cliente",
            height=180,
            placeholder=(
                "Ex: Empresa com 8 anos, 4 técnicos. Atende zona sul e centro. "
                "Diferencial: chegada em 45 min, orçamento grátis, nota fiscal. "
                "Budget Google Ads: R$ 80/dia. QS médio: 5. CTR: 3.2%. CPA: R$ 85."
            ),
            value=st.session_state.get("team_briefing", ""),
        )

        iniciar = st.form_submit_button(
            "🚀 Iniciar Reunião de Time",
            type="primary",
            use_container_width=True,
        )

    if not iniciar and "team_resultado" not in st.session_state:
        st.info(
            "Preencha o briefing e clique em **Iniciar Reunião de Time** para que os especialistas "
            "debatam a melhor estratégia para **" + (cliente.nome if cliente else "o cliente") + "**."
        )
        return

    # ── Execução da reunião ────────────────────────────────────────────────────
    if iniciar:
        if not briefing.strip():
            st.error("Preencha o briefing antes de iniciar.")
            return

        st.session_state["team_briefing"] = briefing
        st.session_state.pop("team_resultado", None)

        contribuicoes = []

        with st.status("Reunião em andamento...", expanded=True) as status_box:
            session = TeamSession(
                nome_cliente=cliente.nome if cliente else "Cliente",
                segmento=cliente.segmento if cliente else "",
                cidade=cliente.cidade if cliente else "",
                tipo=tipo_key,
                briefing=briefing,
            )

            def progresso(etapa, agente, texto):
                label_etapa = _ETAPA_LABEL.get(etapa, etapa)
                nome_curto = agente.split("—")[-1].strip() if "—" in agente else agente
                status_box.write(f"**{label_etapa}** — {nome_curto}")
                contribuicoes.append({"etapa": etapa, "agente": agente, "texto": texto})

            resultado = session.rodar(callback=progresso)
            status_box.update(label="Reunião concluída!", state="complete")

        st.session_state["team_resultado"] = {
            "contribuicoes": contribuicoes,
            "sintese": resultado["sintese_final"],
            "tipo_label": tipo_label,
        }
        st.rerun()

    # ── Exibição dos resultados ────────────────────────────────────────────────
    if "team_resultado" not in st.session_state:
        return

    dados = st.session_state["team_resultado"]
    contribuicoes = dados["contribuicoes"]
    sintese = dados["sintese"]

    st.divider()
    st.markdown(f"### Resultado — {dados['tipo_label']}")

    # Tabs por rodada
    tab_r1, tab_r2, tab_sintese = st.tabs([
        "📌 Rodada 1 — Análise Inicial",
        "💬 Rodada 2 — Debate",
        "📋 Plano Final",
    ])

    with tab_r1:
        r1 = [c for c in contribuicoes if c["etapa"] == "rodada_1"]
        if r1:
            for c in r1:
                _card_contribuicao(c["agente"], c["texto"], c["etapa"])
        else:
            st.info("Nenhuma contribuição da Rodada 1.")

    with tab_r2:
        r2 = [c for c in contribuicoes if c["etapa"] == "rodada_2"]
        if r2:
            for c in r2:
                _card_contribuicao(c["agente"], c["texto"], c["etapa"])
        else:
            st.info("Nenhuma contribuição da Rodada 2.")

    with tab_sintese:
        _card_contribuicao("📋 Moderador — Plano Final", sintese, "sintese")

        st.download_button(
            "⬇️ Baixar Plano Final (.txt)",
            data=sintese,
            file_name=f"plano_{(cliente.nome if cliente else 'cliente').replace(' ','_')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # Botão de nova reunião
    st.divider()
    if st.button("🔄 Nova Reunião", use_container_width=True):
        st.session_state.pop("team_resultado", None)
        st.session_state.pop("team_briefing", None)
        st.rerun()
