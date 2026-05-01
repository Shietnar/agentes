"""
Sidebar — UnboundSales
Dark premium navigation with client selector.
"""
import streamlit as st
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from database.models import SessionLocal, Cliente


def _carregar_clientes():
    db = SessionLocal()
    try:
        return db.query(Cliente).order_by(Cliente.nome).all()
    finally:
        db.close()


def render_sidebar():
    with st.sidebar:
        # ── Logo ──────────────────────────────────────────────────────────────
        st.markdown(
            """
            <div style='padding:22px 16px 16px;border-bottom:1px solid rgba(0,207,253,0.10);margin-bottom:12px'>
              <div style='font-size:19px;font-weight:900;letter-spacing:-0.5px;line-height:1'>
                <span style='color:#FFFFFF'>Unbound</span><span style='color:#00CFFD;text-shadow:0 0 12px rgba(0,207,253,0.5)'>Sales</span>
              </div>
              <div style='font-size:9px;color:#1e3a4a;letter-spacing:2.5px;margin-top:4px;font-weight:700'>
                PAINEL DE IA
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Cliente ───────────────────────────────────────────────────────────
        clientes = _carregar_clientes()
        if not clientes:
            st.markdown(
                "<p style='font-size:12px;color:#475569;padding:0 4px'>Nenhum cliente cadastrado.</p>",
                unsafe_allow_html=True,
            )
            cliente_selecionado = None
        else:
            nomes = [f"{c.nome}" for c in clientes]
            idx_atual = st.session_state.get("cliente_idx", 0)
            idx = st.selectbox(
                "Cliente",
                range(len(nomes)),
                format_func=lambda i: nomes[i],
                index=min(idx_atual, len(nomes) - 1),
                label_visibility="visible",
            )
            st.session_state["cliente_idx"] = idx
            cliente_selecionado = clientes[idx]

            if st.session_state.get("_cliente_id") != cliente_selecionado.id:
                for key in [
                    "expert_dados", "expert_analise", "expert_phase",
                    "copy_resultado", "market_resultado", "lp_analise", "lp_html",
                    "team_resultado", "team_briefing", "social_resultado",
                    "designer_resultado", "director_resultado",
                    "director_etapas", "director_pedido",
                ]:
                    st.session_state.pop(key, None)
                st.session_state["_cliente_id"] = cliente_selecionado.id

        # ── IA Central ────────────────────────────────────────────────────────
        pagina_atual = st.session_state.get("page", "overview")

        st.markdown(
            "<p style='font-size:10px;font-weight:700;text-transform:uppercase;"
            "letter-spacing:1.2px;color:#334155;padding:16px 4px 6px'>IA Central</p>",
            unsafe_allow_html=True,
        )

        _nav_btn("🎬  Diretor",       "director", pagina_atual)
        _nav_btn("💬  Consulta Livre","consulta",  pagina_atual)

        # ── Por Cliente ───────────────────────────────────────────────────────
        st.markdown(
            "<p style='font-size:10px;font-weight:700;text-transform:uppercase;"
            "letter-spacing:1.2px;color:#334155;padding:14px 4px 6px'>Por Cliente</p>",
            unsafe_allow_html=True,
        )

        _nav_btn("📊  Visão Geral",         "overview",   pagina_atual)
        _nav_btn("🤝  Reunião de Time",      "team",       pagina_atual)
        _nav_btn("🎯  Estratégia",           "market",     pagina_atual)
        _nav_btn("✍️  Copywriter RSA",       "copywriter", pagina_atual)
        _nav_btn("🔬  Google Ads",           "expert",     pagina_atual)
        _nav_btn("🌐  Landing Pages",        "landing",    pagina_atual)
        _nav_btn("📱  Mídias Sociais",       "social",     pagina_atual)
        _nav_btn("🎨  Designer",             "designer",   pagina_atual)
        _nav_btn("👥  Leads",                "leads",      pagina_atual)
        _nav_btn("⚙️  Clientes",             "clientes",   pagina_atual)

        # ── Cliente ativo (rodapé) ────────────────────────────────────────────
        if cliente_selecionado:
            seg = cliente_selecionado.segmento or ""
            cid = cliente_selecionado.cidade or ""
            info = " · ".join(filter(None, [seg, cid]))
            st.markdown(
                f"""
                <div style='margin-top:20px;padding:11px 14px;
                            background:rgba(0,207,253,0.05);
                            border:1px solid rgba(0,207,253,0.18);
                            border-radius:10px'>
                  <div style='font-size:12px;font-weight:700;color:#e2e8f0;
                              white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>
                    {cliente_selecionado.nome}
                  </div>
                  <div style='font-size:11px;color:#2a4a5c;margin-top:2px'>{info}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ── Reiniciar servidor ────────────────────────────────────────────────
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        _render_restart_btn()

    return cliente_selecionado


def _render_restart_btn():
    """Botão de reinicialização do servidor com confirmação de 1 clique."""
    confirmando = st.session_state.get("_restart_confirm", False)

    if not confirmando:
        if st.button("↺  Reiniciar servidor", key="btn_restart",
                     use_container_width=True):
            st.session_state["_restart_confirm"] = True
            st.rerun()
    else:
        st.markdown(
            "<p style='font-size:11px;color:#F59E0B;padding:0 4px;margin-bottom:6px'>"
            "Confirma reinicialização?</p>",
            unsafe_allow_html=True,
        )
        col_ok, col_cancel = st.columns(2)
        with col_ok:
            if st.button("Sim", key="btn_restart_ok",
                         type="primary", use_container_width=True):
                st.session_state["_restart_confirm"] = False
                _executar_restart()
        with col_cancel:
            if st.button("Não", key="btn_restart_cancel",
                         use_container_width=True):
                st.session_state["_restart_confirm"] = False
                st.rerun()


def _executar_restart():
    """Mata o servidor atual e sobe um novo em background."""
    script = os.path.join(_PROJECT, "start_dashboard.sh")
    subprocess.Popen(["bash", script],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL,
                     start_new_session=True)
    st.markdown(
        """
        <div style='background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;
                    padding:12px 14px;margin-top:8px'>
          <div style='font-size:12px;font-weight:700;color:#92400E'>Reiniciando…</div>
          <div style='font-size:11px;color:#B45309;margin-top:4px'>
            Aguarde 5 segundos e<br>recarregue a página (F5).
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()


def _nav_btn(label: str, page_key: str, pagina_atual: str):
    """Botão de navegação — primary quando selecionado."""
    is_active = pagina_atual == page_key
    if st.button(
        label,
        key=f"nav_{page_key}",
        use_container_width=True,
        type="primary" if is_active else "secondary",
    ):
        st.session_state["page"] = page_key
        st.rerun()
