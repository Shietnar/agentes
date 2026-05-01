"""Estratégia de Negócio — Agente de Mercado."""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.market_agent import analisar_mercado


def render(cliente):
    st.header("🎯 Estratégia de Negócio")
    st.caption("Análise de mercado, personas, posicionamento e plano de ação.")

    with st.form("form_market"):
        col1, col2 = st.columns(2)
        segmento = col1.text_input("Segmento", value=cliente.segmento or "")
        cidade = col2.text_input("Cidade / Região", value=cliente.cidade or "")

        briefing = st.text_area(
            "Informações do negócio",
            height=140,
            placeholder=(
                "Ex: empresa com 8 anos, 4 técnicos, atende zona norte e leste.\n"
                "Diferencial: atende 24h, emite nota fiscal, orçamento em 15 min.\n"
                "Orçamento Google Ads: R$ 80/dia. Ticket médio: R$ 350.\n"
                "Principal concorrente: EmpresaX que tem mais reviews no Google."
            ),
        )
        submitted = st.form_submit_button("🔍 Analisar Mercado", type="primary", use_container_width=True)

    if submitted:
        if not segmento or not briefing:
            st.warning("Preencha o segmento e as informações do negócio.")
            return

        with st.spinner("Analisando mercado e estratégia..."):
            resultado = analisar_mercado(segmento, cidade, briefing)
            st.session_state["market_resultado"] = resultado

    if "market_resultado" in st.session_state:
        r = st.session_state["market_resultado"]

        if "erro" in r:
            st.error(f"Erro: {r['erro']}")
            return

        # ── Resumo executivo ────────────────────────────────────────────────
        st.success("✅ Análise concluída!")
        st.markdown(f"### Resumo Executivo\n{r.get('resumo_executivo', '')}")
        st.divider()

        col1, col2 = st.columns(2)

        # ── Mercado ─────────────────────────────────────────────────────────
        with col1:
            st.subheader("📈 Mercado")
            m = r.get("analise_mercado", {})
            st.write(m.get("tamanho_e_crescimento", ""))

            saz = m.get("sazonalidade", {})
            if saz:
                st.markdown(f"**Sazonalidade:** {saz.get('observacao', '')}")
                if saz.get("meses_pico"):
                    st.markdown(f"🔺 Pico: {', '.join(saz['meses_pico'])}")
                if saz.get("meses_vale"):
                    st.markdown(f"🔻 Vale: {', '.join(saz['meses_vale'])}")

            st.markdown(f"**Concorrência:** {m.get('nivel_concorrencia', '')}")
            for t in m.get("tendencias", []):
                st.markdown(f"• {t}")

        # ── Posicionamento ──────────────────────────────────────────────────
        with col2:
            st.subheader("🎯 Posicionamento")
            pos = r.get("posicionamento", {})
            st.markdown(f"**Proposta de Valor:**\n> {pos.get('uvp', '')}")
            headline = pos.get("uvp_30_chars", "")
            chars = len(headline)
            color = "#2E7D32" if chars <= 30 else "#C62828"
            st.markdown(
                f"**Headline Google Ads ({chars}/30 chars):** "
                f"<span style='color:{color};font-weight:600'>{headline}</span>",
                unsafe_allow_html=True,
            )
            st.markdown(f"**Estratégia de Preço:** {pos.get('estrategia_preco', '')}")
            st.markdown(f"**Diferencial Principal:** {pos.get('diferencial_principal', '')}")

        st.divider()

        # ── Personas ────────────────────────────────────────────────────────
        st.subheader("👥 Personas")
        personas = r.get("personas", [])
        if personas:
            cols = st.columns(min(len(personas), 3))
            for i, p in enumerate(personas):
                with cols[i % len(cols)]:
                    st.markdown(
                        f"""<div style='background:#f5f5f5;border-radius:8px;
                        padding:14px;margin-bottom:8px'>
                        <strong style='font-size:16px'>{p['nome']}</strong><br>
                        <span style='color:#666;font-size:13px'>{p['perfil']}</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                    st.markdown("**Gatilhos:**")
                    for g in p.get("gatilhos_compra", []):
                        st.markdown(f"• {g}")
                    st.markdown("**Objeções:**")
                    for o in p.get("objecoes", []):
                        st.markdown(f"• {o}")
                    st.caption(f"Decisão: {p.get('criterio_decisao', '')}")

        st.divider()

        # ── Canais de atração ────────────────────────────────────────────────
        st.subheader("📡 Canais de Atração")
        canais = r.get("canais_atracao", [])
        pri_colors = {"alta": "#C62828", "média": "#F57F17", "baixa": "#2E7D32"}
        for canal in canais:
            pri = canal.get("prioridade", "média").lower()
            cor = pri_colors.get(pri, "#888")
            st.markdown(
                f"""<div style='border-left:4px solid {cor};padding:8px 12px;
                margin:4px 0;background:#fafafa;border-radius:4px'>
                <strong>{canal['canal']}</strong>
                <span style='float:right;color:{cor};font-size:12px;font-weight:600'>
                {canal.get('prioridade','').upper()}</span><br>
                <span style='font-size:13px;color:#444'>{canal.get('estrategia','')}</span>
                </div>""",
                unsafe_allow_html=True,
            )

        st.divider()

        # ── Plano de ação ────────────────────────────────────────────────────
        st.subheader("📅 Plano de Ação")
        pa = r.get("plano_acao", {})
        col_a, col_b, col_c = st.columns(3)
        for col, titulo, key, cor in [
            (col_a, "30 dias (Quick Wins)", "dias_30", "#1565C0"),
            (col_b, "60 dias (Consolidação)", "dias_60", "#F57F17"),
            (col_c, "90 dias (Crescimento)", "dias_90", "#2E7D32"),
        ]:
            with col:
                st.markdown(
                    f"<div style='font-weight:700;color:{cor};margin-bottom:8px'>{titulo}</div>",
                    unsafe_allow_html=True,
                )
                for acao in pa.get(key, []):
                    st.markdown(f"• {acao}")

        # ── Download JSON ────────────────────────────────────────────────────
        import json
        st.divider()
        st.download_button(
            "⬇️ Baixar Análise (JSON)",
            data=json.dumps(r, ensure_ascii=False, indent=2),
            file_name=f"estrategia_{cliente.nome.lower().replace(' ', '_')}.json",
            mime="application/json",
        )
