"""Copywriter RSA — geração de anúncios estruturados."""
import streamlit as st
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.copywriter_agent import criar_anuncios_json

_CAT_LABELS = {
    "keyword_cidade":  ("🗺️", "#1565C0"),
    "urgencia":        ("⚡", "#C62828"),
    "beneficio":       ("💎", "#2E7D32"),
    "prova_social":    ("⭐", "#F57F17"),
    "cta":             ("📞", "#6A1B9A"),
    "garantia":        ("🛡️", "#00838F"),
    "diferencial":     ("🚀", "#558B2F"),
}


def _char_bar(chars: int, maximo: int):
    """Renderiza uma mini barra de progresso de caracteres."""
    pct = min(chars / maximo, 1.0)
    color = "#2E7D32" if chars <= maximo else "#C62828"
    width = round(pct * 100)
    return (
        f"<div style='display:flex;align-items:center;gap:6px'>"
        f"<div style='flex:1;height:6px;background:#e0e0e0;border-radius:3px'>"
        f"<div style='width:{width}%;height:100%;background:{color};border-radius:3px'></div>"
        f"</div>"
        f"<span style='font-size:11px;color:{color};font-weight:600;white-space:nowrap'>"
        f"{chars}/{maximo}</span></div>"
    )


def render(cliente):
    st.header("✍️ Copywriter RSA")
    st.caption("Gera 15 títulos, 4 descrições e sitelinks otimizados para Google Ads.")

    with st.form("form_copy"):
        col1, col2 = st.columns([2, 1])
        segmento = col1.text_input("Segmento", value=cliente.segmento or "")
        cidade = col2.text_input("Cidade", value=cliente.cidade or "")

        info = st.text_area(
            "Briefing do cliente",
            height=120,
            value=(
                f"Empresa: {cliente.nome}\n"
                f"Segmento: {cliente.segmento}\n"
                f"Cidade: {cliente.cidade}\n"
            ),
            help="Inclua: serviços oferecidos, diferenciais, horário, anos de experiência, preços.",
        )

        estrategia = st.text_area(
            "Estratégia (opcional)",
            height=80,
            placeholder="Cole aqui a estratégia gerada pelo Agente de Negócio, se disponível.",
        )

        submitted = st.form_submit_button(
            "✍️ Gerar Anúncios RSA", type="primary", use_container_width=True
        )

    if submitted:
        if not info.strip():
            st.warning("Preencha o briefing do cliente.")
            return
        with st.spinner("Criando anúncios RSA com IA especialista..."):
            resultado = criar_anuncios_json(info, estrategia, segmento)
            st.session_state["copy_resultado"] = resultado

    if "copy_resultado" in st.session_state:
        r = st.session_state["copy_resultado"]

        if "erro" in r:
            st.error(f"Erro: {r['erro']}")
            return

        st.success("✅ Anúncios gerados!")
        pont = r.get("pontuacao", {})

        # ── Score ────────────────────────────────────────────────────────────
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Headlines válidos",
                    f"{pont.get('headlines_validos')}/{pont.get('headlines_total')}")
        col2.metric("Descrições válidas",
                    f"{pont.get('descriptions_validas')}/{pont.get('descriptions_total')}")
        col3.metric("Diversidade",
                    f"{pont.get('score')}%")
        col4.metric("Categorias",
                    len(pont.get("categorias_cobertas", [])))

        st.divider()

        # ── Headlines ────────────────────────────────────────────────────────
        st.subheader("📌 Headlines (máx. 30 chars)")
        st.caption("Agrupe por categoria para identificar diversidade. "
                   "Verde = válido · Vermelho = excedeu o limite.")

        cols = st.columns(3)
        for i, h in enumerate(r.get("headlines", [])):
            icone, cor = _CAT_LABELS.get(h.get("categoria", ""), ("📝", "#888"))
            valido = h.get("valido", True)
            borda = "#2E7D32" if valido else "#C62828"
            with cols[i % 3]:
                st.markdown(
                    f"""<div style='border:1px solid {borda};border-radius:6px;
                    padding:8px 10px;margin-bottom:8px'>
                    <span style='font-size:11px;color:{cor}'>{icone} {h.get('categoria','')}</span><br>
                    <strong style='font-size:14px'>{h['texto']}</strong><br>
                    {_char_bar(h.get('chars', len(h['texto'])), 30)}
                    </div>""",
                    unsafe_allow_html=True,
                )

        st.divider()

        # ── Descriptions ─────────────────────────────────────────────────────
        st.subheader("📝 Descrições (máx. 90 chars)")
        for i, d in enumerate(r.get("descriptions", [])):
            valido = d.get("valido", True)
            cor = "#2E7D32" if valido else "#C62828"
            st.markdown(
                f"""<div style='border-left:4px solid {cor};padding:8px 12px;
                margin:4px 0;background:#fafafa;border-radius:4px'>
                <strong>Desc {i+1}:</strong> {d['texto']}<br>
                {_char_bar(d.get('chars', len(d['texto'])), 90)}
                </div>""",
                unsafe_allow_html=True,
            )

        st.divider()

        # ── Sitelinks ────────────────────────────────────────────────────────
        st.subheader("🔗 Sitelinks")
        sitelinks = r.get("sitelinks", [])
        if sitelinks:
            cols = st.columns(min(len(sitelinks), 4))
            for i, sl in enumerate(sitelinks):
                with cols[i % 4]:
                    st.markdown(
                        f"""<div style='background:#f0f4ff;border-radius:6px;
                        padding:10px;text-align:center'>
                        <strong style='color:#1565C0'>{sl.get('titulo','')}</strong><br>
                        <span style='font-size:12px;color:#666'>{sl.get('descricao','')}</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )

        # ── Estratégia de copy ───────────────────────────────────────────────
        estrategia_copy = r.get("estrategia_copy", "")
        if estrategia_copy:
            with st.expander("💡 Estratégia de comunicação usada"):
                st.write(estrategia_copy)

        st.divider()

        # ── Exportar ─────────────────────────────────────────────────────────
        col_pdf, col_a, col_b = st.columns(3)
        try:
            from tools.pdf_exporter import gerar_pdf_copy
            pdf_bytes = gerar_pdf_copy(r, cliente.nome, segmento)
            col_pdf.download_button(
                "📄 Exportar PDF",
                data=pdf_bytes,
                file_name=f"rsa_{cliente.nome.lower().replace(' ', '_')}.pdf",
                mime="application/pdf",
                type="primary",
            )
        except Exception as e:
            col_pdf.error(f"PDF: {e}")
        col_a.download_button(
            "⬇️ Exportar JSON",
            data=json.dumps(r, ensure_ascii=False, indent=2),
            file_name=f"rsa_{cliente.nome.lower().replace(' ', '_')}.json",
            mime="application/json",
        )

        # Texto simples para colar no Google Ads
        linhas_txt = ["=== HEADLINES ==="]
        for h in r.get("headlines", []):
            linhas_txt.append(f"{h['texto']} ({h.get('chars', '')} chars)")
        linhas_txt.append("\n=== DESCRIÇÕES ===")
        for d in r.get("descriptions", []):
            linhas_txt.append(f"{d['texto']} ({d.get('chars', '')} chars)")
        linhas_txt.append("\n=== SITELINKS ===")
        for sl in r.get("sitelinks", []):
            linhas_txt.append(f"{sl.get('titulo','')} | {sl.get('descricao','')}")

        col_b.download_button(
            "⬇️ Exportar TXT",
            data="\n".join(linhas_txt),
            file_name=f"rsa_{cliente.nome.lower().replace(' ', '_')}.txt",
            mime="text/plain",
        )
