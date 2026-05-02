"""Landing Pages — análise de URL e geração de LP."""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.landing_agent import analisar_landing_page, gerar_landing_page_html, melhorar_html_para_wordpress

_NOTA_CORES = {"A": "#2E7D32", "B": "#558B2F", "C": "#F57F17", "D": "#E65100", "F": "#C62828"}
_DIM_LABELS = {
    "keywords":           "🔍 Keywords",
    "cta":                "📞 CTA",
    "trust_elements":     "🛡️ Confiança",
    "mobile_readiness":   "📱 Mobile",
    "velocidade_percebida": "⚡ Velocidade",
    "estrutura_persuasiva": "🧠 Persuasão",
}


_WP_STATE_KEY = "wp_conn"


def _wp_conn() -> dict:
    return st.session_state.get(_WP_STATE_KEY, {})


def _render_wordpress_tab(cliente):
    from tools.wordpress_api import (
        testar_conexao, listar_paginas, obter_pagina,
        atualizar_conteudo_html, injetar_html_elementor, snippet_elementor_rest,
    )

    st.caption(
        "Conecte ao WordPress do cliente, selecione a página e aplique as melhorias "
        "diretamente pelo painel — sem precisar acessar o wp-admin."
    )

    # ── Conexão ────────────────────────────────────────────────────────────────
    with st.expander("🔑 Conexão WordPress", expanded=not _wp_conn().get("ok")):
        st.markdown(
            "Use uma **Senha de Aplicação** (WordPress → Usuário → Senhas de Aplicação). "
            "O usuário precisa ter permissão de **Editor** ou superior."
        )
        col1, col2 = st.columns([2, 1])
        wp_url = col1.text_input(
            "URL do WordPress",
            value=_wp_conn().get("url", getattr(cliente, "site_url", "") or ""),
            placeholder="https://www.exemplo.com.br",
            key="wp_url",
        )
        col_u, col_p = st.columns(2)
        wp_user = col_u.text_input("Usuário", value=_wp_conn().get("user", ""), key="wp_user")
        wp_pass = col_p.text_input("Senha de Aplicação", type="password", key="wp_pass")

        if st.button("🔌 Conectar", type="primary"):
            if not wp_url or not wp_user or not wp_pass:
                st.error("Preencha URL, usuário e senha.")
            else:
                with st.spinner("Verificando credenciais..."):
                    result = testar_conexao(wp_url, wp_user, wp_pass)
                if result["ok"]:
                    st.session_state[_WP_STATE_KEY] = {
                        "ok": True, "url": wp_url,
                        "user": wp_user, "pass": wp_pass,
                        "usuario_nome": result["usuario"],
                    }
                    st.rerun()
                else:
                    st.error(f"Falha na conexão: {result['erro']}")

    conn = _wp_conn()
    if not conn.get("ok"):
        return

    st.success(f"✅ Conectado como **{conn['usuario_nome']}** em `{conn['url']}`")

    # ── Listar páginas ─────────────────────────────────────────────────────────
    @st.cache_data(ttl=60, show_spinner=False)
    def _paginas(url, user, pwd):
        return listar_paginas(url, user, pwd)

    try:
        with st.spinner("Carregando páginas..."):
            paginas = _paginas(conn["url"], conn["user"], conn["pass"])
    except Exception as e:
        st.error(f"Erro ao listar páginas: {e}")
        return

    if not paginas:
        st.warning("Nenhuma página encontrada.")
        return

    status_icone = {"publish": "🟢", "draft": "⚫", "private": "🔒"}
    pag_opts = {
        f"{status_icone.get(p['status'], '⚪')} {p['titulo']} (ID {p['id']}) — {p['modificada']}": p
        for p in paginas
    }

    sel_label = st.selectbox("Selecione a página", list(pag_opts.keys()), key="wp_pag_sel")
    pagina_sel = pag_opts[sel_label]

    col_btn1, col_btn2, col_btn3 = st.columns(3)
    analisar = col_btn1.button("🔍 Analisar esta página", type="primary", use_container_width=True)
    col_btn2.link_button("🔗 Abrir no site", pagina_sel["url"], use_container_width=True)
    if col_btn3.button("🔄 Recarregar lista", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if analisar:
        with st.spinner(f"Buscando e analisando {pagina_sel['url']}..."):
            resultado = analisar_landing_page(pagina_sel["url"])
        st.session_state["wp_analise"] = resultado
        st.session_state["wp_pagina_id"] = pagina_sel["id"]
        st.session_state["wp_pagina_url"] = pagina_sel["url"]
        st.session_state["wp_pagina_usa_elementor"] = None  # será resolvido ao aplicar

    # ── Resultado da análise ───────────────────────────────────────────────────
    if "wp_analise" not in st.session_state:
        return

    r = st.session_state["wp_analise"]
    if "erro" in r:
        st.error(f"Erro na análise: {r['erro']}")
        return

    st.divider()
    st.subheader("📊 Resultado da análise")

    col_nota, col_score = st.columns([1, 3])
    nota = r.get("nota_geral", "?")
    score = r.get("score_percentual", 0)
    cor_nota = _NOTA_CORES.get(nota, "#888")
    col_nota.markdown(
        f"<div style='text-align:center'>{_nota_badge(nota)}"
        f"<div style='font-size:11px;color:#888;margin-top:4px'>Nota geral</div></div>",
        unsafe_allow_html=True,
    )
    col_score.progress(score / 100, text=f"Score: {score}/100")

    col_p, col_r = st.columns(2)
    with col_p:
        st.markdown("#### 🔴 Problemas críticos")
        for p in r.get("problemas_criticos", []):
            st.markdown(f"• {p}")
    with col_r:
        st.markdown("#### ✅ Recomendações")
        for rec in r.get("recomendacoes_priorizadas", []):
            st.markdown(f"• {rec}")

    try:
        from tools.pdf_exporter import gerar_pdf_relatorio_agente
        linhas = [
            f"# Análise de Landing Page\n\n**Score:** {r.get('score_percentual', 0)}/100  |  **Nota:** {r.get('nota_geral', '?')}\n\n{r.get('resumo_executivo', '')}",
            "## Problemas Críticos\n" + "\n".join(f"- {p}" for p in r.get("problemas_criticos", [])),
            "## Recomendações\n" + "\n".join(f"- {rec}" for rec in r.get("recomendacoes_priorizadas", [])),
        ]
        for bloco in r.get("analise_detalhada", []):
            titulo = bloco.get("elemento", bloco.get("titulo", ""))
            linhas.append(f"## {titulo}\n{bloco.get('analise', bloco.get('descricao', ''))}")
        conteudo_md = "\n\n".join(linhas)
        pdf_bytes = gerar_pdf_relatorio_agente("Análise de Landing Page", conteudo_md, cliente.nome)
        st.download_button(
            "📄 Exportar PDF",
            data=pdf_bytes,
            file_name=f"lp_{cliente.nome.lower().replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary",
        )
    except Exception:
        pass

    # ── Gerar HTML melhorado ───────────────────────────────────────────────────
    st.divider()
    st.subheader("🛠️ Gerar versão melhorada")

    if score >= 80:
        st.info("Página com boa pontuação. Ainda é possível gerar uma versão otimizada.")

    if st.button("⚡ Gerar HTML melhorado com IA", type="primary", use_container_width=True):
        problemas = r.get("problemas_criticos", [])
        recomendacoes = r.get("recomendacoes_priorizadas", [])
        with st.spinner("Gerando HTML melhorado — pode levar alguns segundos..."):
            from tools.html_fetcher import fetch_html
            html_atual_result = fetch_html(st.session_state.get("wp_pagina_url", ""))
            html_atual = html_atual_result.get("html", "")
            html_novo = melhorar_html_para_wordpress(
                html_atual=html_atual,
                problemas=problemas,
                recomendacoes=recomendacoes,
                nome_empresa=cliente.nome,
            )
        st.session_state["wp_html_novo"] = html_novo
        st.success(f"HTML gerado: {len(html_novo):,} caracteres")

    if "wp_html_novo" not in st.session_state:
        return

    html_novo = st.session_state["wp_html_novo"]

    st.subheader("👁️ Preview do HTML melhorado")
    st.components.v1.html(html_novo, height=500, scrolling=True)

    st.download_button(
        "⬇️ Baixar HTML melhorado",
        data=html_novo.encode("utf-8"),
        file_name=f"lp_melhorada_{pagina_sel['id']}.html",
        mime="text/html",
    )

    # ── Publicar no WordPress ──────────────────────────────────────────────────
    st.divider()
    st.subheader("🚀 Publicar no WordPress")

    metodo = st.radio(
        "Como deseja aplicar a melhoria?",
        options=["classic", "elementor"],
        format_func=lambda x: (
            "📝 Substituir conteúdo (editor clássico)" if x == "classic"
            else "🎨 Injetar via Elementor (HTML Widget)"
        ),
        horizontal=True,
        key="wp_metodo",
    )

    if metodo == "elementor":
        with st.expander("ℹ️ Requisito para modo Elementor", expanded=False):
            st.markdown(
                "Para que o UnboundSales possa escrever diretamente no Elementor, "
                "adicione o snippet abaixo no `functions.php` do seu tema filho "
                "ou num plugin personalizado:"
            )
            st.code(snippet_elementor_rest(), language="php")

    confirmar = st.checkbox(
        "⚠️ Confirmo que desejo substituir o conteúdo atual desta página no WordPress",
        key="wp_confirmar",
    )

    if st.button(
        "✅ Publicar agora",
        type="primary",
        disabled=not confirmar,
        use_container_width=True,
    ):
        page_id = st.session_state.get("wp_pagina_id")
        with st.spinner("Publicando no WordPress..."):
            if metodo == "elementor":
                res = injetar_html_elementor(conn["url"], conn["user"], conn["pass"],
                                              page_id, html_novo)
            else:
                res = atualizar_conteudo_html(conn["url"], conn["user"], conn["pass"],
                                              page_id, html_novo)

        if res.get("sucesso"):
            link = res.get("link", pagina_sel["url"])
            st.success(f"✅ Página atualizada com sucesso! [Ver página]({link})")
            st.session_state.pop("wp_html_novo", None)
        else:
            st.error(f"Erro ao publicar: {res.get('erro', 'desconhecido')}")


def _nota_badge(nota: str) -> str:
    cor = _NOTA_CORES.get(nota, "#888")
    return (
        f"<span style='background:{cor};color:white;font-size:18px;font-weight:900;"
        f"padding:4px 12px;border-radius:6px'>{nota}</span>"
    )


def render(cliente):
    st.header("🌐 Landing Pages")

    tab_analise, tab_criar, tab_wp = st.tabs([
        "🔍 Analisar URL existente",
        "🛠️ Gerar nova Landing Page",
        "🔧 Editar no WordPress",
    ])

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

    # ── TAB 3: Editar no WordPress ─────────────────────────────────────────────
    with tab_wp:
        _render_wordpress_tab(cliente)
