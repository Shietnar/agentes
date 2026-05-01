"""Visão Geral — métricas e pipeline do cliente selecionado."""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.models import SessionLocal, Cliente, Campanha, Lead, StatusLead
from dashboard.components import page_header, pipeline_card, campaign_row, section_title, empty_state


def render(cliente):
    st.markdown(page_header("📊", "Visão Geral", f"{cliente.segmento} · {cliente.cidade or '—'}"),
                unsafe_allow_html=True)

    db = SessionLocal()
    try:
        total_clientes   = db.query(Cliente).count()
        total_campanhas  = db.query(Campanha).filter(Campanha.cliente_id == cliente.id).count()
        leads_cliente    = db.query(Lead).filter(Lead.cliente_id == cliente.id).all()
        campanhas        = db.query(Campanha).filter(Campanha.cliente_id == cliente.id).all()
    finally:
        db.close()

    total_leads       = len(leads_cliente)
    leads_novos       = sum(1 for l in leads_cliente if l.status == StatusLead.novo)
    leads_em_atend    = sum(1 for l in leads_cliente if l.status == StatusLead.em_atendimento)
    leads_agendados   = sum(1 for l in leads_cliente if l.status == StatusLead.agendado)
    leads_convertidos = sum(1 for l in leads_cliente if l.status == StatusLead.convertido)
    leads_perdidos    = sum(1 for l in leads_cliente if l.status == StatusLead.perdido)
    taxa_conv = f"{round(leads_convertidos / total_leads * 100)}%" if total_leads else "—"

    # ── Métricas principais ───────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Campanhas",        total_campanhas)
    c2.metric("Total de Leads",   total_leads)
    c3.metric("Leads Novos",      leads_novos,
              delta=f"+{leads_novos} aguardando" if leads_novos else None)
    c4.metric("Taxa de Conversão", taxa_conv)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Pipeline ──────────────────────────────────────────────────────────────
    st.markdown(section_title("Pipeline de Leads"), unsafe_allow_html=True)

    if total_leads == 0:
        st.markdown(
            empty_state("👥", "Nenhum lead ainda",
                        "Os leads chegam via atendimento virtual ou cadastro manual."),
            unsafe_allow_html=True,
        )
    else:
        cols = st.columns(5)
        stages = [
            ("Novos",          leads_novos,       "#3B82F6", cols[0]),
            ("Em Atendimento", leads_em_atend,     "#F59E0B", cols[1]),
            ("Agendados",      leads_agendados,    "#8B5CF6", cols[2]),
            ("Convertidos",    leads_convertidos,  "#10B981", cols[3]),
            ("Perdidos",       leads_perdidos,     "#EF4444", cols[4]),
        ]
        for label, value, color, col in stages:
            col.markdown(pipeline_card(label, value, color), unsafe_allow_html=True)

        # Funil visual
        if total_leads > 0:
            try:
                import plotly.graph_objects as go
                fig = go.Figure(go.Funnel(
                    y=["Novos", "Em Atendimento", "Agendados", "Convertidos"],
                    x=[
                        leads_novos + leads_em_atend + leads_agendados + leads_convertidos,
                        leads_em_atend + leads_agendados + leads_convertidos,
                        leads_agendados + leads_convertidos,
                        leads_convertidos,
                    ],
                    textposition="inside",
                    textinfo="value+percent initial",
                    marker_color=["#3B82F6", "#F59E0B", "#8B5CF6", "#10B981"],
                    connector={"line": {"color": "#E2E8F0", "width": 1}},
                ))
                fig.update_layout(
                    height=280,
                    margin=dict(t=12, b=8, l=0, r=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter, sans-serif", size=13, color="#374151"),
                )
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                pass

    # ── Campanhas ─────────────────────────────────────────────────────────────
    st.markdown(section_title("Campanhas"), unsafe_allow_html=True)

    if not campanhas:
        st.markdown(
            empty_state("🔬", "Nenhuma campanha vinculada",
                        "Use **Google Ads** para criar ou vincular uma campanha."),
            unsafe_allow_html=True,
        )
    else:
        for camp in campanhas:
            st.markdown(
                campaign_row(
                    camp.nome,
                    camp.google_ads_id or "—",
                    str(camp.orcamento_diario) if camp.orcamento_diario else "—",
                    camp.status or "—",
                ),
                unsafe_allow_html=True,
            )

    # ── Rodapé ────────────────────────────────────────────────────────────────
    st.markdown(
        f"<p style='font-size:12px;color:#94A3B8;margin-top:16px'>"
        f"Plataforma com {total_clientes} cliente(s) cadastrado(s)</p>",
        unsafe_allow_html=True,
    )
