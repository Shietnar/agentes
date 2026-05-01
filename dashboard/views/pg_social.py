"""
Dashboard — Mídias Sociais
Análise de Instagram com dados manuais ou via API.
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def render(cliente):
    st.title("📱 Mídias Sociais")
    st.caption(f"Análise de presença digital — {cliente.nome}")

    # ─── TABS ─────────────────────────────────────────────────────────────────
    tab_analise, tab_api, tab_tiktok, tab_publicar = st.tabs([
        "📊 Análise de Conta",
        "🔗 Conectar Instagram",
        "🎵 Conectar TikTok",
        "📤 Publicar Conteúdo",
    ])

    # ─── ABA: ANÁLISE ─────────────────────────────────────────────────────────
    with tab_analise:
        _render_analise(cliente)

    # ─── ABA: CONECTAR INSTAGRAM ──────────────────────────────────────────────
    with tab_api:
        _render_conexao_api(cliente)

    # ─── ABA: CONECTAR TIKTOK ─────────────────────────────────────────────────
    with tab_tiktok:
        _render_conexao_tiktok()

    # ─── ABA: PUBLICAR ────────────────────────────────────────────────────────
    with tab_publicar:
        _render_publicar(cliente)


# ─── ANÁLISE ─────────────────────────────────────────────────────────────────

def _render_analise(cliente):
    st.subheader("Análise de Conta Instagram")

    # Determinar modo (API ou manual)
    from config.settings import INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID
    tem_api = bool(INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID)

    modo = st.radio(
        "Modo de análise:",
        ["Dados manuais (sem API)", "API Instagram (com token)"],
        index=1 if tem_api else 0,
        horizontal=True,
    )

    if modo == "Dados manuais (sem API)":
        _render_analise_manual(cliente)
    else:
        _render_analise_api(cliente)


def _render_analise_manual(cliente):
    with st.form("form_social_manual"):
        col1, col2 = st.columns(2)
        username = col1.text_input("Username do Instagram", placeholder="@seucliente")
        seguidores = col2.number_input("Nº de seguidores", min_value=0, value=1000)

        col3, col4 = st.columns(2)
        posts_semana = col3.number_input("Posts por semana", min_value=0, max_value=30, value=3)
        taxa_eng = col4.number_input("Taxa de engajamento estimada (%)", min_value=0.0, max_value=100.0, value=2.5, step=0.1)

        tipo_conteudo = st.text_input(
            "Tipo de conteúdo predominante",
            placeholder="Ex: fotos de serviços, antes/depois, dicas",
        )
        briefing = st.text_area(
            "Informações adicionais do cliente",
            value=cliente.segmento + " em " + (cliente.cidade or ""),
            height=80,
        )

        if st.form_submit_button("🔍 Analisar", type="primary", use_container_width=True):
            if not username:
                st.error("Informe o username do Instagram.")
                return

            with st.spinner("Analisando conta com IA..."):
                try:
                    from agents.social_agent import analisar_sem_api
                    resultado = analisar_sem_api(
                        segmento=cliente.segmento,
                        cidade=cliente.cidade or "",
                        username=username.lstrip("@"),
                        seguidores=seguidores,
                        posts_por_semana=posts_semana,
                        tipo_conteudo=tipo_conteudo or "Geral",
                        taxa_engajamento=taxa_eng,
                        briefing=briefing,
                    )
                    st.session_state["social_resultado"] = resultado
                except Exception as e:
                    st.error(f"Erro na análise: {e}")
                    return

    if "social_resultado" in st.session_state:
        _exibir_resultado(st.session_state["social_resultado"])


def _render_analise_api(cliente):
    from config.settings import INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID

    st.info("Usando credenciais do `.env` (INSTAGRAM_ACCESS_TOKEN / INSTAGRAM_ACCOUNT_ID).")

    account_id_custom = st.text_input(
        "Account ID (deixe em branco para usar o do .env)",
        placeholder=INSTAGRAM_ACCOUNT_ID or "ex: 17841400000000000",
    )

    if st.button("🔍 Buscar dados e analisar", type="primary", use_container_width=True):
        account_id = account_id_custom or INSTAGRAM_ACCOUNT_ID
        if not account_id:
            st.error("INSTAGRAM_ACCOUNT_ID não configurado no .env.")
            return

        with st.spinner("Coletando dados do Instagram..."):
            try:
                from tools.instagram_api import coletar_dados_completos
                dados = coletar_dados_completos(account_id, INSTAGRAM_ACCESS_TOKEN)
            except Exception as e:
                st.error(f"Erro ao buscar dados da API: {e}")
                return

        with st.spinner("Analisando com IA..."):
            try:
                from agents.social_agent import analisar_instagram
                resultado = analisar_instagram(
                    segmento=cliente.segmento,
                    cidade=cliente.cidade or "",
                    dados_instagram=dados,
                    briefing="",
                )
                st.session_state["social_resultado"] = resultado
            except Exception as e:
                st.error(f"Erro na análise: {e}")

    if "social_resultado" in st.session_state:
        _exibir_resultado(st.session_state["social_resultado"])


def _exibir_resultado(r: dict):
    if "erro" in r:
        st.error(r["erro"])
        return

    # Score e resumo
    st.divider()
    col1, col2 = st.columns([1, 3])
    score = r.get("score_geral", 0)
    cor_score = "#2e7d32" if score >= 70 else "#f57c00" if score >= 40 else "#c62828"
    col1.markdown(
        f"<div style='text-align:center;padding:16px;background:{cor_score};"
        f"border-radius:12px;color:white'>"
        f"<div style='font-size:40px;font-weight:900'>{score}</div>"
        f"<div style='font-size:12px'>Score Geral</div></div>",
        unsafe_allow_html=True,
    )
    col2.markdown(f"### Resumo Executivo\n{r.get('resumo_executivo', '')}")

    st.divider()

    # Saúde do perfil
    with st.expander("📋 Saúde do Perfil", expanded=True):
        saude = r.get("saude_perfil", {})
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**✅ Pontos Fortes**")
            for p in saude.get("pontos_fortes", []):
                st.markdown(f"- {p}")
        with col_b:
            st.markdown("**⚠️ Pontos a Melhorar**")
            for p in saude.get("pontos_fracos", []):
                st.markdown(f"- {p}")
        st.caption(
            f"Engajamento atual: **{saude.get('taxa_engajamento_atual', '?')}** | "
            f"Benchmark do segmento: **{saude.get('benchmark_segmento', '?')}**"
        )

    # Análise de conteúdo
    with st.expander("🎯 Análise de Conteúdo"):
        conteudo = r.get("analise_conteudo", {})
        col_x, col_y = st.columns(2)
        with col_x:
            st.metric("Formato mais eficaz", conteudo.get("formato_mais_eficaz", "?"))
            st.metric("Melhor horário", conteudo.get("melhor_horario", "?"))
        with col_y:
            st.metric("Frequência atual", conteudo.get("frequencia_atual", "?"))
            st.metric("Frequência recomendada", conteudo.get("frequencia_recomendada", "?"))

        col_e, col_f = st.columns(2)
        with col_e:
            st.markdown("**📈 Temas que engajam:**")
            for t in conteudo.get("temas_que_engajam", []):
                st.markdown(f"- {t}")
        with col_f:
            st.markdown("**📉 Temas que não engajam:**")
            for t in conteudo.get("temas_que_nao_engajam", []):
                st.markdown(f"- {t}")

    # Oportunidades
    with st.expander("🚀 Oportunidades"):
        for op in r.get("oportunidades", []):
            st.markdown(f"**{op.get('titulo', '')}**")
            st.caption(f"Impacto: {op.get('impacto', '')} | {op.get('descricao', '')}")
            st.divider()

    # Plano de ação
    with st.expander("📅 Plano de Ação", expanded=True):
        plano = r.get("plano_acao", {})
        tab_sem, tab_mes, tab_cal = st.tabs(["Esta Semana", "Este Mês", "Calendário Semanal"])

        with tab_sem:
            for a in plano.get("esta_semana", []):
                st.markdown(f"- {a}")

        with tab_mes:
            for a in plano.get("este_mes", []):
                st.markdown(f"- {a}")

        with tab_cal:
            cal = plano.get("calendario_semanal", {})
            dias = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]
            nomes = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
            for d, n in zip(dias, nomes):
                if d in cal:
                    st.markdown(f"**{n}:** {cal[d]}")

    # Hashtags
    hashtags = r.get("hashtags_recomendadas", [])
    if hashtags:
        st.markdown("**🏷️ Hashtags Recomendadas:**")
        st.code(" ".join(hashtags))


# ─── CONEXÃO API ─────────────────────────────────────────────────────────────

def _render_conexao_tiktok():
    st.subheader("Conectar TikTok Content Posting API")
    st.markdown("""
