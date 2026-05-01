"""Leads — visualização e gestão do pipeline."""
import streamlit as st
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.models import SessionLocal, Lead, StatusLead

_STATUS_LABEL = {
    StatusLead.novo: "🆕 Novo",
    StatusLead.em_atendimento: "💬 Em atendimento",
    StatusLead.agendado: "📅 Agendado",
    StatusLead.convertido: "✅ Convertido",
    StatusLead.perdido: "❌ Perdido",
}
_STATUS_CORES = {
    StatusLead.novo: "#1565C0",
    StatusLead.em_atendimento: "#F57F17",
    StatusLead.agendado: "#6A1B9A",
    StatusLead.convertido: "#2E7D32",
    StatusLead.perdido: "#C62828",
}


def render(cliente):
    st.header("👥 Leads")

    db = SessionLocal()
    try:
        leads = (
            db.query(Lead)
            .filter(Lead.cliente_id == cliente.id)
            .order_by(Lead.criado_em.desc())
            .all()
        )
    finally:
        db.close()

    if not leads:
        st.info("Nenhum lead cadastrado para este cliente ainda.")
        return

    # ── Filtros ────────────────────────────────────────────────────────────────
    col_f1, col_f2 = st.columns([2, 1])
    busca = col_f1.text_input("🔍 Buscar por nome ou telefone", "")
    status_filtro = col_f2.selectbox(
        "Filtrar por status",
        ["Todos"] + [_STATUS_LABEL[s] for s in StatusLead],
    )

    leads_filtrados = leads
    if busca:
        b = busca.lower()
        leads_filtrados = [
            l for l in leads_filtrados
            if b in (l.nome or "").lower() or b in (l.telefone or "")
        ]
    if status_filtro != "Todos":
        status_key = next(
            (k for k, v in _STATUS_LABEL.items() if v == status_filtro), None
        )
        if status_key:
            leads_filtrados = [l for l in leads_filtrados if l.status == status_key]

    st.caption(f"{len(leads_filtrados)} lead(s) exibido(s)")
    st.divider()

    # ── Tabela de leads ────────────────────────────────────────────────────────
    for lead in leads_filtrados:
        cor = _STATUS_CORES.get(lead.status, "#888")
        label = _STATUS_LABEL.get(lead.status, "?")
        data = lead.criado_em.strftime("%d/%m/%Y %H:%M") if lead.criado_em else "—"

        with st.container():
            col_info, col_status, col_acoes = st.columns([3, 2, 2])

            with col_info:
                st.markdown(
                    f"**{lead.nome or 'Sem nome'}**  "
                    f"<span style='color:#666;font-size:13px'>{lead.telefone or '—'}</span>",
                    unsafe_allow_html=True,
                )
                st.caption(f"📅 {data} • Origem: {lead.origem or '—'}")
                if lead.mensagem:
                    st.caption(f"💬 {lead.mensagem[:120]}{'...' if len(lead.mensagem) > 120 else ''}")

            with col_status:
                st.markdown(
                    f"<div style='padding:6px 10px;background:{cor}20;"
                    f"border-left:4px solid {cor};border-radius:4px;margin-top:6px'>"
                    f"<span style='color:{cor};font-weight:600'>{label}</span></div>",
                    unsafe_allow_html=True,
                )

            with col_acoes:
                novo_status = st.selectbox(
                    "Atualizar",
                    list(_STATUS_LABEL.values()),
                    index=list(StatusLead).index(lead.status),
                    key=f"status_{lead.id}",
                    label_visibility="collapsed",
                )
                if st.button("Salvar", key=f"salvar_{lead.id}", use_container_width=True):
                    novo_enum = next(
                        k for k, v in _STATUS_LABEL.items() if v == novo_status
                    )
                    db2 = SessionLocal()
                    try:
                        l = db2.query(Lead).filter(Lead.id == lead.id).first()
                        if l:
                            l.status = novo_enum
                            db2.commit()
                        st.success("Status atualizado!")
                    finally:
                        db2.close()

            st.markdown("<hr style='margin:4px 0;border:none;border-top:1px solid #eee'>",
                        unsafe_allow_html=True)
