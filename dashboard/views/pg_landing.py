"""Landing Pages — análise de URL e geração de LP."""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.landing_agent import analisar_landing_page, gerar_landing_page_html

_NOTA_CORES = {"A": "#2E7D32", "B": "#558B2F", "C": "#F57F17", "D": "#E65100", "F": "#C62828"}
_DIM_LABELS = {
    "keywords":           "🔍 Keywords",
    "cta":                "📞 CTA",
    "trust_elements":     "🛡️ Confiança",
    "mobile_readiness":   "📱 Mobile",
    "velocidade_percebida": "⚡ Velocidade",
    "estrutura_persuasiva": "🧠 Persuasão",
}


def _nota_badge(nota: str) -> str:
    cor = _NOTA_CORES.get(nota, "#888")
    return (
        f"<span style='background:{cor};color:white;font-size:18px;font-weight:900;"
        f"padding:4px 12px;border-radius:6px'>{nota}</span>"
    )


def render(cliente):
    st.header("🌐 Landing Pages")

    tab_analise, tab_criar = st.tabs(["🔍 Analisar URL existente", "🛠️ Gerar nova Landing Page"])

    # ── TAB 1: Análise de URL ──────────────────────────────────────────────────
    with tab_analise:
        st.caption("Avalia a landing page atual nos 6 critérios de conversão para Google Ads.")

        url = st.text_input("URL da Landing Page", placeholder="https://www.exemplo.com.br")

        if st.button("🔍 Analisar", type="primary", key="btn_analisar"):
            if not url.startswith("http"):
                st.warning("Insira uma URL válida começando com http:// ou https://")
            else:
                with st.spinner(f"Buscando e analisando {url}..."):
                    resultado = analisar_landing_page(url)
                    st.session_state["lp_analise"] = resultado

        if "lp_analise" in st.session_state:
            r = st.session_state["lp_analise"]

            if "erro" in r:
                st.error(f"Erro: {r['erro']}")
            else:
                st.success("✅ Análise concluída!")

                # Nota geral
                col_nota, col_score = st.columns([1, 3])
                nota = r.get("nota_geral", "?")
                score = r.get("score_percentual", 0)
                col_nota.markdown(
                    f"<div style='text-align:center;margin-top:8px'>"
                    f"{_nota_badge(nota)}<br>"
                    f"<span style='font-size:12px;color:#888;margin-top:4px'>Nota geral</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                col_score.progress(score / 100, text=f"Score: {score}/100")

                st.divider()

                # Dimensões
                st.subheader("📋 Dimensões avaliadas")
                dimensoes = r.get("dimensoes", {})
                cols = st.columns(3)
                for i, (key, label) in enumerate(_DIM_LABELS.items()):
                    dim = dimensoes.get(key, {})
                    nota_dim = dim.get("nota", "?")
                    cor = _NOTA_CORES.get(nota_dim, "#888")
                    with cols[i % 3]:
                        st.markdown(
                            f"""<div style='border:2px solid {cor};border-radius:8px;
                            padding:12px;margin-bottom:10px;text-align:center'>
                            <div style='font-size:13px;color:#666'>{label}</div>
                            <div style='font-size:28px;font-weight:900;color:{cor}'>{nota_dim}</div>
                            <div style='font-size:11px;color:#444;margin-top:4px'>
                            {dim.get('obs','')}</div>
                            </div>""",
                            unsafe_allow_html=True,
                        )

                # Problemas e recomendações
                col_prob, col_rec = st.columns(2)
                with col_prob:
                    st.markdown("#### 🔴 Problemas críticos")
                    for p in r.get("problemas_criticos", []):
                        st.markdown(f"• {p}")
                with col_rec:
                    st.markdown("#### ✅ Recomendações priorizadas")
                    for rec in r.get("recomendacoes_priorizadas", []):
                        st.markdown(f"• {rec}")

                pontos_pos = r.get("pontos_positivos", [])
                if pontos_pos:
                    with st.expander("💚 Pontos positivos encontrados"):
                        for p in pontos_pos:
                            st.markdown(f"• {p}")

    # ── TAB 2: Gerar nova LP ───────────────────────────────────────────────────
    with tab_criar:
        st.caption("Gera HTML completo, standalone e mobile-first para hospedar imediatamente.")

        with st.form("form_lp"):
            col1, col2 = st.columns(2)
            nome = col1.text_input("Nome da empresa", value=cliente.nome)
            segmento = col2.text_input("Segmento", value=cliente.segmento or "")

            col3, col4 = st.columns(2)
            cidade = col3.text_input("Cidade", value=cliente.cidade or "")
            cor_primaria = col4.color_picker("Cor primária", value="#e53935")

            col5, col6 = st.columns(2)
            telefone = col5.text_input("Telefone", placeholder="(11) 9 9999-0000",
                                       value=cliente.telefone or "")
            whatsapp = col6.text_input("WhatsApp (DDI+DDD+número)",
                                       placeholder="5511999990000")

            servicos_txt = st.text_area(
                "Serviços oferecidos (um por linha)",
                height=100,
                placeholder="Desentupimento de esgoto\nDesentupimento de pia\nCaixa de gordura",
            )

            diferenciais_txt = st.text_area(
                "Diferenciais (um por linha)",
                height=100,
                placeholder="Atendimento 24 horas\nChega em até 1 hora\nOrçamento grátis\nGarantia no serviço",
            )

            col7, col8 = st.columns(2)
            anos = col7.number_input("Anos de experiência", min_value=0, max_value=50, value=0)
            keywords_txt = col8.text_input(
                "Keywords principais (vírgula)",
                placeholder="desentupidora sp, desentupimento emergência",
            )

            gerar = st.form_submit_button("🛠️ Gerar Landing Page", type="primary", use_container_width=True)

        if gerar:
            servicos = [s.strip() for s in servicos_txt.splitlines() if s.strip()]
            diferenciais = [d.strip() for d in diferenciais_txt.splitlines() if d.strip()]
            keywords = [k.strip() for k in keywords_txt.split(",") if k.strip()]

            if not servicos:
                st.warning("Adicione pelo menos um serviço.")
            else:
                with st.spinner("Gerando landing page com IA especialista..."):
                    html = gerar_landing_page_html(
                        nome_empresa=nome,
                        segmento=segmento,
                        cidade=cidade,
                        telefone=telefone,
                        telefone_whatsapp=whatsapp,
                        servicos=servicos,
                        diferenciais=diferenciais,
                        anos_experiencia=anos if anos > 0 else None,
                        cor_primaria=cor_primaria,
                        keywords_principais=keywords or None,
                    )
                    st.session_state["lp_html"] = html

        if "lp_html" in st.session_state:
            html = st.session_state["lp_html"]
            st.success(f"✅ Landing page gerada! {len(html):,} caracteres")

            # Preview
            st.subheader("👁️ Preview")
            st.components.v1.html(html, height=600, scrolling=True)

            # Download
            st.download_button(
                "⬇️ Baixar HTML",
                data=html.encode("utf-8"),
                file_name=f"lp_{nome.lower().replace(' ', '_')}.html",
                mime="text/html",
                use_container_width=True,
                type="primary",
            )