### Pré-requisito
Conta TikTok pessoal ou de criador (com pelo menos 1 post publicado).

---

### Passo a passo

**1. Criar conta de desenvolvedor**
1. Acesse **developers.tiktok.com** e faça login com sua conta TikTok
2. Clique em **Manage Apps** → **Connect new app**

**2. Configurar o App**
- App name: `UnboundSales`
- App type: **Web**
- Category: **Business/Utility**

**3. Ativar permissões (Scopes)**

Em **Products** → adicione **Login Kit** e **Content Posting API**:
- `user.info.basic`
- `video.publish`
- `video.upload`

**4. Testar em Sandbox**
- Por padrão o app fica em modo Sandbox (publica apenas para si mesmo como SELF_ONLY)
- Adicione sua conta TikTok em **Testers** para poder testar
- Solicite revisão para produção depois de validar

**5. Obter Access Token (OAuth 2.0)**

```
1. Acesse a URL de autorização:
   https://www.tiktok.com/v2/auth/authorize/
   ?client_key=SEU_CLIENT_KEY
   &scope=user.info.basic,video.publish,video.upload
   &response_type=code
   &redirect_uri=http://localhost:8080/callback
   &state=random_string

2. Após autorização, você recebe um 'code' na URL de retorno

3. Troque o code pelo access_token:
   POST https://open.tiktokapis.com/v2/oauth/token/
   {
     "client_key": "SEU_CLIENT_KEY",
     "client_secret": "SEU_CLIENT_SECRET",
     "code": "CODE_RECEBIDO",
     "grant_type": "authorization_code",
     "redirect_uri": "http://localhost:8080/callback"
   }
```

