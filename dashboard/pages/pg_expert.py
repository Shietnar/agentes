"""Especialista Google Ads — análise completa com aprovação de melhorias."""
import streamlit as st
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.models import SessionLocal, Campanha
from config.settings import GOOGLE_ADS_LOGIN_CUSTOMER_ID

_PRI_CONFIG = {
    "CRITICO":    ("#C62828", "🔴"),
    "IMPORTANTE": ("#F57F17", "🟡"),
    "MELHORIA":   ("#2E7D32", "🟢"),
}


def _badge(prioridade: str) -> str:
    cor, icone = _PRI_CONFIG.get(prioridade, ("#888", "⚪"))
    return (
        f"<span style='background:{cor};color:white;padding:2px 8px;"
        f"border-radius:10px;font-size:11px;font-weight:700'>{icone} {prioridade}</span>"
    )


def render(cliente):
    st.header("🔬 Especialista Google Ads")
    st.caption("Análise completa de campanha com recomendações e aplicação de melhorias via API.")

    # ── Configuração ───────────────────────────────────────────────────────────
    db = SessionLocal()
    try:
        campanhas_db = db.query(Campanha).filter(
            Campanha.cliente_id == cliente.id,
            Campanha.google_ads_id.isnot(None),
        ).all()
    finally:
        db.close()

    with st.expander("⚙️ Configuração da campanha", expanded="expert_analise" not in st.session_state):
        col1, col2 = st.columns([2, 1])
        customer_id = col1.text_input(
            "Customer ID",
            value=GOOGLE_ADS_LOGIN_CUSTOMER_ID or "",
            help="ID da conta Google Ads (sem traços)",
        )

        if campanhas_db:
            opcoes = {f"{c.nome} ({c.google_ads_id})": c.google_ads_id for c in campanhas_db}
            opcoes["Outro..."] = ""
            sel = col2.selectbox("Campanha", list(opcoes.keys()))
            campaign_id = opcoes[sel] if opcoes[sel] else col2.text_input("ID manual")
        else:
            campaign_id = col2.text_input("Campaign ID", placeholder="Ex: 1234567890")

        st.session_state["_expert_customer_id"] = customer_id
        st.session_state["_expert_campaign_id"] = campaign_id

        if st.button("🔍 Analisar Campanha", type="primary", use_container_width=True):
            if not customer_id or not campaign_id:
                st.error("Preencha o Customer ID e o Campaign ID.")
            else:
                st.session_state["expert_phase"] = "coletando"
                st.rerun()

    # ── Fase: coletando dados ──────────────────────────────────────────────────
    if st.session_state.get("expert_phase") == "coletando":
        customer_id = st.session_state["_expert_customer_id"]
        campaign_id = st.session_state["_expert_campaign_id"]

        from agents.expert_agent import coletar_dados_campanha, gerar_recomendacoes_json
        from google.ads.googleads.errors import GoogleAdsException

        progress = st.progress(0.0, text="Iniciando coleta...")

        def atualizar_progress(pct, label):
            progress.progress(pct, text=f"Buscando {label}...")

        try:
            dados = coletar_dados_campanha(customer_id, campaign_id, atualizar_progress)
            st.session_state["expert_dados"] = dados
        except GoogleAdsException as e:
            st.error(f"Erro Google Ads API: {e.failure.errors[0].message}")
            st.session_state.pop("expert_phase", None)
            st.stop()
        except Exception as e:
            st.error(f"Erro na coleta: {e}")
            st.session_state.pop("expert_phase", None)
            st.stop()

        progress.progress(1.0, text="Dados coletados! Chamando especialista Claude...")

        with st.spinner("Analisando tudo com o especialista IA..."):
            analise = gerar_recomendacoes_json(dados, cliente.nome, campaign_id)
            st.session_state["expert_analise"] = analise

        st.session_state["expert_phase"] = "revisao"
        st.rerun()

    # ── Fase: revisão e aprovação ──────────────────────────────────────────────
    if "expert_analise" not in st.session_state:
        return

    analise = st.session_state["expert_analise"]
    dados = st.session_state.get("expert_dados", {})
    customer_id = st.session_state.get("_expert_customer_id", "")

    if "erro" in analise:
        st.error(f"Erro na análise: {analise['erro']}")
        return

    st.success("✅ Análise concluída!")

    # Score
    score = analise.get("score_campanha", 0)
    score_color = "#C62828" if score <= 4 else "#F57F17" if score <= 6 else "#2E7D32"
    col1, col2, col3 = st.columns([1, 3, 1])
    col1.markdown(
        f"""<div style='text-align:center;background:{score_color}15;
        border:3px solid {score_color};border-radius:50%;width:80px;height:80px;
        display:flex;align-items:center;justify-content:center;margin:auto'>
        <span style='font-size:28px;font-weight:900;color:{score_color}'>{score}</span>
        </div><div style='text-align:center;font-size:11px;color:#666;margin-top:4px'>
        /10</div>""",
        unsafe_allow_html=True,
    )
    with col2:
        st.markdown(f"### Diagnóstico\n{analise.get('resumo_executivo', '')}")

    st.divider()

    # Pontos críticos e positivos
    col_neg, col_pos = st.columns(2)
    with col_neg:
        st.markdown("#### 🔴 Problemas Identificados")
        for p in analise.get("pontos_criticos", []):
            st.markdown(f"• {p}")
    with col_pos:
        st.markdown("#### 🟢 Pontos Fortes")
        for p in analise.get("pontos_positivos", []):
            st.markdown(f"• {p}")

    st.divider()

    # ── Métricas da campanha (se disponíveis) ──────────────────────────────────
    metricas = dados.get("metricas", {})
    if metricas and isinstance(metricas, dict) and "impressoes" in metricas:
        st.subheader("📊 Métricas dos últimos 30 dias")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Impressões", f"{metricas.get('impressoes', 0):,}")
        c2.metric("Cliques", f"{metricas.get('cliques', 0):,}")
        c3.metric("CTR", f"{metricas.get('ctr_pct', 0):.1f}%")
        c4.metric("CPC médio", f"R$ {metricas.get('cpc_medio_brl', 0):.2f}")
        c5.metric("Custo", f"R$ {metricas.get('custo_total_brl', 0):.2f}")
        c6.metric("Conversões", f"{metricas.get('conversoes', 0):.0f}")

        # Mini gráfico dispositivos
        dispositivos = dados.get("dispositivos", [])
        if dispositivos:
            try:
                import plotly.express as px
                df_dev = {
                    "Dispositivo": [d["dispositivo"] for d in dispositivos],
                    "Custo (R$)": [d["custo_brl"] for d in dispositivos],
                }
                fig = px.pie(df_dev, values="Custo (R$)", names="Dispositivo",
                             title="Custo por dispositivo",
                             color_discrete_sequence=["#1565C0", "#2E7D32", "#F57F17"])
                fig.update_layout(height=260, margin=dict(t=40, b=10, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                pass

        st.divider()

    # ── Keywords com QS ruim ───────────────────────────────────────────────────
    keywords = dados.get("keywords", [])
    if keywords:
        kws_ruins = [k for k in keywords if isinstance(k, dict) and k.get("quality_score", 10) <= 6]
        if kws_ruins:
            with st.expander(f"⚠️ Keywords com Quality Score baixo ({len(kws_ruins)})"):
                for kw in kws_ruins[:20]:
                    qs = kw.get("quality_score", "?")
                    cor = "#C62828" if qs and qs <= 4 else "#F57F17"
                    st.markdown(
                        f"""<div style='display:flex;justify-content:space-between;
                        padding:4px 0;border-bottom:1px solid #eee'>
                        <span>{kw.get('texto','')} <em style='color:#888;font-size:12px'>
                        [{kw.get('match_type','')}]</em></span>
                        <span style='color:{cor};font-weight:700'>QS {qs}/10 •
                        R$ {kw.get('custo_total_brl', 0):.2f}</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )

    st.divider()

    # ── Recomendações com checkboxes ───────────────────────────────────────────
    st.subheader("🔧 Recomendações — selecione as que deseja aplicar")

    recomendacoes = analise.get("recomendacoes", [])
    selecionadas = []

    for rec in recomendacoes:
        cor, icone = _PRI_CONFIG.get(rec.get("prioridade", ""), ("#888", "⚪"))
        pode_aplicar = rec.get("acao") and rec["acao"] != "informativo"

        with st.container():
            col_check, col_info = st.columns([0.07, 0.93])
            with col_check:
                checked = st.checkbox(
                    "",
                    key=f"rec_{rec.get('id', rec['titulo'][:20])}",
                    disabled=not pode_aplicar,
                )
            with col_info:
                st.markdown(
                    f"{_badge(rec.get('prioridade',''))} "
                    f"**{rec['titulo']}**",
                    unsafe_allow_html=True,
                )
                st.caption(f"_{rec.get('justificativa','')}_ • {rec.get('impacto_esperado','')}")
                if not pode_aplicar:
                    st.caption("ℹ️ Recomendação informativa — aplicação manual necessária")

            if checked and pode_aplicar:
                selecionadas.append(rec)

    st.divider()

    col_btn, col_info = st.columns([1, 2])
    aplicar = col_btn.button(
        f"✅ Aplicar {len(selecionadas)} melhoria(s)",
        type="primary",
        disabled=len(selecionadas) == 0,
        use_container_width=True,
    )
    col_info.caption(
        "As melhorias são aplicadas diretamente na conta Google Ads. "
        "Campanhas são modificadas em tempo real."
    )

    if aplicar and selecionadas:
        from agents.expert_agent import aplicar_melhorias
        from google.ads.googleads.errors import GoogleAdsException

        with st.spinner("Aplicando melhorias na API do Google Ads..."):
            try:
                resultados = aplicar_melhorias(customer_id, selecionadas)
            except GoogleAdsException as e:
                st.error(f"Erro API: {e.failure.errors[0].message}")
                return
            except Exception as e:
                st.error(f"Erro: {e}")
                return

        st.subheader("📋 Resultado das Aplicações")
        for res in resultados:
            if res["sucesso"]:
                st.success(f"✅ {res['titulo']}")
            else:
                erro = res.get("resultado", {}).get("erro", "Erro desconhecido")
                st.error(f"❌ {res['titulo']}: {erro}")

    # ── Botão de nova análise ──────────────────────────────────────────────────
    st.divider()
    if st.button("🔄 Nova análise", use_container_width=False):
        for key in ["expert_dados", "expert_analise", "expert_phase"]:
            st.session_state.pop(key, None)
        st.rerun()
