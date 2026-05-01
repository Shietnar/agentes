"""
Consulta Livre — UnboundSales Dashboard
Terminal de consulta direta aos agentes sem vínculo com cliente.
Modos: pergunta livre, análise de site, análise de Instagram, Google Ads.
"""
import streamlit as st
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.consulta import AGENTES


# ─── COMPONENTE: CARD DE RESPOSTA ─────────────────────────────────────────────

def _card(label: str, cor: str, texto: str):
    icone = label.split(" ")[0]
    nome = label.split("—")[-1].strip() if "—" in label else label
    st.markdown(
        f"""
        <div style="
            border-left: 4px solid {cor};
            background: #fafafa;
            border-radius: 0 8px 8px 0;
            padding: 14px 18px;
            margin-bottom: 14px;
        ">
          <div style="font-size:13px;font-weight:700;color:{cor};margin-bottom:8px">
            {icone} {nome}
          </div>
          <div style="font-size:14px;color:#212121;line-height:1.6;white-space:pre-wrap">{texto}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── RENDER PRINCIPAL ─────────────────────────────────────────────────────────

def render(cliente=None):
    st.markdown("## 💬 Consulta Livre aos Agentes")
    st.caption("Fale com qualquer agente — sem necessidade de cliente selecionado.")

    tab_livre, tab_site, tab_insta, tab_ads = st.tabs([
        "💬 Pergunta Livre",
        "🌐 Analisar Site",
        "📱 Analisar Instagram",
        "📊 Google Ads",
    ])

    with tab_livre:
        _render_livre()

    with tab_site:
        _render_site()

    with tab_insta:
        _render_instagram()

    with tab_ads:
        _render_google_ads()


# ─── ABA: PERGUNTA LIVRE ──────────────────────────────────────────────────────

def _render_livre():
    todos_keys = list(AGENTES.keys())
    todos_labels = [AGENTES[k]["label"] for k in todos_keys]
    label_para_key = {AGENTES[k]["label"]: k for k in todos_keys}

    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        sel_labels = st.multiselect(
            "Agentes:", options=todos_labels, default=todos_labels[:2], key="livre_agentes"
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Todos", key="livre_todos", use_container_width=True):
            st.session_state["livre_agentes"] = todos_labels
            st.rerun()

    agentes = [label_para_key[l] for l in sel_labels if l in label_para_key]

    pergunta = st.text_area(
        "Sua pergunta ou tarefa:",
        height=140,
        key="livre_pergunta",
        placeholder=(
            "Ex: Qual a melhor estratégia de Google Ads para desentupidora em SP com R$ 80/dia?\n"
            "Ex: Avalie esta copy: 'Desentupimento 24h • 45 min • Orçamento grátis'\n"
            "Ex: Como escalar uma conta que já tem CPA de R$ 45 mas está limitada por orçamento?"
        ),
    )

    if st.button("🚀 Consultar", type="primary", use_container_width=True, key="livre_btn"):
        if not agentes:
            st.error("Selecione pelo menos um agente.")
        elif not pergunta.strip():
            st.error("Digite uma pergunta.")
        else:
            _executar_e_exibir(agentes, pergunta, chave_resultado="livre_resultado")

    if "livre_resultado" in st.session_state:
        _exibir_resultado(st.session_state["livre_resultado"], chave="livre")


# ─── ABA: ANALISAR SITE ───────────────────────────────────────────────────────

def _render_site():
    todos_keys = list(AGENTES.keys())
    todos_labels = [AGENTES[k]["label"] for k in todos_keys]
    label_para_key = {AGENTES[k]["label"]: k for k in todos_keys}

    sel_labels = st.multiselect(
        "Agentes:", options=todos_labels,
        default=[AGENTES["ana"]["label"], AGENTES["lucas"]["label"]],
        key="site_agentes",
    )
    agentes = [label_para_key[l] for l in sel_labels if l in label_para_key]

    url = st.text_input("URL do site ou landing page:", placeholder="https://www.exemplo.com.br", key="site_url")
    pergunta_custom = st.text_area(
        "Pergunta específica (opcional):",
        placeholder="Ex: O que está faltando para aumentar a conversão?",
        height=70,
        key="site_pergunta",
    )

    if st.button("🔍 Analisar site", type="primary", use_container_width=True, key="site_btn"):
        if not agentes:
            st.error("Selecione pelo menos um agente.")
        elif not url.strip():
            st.error("Informe a URL.")
        else:
            with st.spinner(f"Buscando conteúdo de {url}..."):
                from agents.consulta import preparar_contexto_site
                conteudo = preparar_contexto_site(url)

            pergunta = pergunta_custom or (
                "Analise este site na sua área de especialidade. "
                "Identifique os principais problemas, oportunidades e dê recomendações concretas."
            )
            mensagem = f"TAREFA: {pergunta}\n\n{conteudo}"
            _executar_e_exibir(agentes, mensagem, chave_resultado="site_resultado",
                               label_pergunta=pergunta_custom or "Análise geral do site")

    if "site_resultado" in st.session_state:
        _exibir_resultado(st.session_state["site_resultado"], chave="site")


# ─── ABA: ANALISAR INSTAGRAM ─────────────────────────────────────────────────

def _render_instagram():
    todos_keys = list(AGENTES.keys())
    todos_labels = [AGENTES[k]["label"] for k in todos_keys]
    label_para_key = {AGENTES[k]["label"]: k for k in todos_keys}

    sel_labels = st.multiselect(
        "Agentes:", options=todos_labels,
        default=[AGENTES["social"]["label"]],
        key="insta_agentes",
    )
    agentes = [label_para_key[l] for l in sel_labels if l in label_para_key]

    col1, col2 = st.columns(2)
    handle = col1.text_input("Handle do Instagram:", placeholder="@empresa", key="insta_handle")
    segmento = col2.text_input("Segmento:", placeholder="desentupidora, gasista...", key="insta_seg")

    info = st.text_area(
        "Informações adicionais (seguidores, posts/semana, tipo de conteúdo...):",
        height=70,
        key="insta_info",
        placeholder="Ex: 850 seguidores, 2x semana, fotos de antes/depois, zona sul SP",
    )
    pergunta_custom = st.text_area(
        "Pergunta específica (opcional):",
        height=60,
        key="insta_pergunta",
        placeholder="Ex: Como aumentar engajamento? Qual conteúdo priorizar?",
    )

    if st.button("📱 Analisar Instagram", type="primary", use_container_width=True, key="insta_btn"):
        if not agentes:
            st.error("Selecione pelo menos um agente.")
        elif not handle.strip():
            st.error("Informe o handle do Instagram.")
        else:
            from agents.consulta import preparar_contexto_instagram
            ctx = preparar_contexto_instagram(handle, f"Segmento: {segmento}. {info}")
            pergunta = pergunta_custom or (
                "Analise a presença no Instagram desta empresa e dê seu parecer na sua especialidade."
            )
            mensagem = f"TAREFA: {pergunta}\n\n{ctx}"
            _executar_e_exibir(agentes, mensagem, chave_resultado="insta_resultado",
                               label_pergunta=handle)

    if "insta_resultado" in st.session_state:
        _exibir_resultado(st.session_state["insta_resultado"], chave="insta")


# ─── ABA: GOOGLE ADS ─────────────────────────────────────────────────────────

def _render_google_ads():
    from config.settings import GOOGLE_ADS_LOGIN_CUSTOMER_ID

    st.markdown("#### Contas / Campanhas para analisar")
    st.caption(
        "Adicione uma ou mais contas. Com múltiplas, Pedro fará análise comparativa. "
        "Você pode aplicar alterações com confirmação individual."
    )

    # ── Gerenciar lista de contas ─────────────────────────────────────────────
    if "ads_contas" not in st.session_state:
        st.session_state["ads_contas"] = [
            {"customer_id": GOOGLE_ADS_LOGIN_CUSTOMER_ID or "", "campaign_id": "", "label": "", "dias": 30}
        ]

    contas = st.session_state["ads_contas"]

    for i, conta in enumerate(contas):
        with st.container(border=True):
            col_label, col_remove = st.columns([4, 1])
            with col_label:
                label_txt = f"— {conta['label']}" if conta['label'] else ''
                st.markdown(f"**Conta {i + 1}** {label_txt}")
            with col_remove:
                if len(contas) > 1 and st.button("✕", key=f"rm_conta_{i}", use_container_width=True):
                    st.session_state["ads_contas"].pop(i)
                    st.rerun()

            col_cid, col_camp, col_lbl, col_dias = st.columns([2, 2, 2, 1])
            conta["customer_id"] = col_cid.text_input(
                "Customer ID", value=conta["customer_id"], key=f"cid_{i}",
                placeholder="8367385493",
            )
            conta["campaign_id"] = col_camp.text_input(
                "Campaign ID", value=conta["campaign_id"], key=f"camp_{i}",
                placeholder="12345678",
            )
            conta["label"] = col_lbl.text_input(
                "Rótulo (opcional)", value=conta["label"], key=f"lbl_{i}",
                placeholder="Ex: Cliente A",
            )
            conta["dias"] = col_dias.selectbox(
                "Período", [7, 14, 30], index=[7, 14, 30].index(conta["dias"]),
                key=f"dias_{i}",
            )

    if st.button("➕ Adicionar outra conta", key="add_conta"):
        st.session_state["ads_contas"].append(
            {"customer_id": "", "campaign_id": "", "label": "", "dias": 30}
        )
        st.rerun()

    st.divider()

    # ── Agentes e pergunta ────────────────────────────────────────────────────
    todos_keys = list(AGENTES.keys())
    label_para_key = {AGENTES[k]["label"]: k for k in todos_keys}

    col_ag, col_q = st.columns([1, 2])
    with col_ag:
        sel_labels = st.multiselect(
            "Agentes que analisam:",
            options=[AGENTES[k]["label"] for k in todos_keys],
            default=[AGENTES["pedro"]["label"], AGENTES["lucas"]["label"]],
            key="ads_agentes",
        )
    with col_q:
        pergunta_ads = st.text_area(
            "Pergunta específica (opcional):",
            height=88,
            key="ads_pergunta",
            placeholder=(
                "Ex: Onde está o maior desperdício de budget?\n"
                "Ex: Compare o CPA das duas contas e diga qual está mais eficiente\n"
                "Ex: Quais keywords devem ser pausadas imediatamente?"
            ),
        )

    modo_analise = st.radio(
        "Tipo de análise:",
        ["📋 Análise livre (texto)", "🎯 Análise estruturada com recomendações aplicáveis"],
        horizontal=True,
        key="ads_modo",
    )

    col_btn1, col_btn2 = st.columns(2)
    iniciar = col_btn1.button(
        "📊 Analisar agora",
        type="primary",
        use_container_width=True,
        key="ads_analisar",
    )
    limpar = col_btn2.button("🔄 Nova análise", use_container_width=True, key="ads_limpar")

    if limpar:
        for k in ["ads_resultado", "ads_dados_raw", "ads_recomendacoes"]:
            st.session_state.pop(k, None)
        st.rerun()

    if iniciar:
        agentes_keys = [label_para_key[l] for l in sel_labels if l in label_para_key]
        contas_validas = [c for c in contas if c["customer_id"].strip() and c["campaign_id"].strip()]

        if not contas_validas:
            st.error("Informe pelo menos uma conta com Customer ID e Campaign ID.")
        elif not agentes_keys:
            st.error("Selecione pelo menos um agente.")
        else:
            _executar_ads(contas_validas, agentes_keys, pergunta_ads, modo_analise)

    # ── Exibição dos resultados ───────────────────────────────────────────────
    if "ads_resultado" in st.session_state:
        _exibir_resultado_ads()


def _executar_ads(contas, agentes_keys, pergunta, modo):
    from agents.consulta import comparar_contas_ads, coletar_e_formatar_ads

    todas_dados = []
    contexto_ads = ""

    barra = st.progress(0.0, text="Iniciando coleta de dados...")

    try:
        if len(contas) == 1:
            conta = contas[0]
            dados, contexto_ads = coletar_e_formatar_ads(
                customer_id=conta["customer_id"],
                campaign_id=conta["campaign_id"],
                label=conta.get("label", ""),
                dias=conta.get("dias", 30),
                progress_cb=lambda p, l: barra.progress(p * 0.8, text=f"Coletando {l}..."),
            )
            todas_dados = [{"conta": conta, "dados": dados}]
        else:
            todas_dados, contexto_ads = comparar_contas_ads(
                contas,
                progress_cb=lambda p, l: barra.progress(p * 0.8, text=l),
            )
    except Exception as e:
        barra.empty()
        st.error(f"Erro ao coletar dados do Google Ads: {e}")
        return

    barra.progress(0.85, text="Analisando com IA...")

    st.session_state["ads_dados_raw"] = todas_dados

    if modo == "🎯 Análise estruturada com recomendações aplicáveis" and len(contas) == 1:
        # Usa expert_agent para análise estruturada (apenas para conta única)
        from agents.expert_agent import gerar_recomendacoes_json
        conta = contas[0]
        try:
            rec = gerar_recomendacoes_json(
                todas_dados[0]["dados"],
                conta.get("label") or conta["customer_id"],
                conta["campaign_id"],
            )
            st.session_state["ads_recomendacoes"] = {
                "rec": rec,
                "customer_id": conta["customer_id"],
            }
        except Exception as e:
            st.warning(f"Análise estruturada falhou: {e}. Usando análise livre.")

    # Análise livre pelos agentes selecionados
    pergunta_final = pergunta or (
        "Analise os dados do Google Ads abaixo na sua área de especialidade. "
        "Identifique os principais problemas, oportunidades e priorize as ações."
    )
    if len(contas) > 1:
        pergunta_final = (pergunta or "") + (
            "\n\nFaça uma análise COMPARATIVA das contas acima. "
            "Qual está mais eficiente? Onde está o maior desperdício? "
            "O que a conta melhor pode ensinar para a pior?"
        )

    mensagem = f"TAREFA: {pergunta_final}\n\n{contexto_ads}"
    resultados = []

    from agents.consulta import consultar_agentes
    try:
        resultados = consultar_agentes(
            agentes_keys,
            mensagem,
            callback=lambda k, l, t: barra.progress(0.9, text=f"✅ {l.split('—')[-1].strip()} respondeu"),
        )
    except Exception as e:
        barra.empty()
        st.error(f"Erro na consulta aos agentes: {e}")
        return

    barra.progress(1.0, text="Concluído!")
    barra.empty()

    st.session_state["ads_resultado"] = {
        "resultados": resultados,
        "pergunta": pergunta_final,
        "n_contas": len(contas),
    }
    st.rerun()


def _exibir_resultado_ads():
    dados = st.session_state.get("ads_resultado", {})
    resultados = dados.get("resultados", [])
    n_contas = dados.get("n_contas", 1)

    if not resultados:
        return

    st.divider()

    # ── Pareceres dos agentes ─────────────────────────────────────────────────
    if n_contas > 1:
        st.markdown("### 📊 Análise Comparativa")
    else:
        st.markdown("### 📊 Análise da Campanha")

    for r in resultados:
        _card(r["label"], r["cor"], r["texto"])

    # ── Recomendações estruturadas (conta única) ──────────────────────────────
    if "ads_recomendacoes" in st.session_state:
        _exibir_recomendacoes_estruturadas()

    # ── Export ────────────────────────────────────────────────────────────────
    st.divider()
    texto_exp = f"ANÁLISE GOOGLE ADS\n\n"
    for r in resultados:
        texto_exp += f"{r['label']}\n{'─'*40}\n{r['texto']}\n\n"
    st.download_button(
        "⬇️ Exportar análise (.txt)",
        data=texto_exp,
        file_name="analise_google_ads.txt",
        mime="text/plain",
        use_container_width=True,
    )


def _exibir_recomendacoes_estruturadas():
    from agents.expert_agent import aplicar_melhorias

    dados_rec = st.session_state["ads_recomendacoes"]
    rec = dados_rec["rec"]
    customer_id = dados_rec["customer_id"]

    if "erro" in rec:
        return

    st.divider()
    st.markdown("### 🎯 Recomendações Aplicáveis")

    # Score e resumo
    col_score, col_resumo = st.columns([1, 4])
    score = rec.get("score_campanha", 0)
    cor = "#2e7d32" if score >= 7 else "#f57c00" if score >= 4 else "#c62828"
    col_score.markdown(
        f"<div style='text-align:center;padding:12px;background:{cor};"
        f"border-radius:8px;color:white'>"
        f"<div style='font-size:32px;font-weight:900'>{score}/10</div>"
        f"<div style='font-size:11px'>Score</div></div>",
        unsafe_allow_html=True,
    )
    col_resumo.markdown(rec.get("resumo_executivo", ""))

    # Pontos críticos e positivos
    col_crit, col_pos = st.columns(2)
    with col_crit:
        st.markdown("**🔴 Pontos Críticos**")
        for p in rec.get("pontos_criticos", []):
            st.markdown(f"- {p}")
    with col_pos:
        st.markdown("**✅ Pontos Positivos**")
        for p in rec.get("pontos_positivos", []):
            st.markdown(f"- {p}")

    # Recomendações com checkboxes
    recomendacoes = rec.get("recomendacoes", [])
    if not recomendacoes:
        return

    st.markdown("---")
    st.markdown("#### Selecione as melhorias para aplicar")

    _COR_PRIO = {"CRITICO": "#c62828", "IMPORTANTE": "#f57c00", "MELHORIA": "#2e7d32"}
    _ICON_PRIO = {"CRITICO": "🔴", "IMPORTANTE": "🟡", "MELHORIA": "🟢"}

    selecionadas = []
    for rec_item in recomendacoes:
        acao = rec_item.get("acao", "informativo")
        aplicavel = acao and acao != "informativo"
        prio = rec_item.get("prioridade", "MELHORIA")
        cor_prio = _COR_PRIO.get(prio, "#666")
        icone = _ICON_PRIO.get(prio, "🟢")

        with st.container(border=True):
            col_check, col_info = st.columns([1, 10])
            with col_check:
                if aplicavel:
                    checked = st.checkbox("", key=f"rec_{rec_item['id']}", label_visibility="collapsed")
                    if checked:
                        selecionadas.append(rec_item)
                else:
                    st.markdown("ℹ️")
            with col_info:
                st.markdown(
                    f"<span style='font-size:12px;font-weight:700;color:{cor_prio}'>"
                    f"{icone} {prio}</span> &nbsp; **{rec_item.get('titulo', '')}**",
                    unsafe_allow_html=True,
                )
                st.caption(
                    f"Justificativa: {rec_item.get('justificativa', '')} &nbsp;|&nbsp; "
                    f"Impacto esperado: {rec_item.get('impacto_esperado', '')}"
                )
                if not aplicavel:
                    st.caption(f"ℹ️ Ação manual: {rec_item.get('acao', '')}")

    if selecionadas:
        st.markdown(f"**{len(selecionadas)} melhoria(s) selecionada(s)**")
        _exibir_preview_alteracoes(selecionadas)

        if st.button(
            f"✅ Aplicar {len(selecionadas)} melhoria(s) agora",
            type="primary",
            use_container_width=True,
            key="ads_aplicar",
        ):
            with st.spinner("Aplicando alterações na conta Google Ads..."):
                try:
                    resultados_mut = aplicar_melhorias(customer_id, selecionadas)
                    for r in resultados_mut:
                        if r["sucesso"]:
                            st.success(f"✅ {r['titulo']}")
                        else:
                            st.error(f"❌ {r['titulo']}: {r['resultado'].get('erro')}")
                except Exception as e:
                    st.error(f"Erro ao aplicar melhorias: {e}")


def _exibir_preview_alteracoes(selecionadas):
    """Mostra resumo das alterações antes de aplicar."""
    with st.expander("👁️ Prévia das alterações que serão feitas", expanded=True):
        for rec in selecionadas:
            acao = rec.get("acao", "")
            params = rec.get("parametros", {})
            prio = rec.get("prioridade", "")

            if acao == "atualizar_orcamento_campanha":
                st.markdown(
                    f"**{rec['titulo']}** — Novo orçamento: **R$ {params.get('novo_orcamento_brl', '?'):.2f}/dia**"
                )
            elif acao == "pausar_ativar_keyword":
                acao_txt = "⏸ Pausar" if params.get("pausar") else "▶ Ativar"
                st.markdown(
                    f"**{rec['titulo']}** — {acao_txt} keyword: `{params.get('keyword_texto', '?')}`"
                )
            elif acao == "adicionar_negativos_campanha":
                kws = params.get("keywords", [])
                st.markdown(
                    f"**{rec['titulo']}** — Negativar {len(kws)} termo(s): "
                    + ", ".join(f"`{k}`" for k in kws[:5])
                    + ("..." if len(kws) > 5 else "")
                )
            elif acao == "atualizar_lance_grupo":
                st.markdown(
                    f"**{rec['titulo']}** — Grupo `{params.get('ad_group_nome', '?')}`: "
                    f"CPC → **R$ {params.get('novo_cpc_brl', '?'):.2f}**"
                )
            else:
                st.markdown(f"**{rec['titulo']}** — {acao}")


# ─── EXECUÇÃO GENÉRICA (livre, site, instagram) ────────────────────────────────

def _executar_e_exibir(agentes_keys, mensagem, chave_resultado, label_pergunta=""):
    from agents.consulta import consultar_agentes

    resultados = []
    with st.status(f"Consultando {len(agentes_keys)} agente(s)...", expanded=True) as status:
        def on_resp(key, label, texto):
            nome = label.split("—")[-1].strip() if "—" in label else label
            status.write(f"✅ {nome} respondeu")
            resultados.append({"label": label, "cor": AGENTES[key]["cor"], "texto": texto})

        try:
            consultar_agentes(agentes_keys, mensagem, callback=on_resp)
            status.update(label="Concluído!", state="complete")
        except Exception as e:
            status.update(label=f"Erro: {e}", state="error")
            st.error(str(e))
            return

    st.session_state[chave_resultado] = {
        "resultados": resultados,
        "pergunta": label_pergunta or mensagem[:120],
    }
    st.rerun()


def _exibir_resultado(dados, chave):
    resultados = dados.get("resultados", [])
    if not resultados:
        return

    st.divider()
    with st.expander("Ver pergunta enviada", expanded=False):
        st.code(dados.get("pergunta", ""), language=None)

    for r in resultados:
        _card(r["label"], r["cor"], r["texto"])

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Nova consulta", key=f"nova_{chave}", use_container_width=True):
            st.session_state.pop(f"{chave}_resultado", None)
            st.rerun()
    with col2:
        texto = f"CONSULTA\n\nPERGUNTA:\n{dados.get('pergunta','')}\n\n{'─'*60}\n\n"
        texto += "\n\n".join(f"{r['label']}\n{'─'*40}\n{r['texto']}" for r in resultados)
        st.download_button(
            "⬇️ Exportar (.txt)",
            data=texto,
            file_name=f"consulta_{chave}.txt",
            mime="text/plain",
            key=f"dl_{chave}",
            use_container_width=True,
        )