**6. Adicionar ao .env**
```env
TIKTOK_ACCESS_TOKEN=seu_token_aqui
```

---
    """)

    from config.settings import TIKTOK_ACCESS_TOKEN
    if st.button("🔌 Testar conexão TikTok"):
        if not TIKTOK_ACCESS_TOKEN:
            st.error("TIKTOK_ACCESS_TOKEN não configurado no .env")
        else:
            try:
                from tools.tiktok_api import obter_usuario_info
                user = obter_usuario_info()
                st.success(f"✅ Conectado! Usuário: {user.get('display_name')} — {user.get('follower_count', 0):,} seguidores")
            except Exception as e:
                st.error(f"Falha na conexão: {e}")


def _render_conexao_api(cliente):
    st.subheader("Conectar Instagram Graph API")
    st.markdown("""
### Como configurar (passo a passo)

**Pré-requisitos:** Conta Instagram Business conectada a uma Página do Facebook.

---

**1. Criar App no Meta for Developers**

1. Acesse [developers.facebook.com](https://developers.facebook.com) → **Meus Apps** → **Criar App**
2. Tipo de App: **Business** (não "Consumer")
3. Nome: `UnboundSales` (ou nome da sua agência)
4. Email de contato: seu email

**2. Adicionar produto: Instagram Graph API**

1. No painel do app → **Adicionar Produtos** → **Instagram** → **Configurar**
2. Vá em **Instagram > Basic Display** e depois em **Instagram > API with Instagram Login**

**3. Gerar Token de Acesso de Longa Duração**

```
Tipo de token necessário: System User Token (via Business Manager)
Permissões: instagram_basic, instagram_content_publish,
            pages_read_engagement, pages_show_list,
            business_management
```

1. Acesse [business.facebook.com](https://business.facebook.com) → Configurações → **Usuários do sistema**
2. Crie um usuário do sistema (Admin)
3. Clique em **Gerar novo token** → selecione seu App → marque as permissões acima
4. Copie o token gerado (é de longa duração, ~60 dias ou nunca expira para System Users)

**4. Obter o Instagram Account ID**

1. Acesse o Explorador de API do Graph: [developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer)
2. Selecione seu app e gere um token de acesso do usuário
3. Faça a query: `GET /me/accounts` → copie o `id` da sua Página do Facebook
4. Depois: `GET /{page-id}?fields=instagram_business_account` → copie o `id` (esse é o INSTAGRAM_ACCOUNT_ID)

**5. Adicionar ao .env**

```env
INSTAGRAM_ACCESS_TOKEN=seu_token_aqui
INSTAGRAM_ACCOUNT_ID=17841400000000000
```

---
    """)

    # Teste de conexão
    st.subheader("Testar Conexão")
    test_token = st.text_input("Token de teste (ou deixe em branco para usar o do .env)", type="password")
    test_account = st.text_input("Account ID de teste")

    if st.button("🔌 Testar conexão"):
        from config.settings import INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID
        token = test_token or INSTAGRAM_ACCESS_TOKEN
        account = test_account or INSTAGRAM_ACCOUNT_ID

        if not token or not account:
            st.error("Configure o token e o account ID.")
        else:
            try:
                from tools.instagram_api import obter_perfil
                perfil = obter_perfil(account, token)
                st.success(f"✅ Conectado com sucesso! Conta: @{perfil.get('username')} — {perfil.get('followers_count', 0):,} seguidores")
            except Exception as e:
                st.error(f"Falha na conexão: {e}")


# ─── PUBLICAR ────────────────────────────────────────────────────────────────

def _render_publicar(cliente):
    st.subheader("Publicar no Instagram")

    from config.settings import INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID
    if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_ACCOUNT_ID:
        st.warning("Configure INSTAGRAM_ACCESS_TOKEN e INSTAGRAM_ACCOUNT_ID no .env para publicar.")

    st.markdown("Use a aba **Designer** para gerar imagens e publique aqui.")

    with st.form("form_publicar_instagram"):
        image_url = st.text_input(
            "URL pública da imagem",
            placeholder="https://exemplo.com/imagem.jpg",
            help="A imagem precisa estar em uma URL pública acessível pelo Instagram.",
        )
        legenda = st.text_area(
            "Legenda do post",
            placeholder="Escreva a legenda aqui...\n\n#hashtag1 #hashtag2",
            height=150,
        )
        tipo = st.radio("Tipo de publicação:", ["Feed", "Story"], horizontal=True)

        if st.form_submit_button("📤 Publicar agora", type="primary", use_container_width=True):
            if not image_url or not legenda:
                st.error("URL da imagem e legenda são obrigatórios.")
            elif not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_ACCOUNT_ID:
                st.error("Token e Account ID do Instagram não configurados.")
            else:
                with st.spinner("Publicando..."):
                    try:
                        if tipo == "Feed":
                            from tools.instagram_api import publicar_imagem
                            resultado = publicar_imagem(image_url, legenda)
                        else:
                            from tools.instagram_api import publicar_story
                            resultado = publicar_story(image_url)
                        st.success(f"✅ Publicado com sucesso! ID: {resultado.get('id')}")
                    except Exception as e:
                        st.error(f"Erro ao publicar: {e}")
