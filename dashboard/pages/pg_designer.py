"""
Dashboard — Designer de Conteúdo
Geração de imagens com IA para posts, stories, banners e landing pages.
"""
import streamlit as st
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def render(cliente):
    st.title("🎨 Designer de Conteúdo")
    st.caption(f"Criação de imagens com IA — {cliente.nome}")

    tab_gerar, tab_galeria, tab_guia = st.tabs([
        "✨ Gerar Imagem",
        "🖼️ Galeria",
        "📖 Como usar",
    ])

    with tab_gerar:
        _render_gerar(cliente)

    with tab_galeria:
        _render_galeria(cliente)

    with tab_guia:
        _render_guia()


# ─── GERAR IMAGEM ─────────────────────────────────────────────────────────────

def _render_gerar(cliente):
    from agents.designer_agent import FORMATOS

    st.subheader("Criar nova imagem")

    col1, col2 = st.columns([2, 1])

    with col1:
        descricao = st.text_area(
            "O que você quer criar?",
            placeholder=(
                "Ex: Foto de técnico de desentupimento chegando na casa do cliente "
                "com van da empresa, uniforme profissional, bairro residencial de São Paulo"
            ),
            height=120,
        )
        legenda_sugerida = st.text_area(
            "Legenda do post (opcional — deixe em branco para sugestão automática)",
            height=80,
        )

    with col2:
        formato = st.selectbox(
            "Formato",
            options=list(FORMATOS.keys()),
            format_func=lambda k: FORMATOS[k]["descricao"],
        )
        provider = st.selectbox(
            "Gerador de imagem",
            options=["openai", "gemini"],
            format_func=lambda p: "OpenAI gpt-image-2" if p == "openai" else "Google Gemini",
        )
        estilo = st.selectbox(
            "Estilo",
            options=[
                "Foto realista profissional",
                "Ilustração digital clean",
                "Arte flat design",
                "Foto estilo editorial",
                "Dark mode / fundo escuro",
            ],
        )

    with st.expander("⚙️ Configurações avançadas"):
        qualidade = st.radio("Qualidade (OpenAI)", ["standard", "hd"], horizontal=True)
        briefing_extra = st.text_input(
            "Informações extras para o prompt",
            placeholder="Ex: usar cores azul e branco, incluir nome da empresa no fundo",
        )

    if st.button("🎨 Gerar imagem", type="primary", use_container_width=True):
        if not descricao:
            st.error("Descreva o que você quer criar.")
            return

        with st.spinner(f"Criando prompt visual... ({provider.upper()})"):
            try:
                from agents.designer_agent import gerar_post
                resultado = gerar_post(
                    descricao=descricao + (f". {briefing_extra}" if briefing_extra else ""),
                    segmento=cliente.segmento,
                    cidade=cliente.cidade or "",
                    formato=formato,
                    provider=provider,
                    nome_arquivo=f"{cliente.nome.replace(' ', '_')}_{formato}",
                    estilo=estilo,
                )
                st.session_state["designer_resultado"] = resultado
                st.session_state["designer_legenda_usuario"] = legenda_sugerida
            except Exception as e:
                st.error(f"Erro na geração: {e}")
                return

    if "designer_resultado" in st.session_state:
        _exibir_resultado(st.session_state["designer_resultado"],
                          st.session_state.get("designer_legenda_usuario", ""))


def _exibir_resultado(resultado: dict, legenda_usuario: str):
    st.divider()
    st.subheader("✅ Imagem gerada")

    caminho = Path(resultado["caminho"])
    if caminho.exists():
        col_img, col_info = st.columns([1, 1])
        with col_img:
            st.image(str(caminho), use_container_width=True)
            with open(caminho, "rb") as f:
                st.download_button(
                    "⬇️ Baixar imagem",
                    f,
                    file_name=caminho.name,
                    mime="image/png",
                    use_container_width=True,
                )

        with col_info:
            st.markdown("**📝 Legenda sugerida:**")
            legenda_final = legenda_usuario or resultado.get("sugestao_legenda", "")
            legenda_editavel = st.text_area("", value=legenda_final, height=120, key="leg_edit")

            hashtags = resultado.get("hashtags", [])
            if hashtags:
                st.markdown("**🏷️ Hashtags:**")
                st.code(" ".join(hashtags))

            st.markdown("**🤖 Prompt usado:**")
            st.caption(resultado.get("prompt_usado", ""))

            if resultado.get("justificativa"):
                with st.expander("Por que essas escolhas visuais?"):
                    st.write(resultado["justificativa"])

        # Publicar diretamente
        st.divider()
        st.markdown("**📤 Publicar esta imagem**")
        col_pub1, col_pub2 = st.columns(2)

        with col_pub1:
            image_url_pub = st.text_input(
                "URL pública da imagem (hospedar antes de publicar)",
                key="pub_url",
                help="O Instagram exige URL pública. Hospede a imagem em imgbb.com ou similar.",
            )

        with col_pub2:
            from config.settings import INSTAGRAM_ACCESS_TOKEN
            if INSTAGRAM_ACCESS_TOKEN:
                if st.button("📸 Publicar no Instagram Feed", use_container_width=True):
                    if not image_url_pub:
                        st.error("Informe a URL pública da imagem.")
                    else:
                        with st.spinner("Publicando..."):
                            try:
                                from tools.instagram_api import publicar_imagem
                                res = publicar_imagem(image_url_pub, legenda_editavel)
                                st.success(f"✅ Publicado! ID: {res.get('id')}")
                            except Exception as e:
                                st.error(f"Erro: {e}")
            else:
                st.info("Configure INSTAGRAM_ACCESS_TOKEN no .env para publicar.")
    else:
        st.error(f"Arquivo de imagem não encontrado: {caminho}")


# ─── GALERIA ─────────────────────────────────────────────────────────────────

def _render_galeria(cliente):
    st.subheader("Imagens geradas")

    from tools.image_generation import OUTPUT_DIR
    imagens = sorted(OUTPUT_DIR.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not imagens:
        st.info("Nenhuma imagem gerada ainda. Use a aba **Gerar Imagem** para criar.")
        return

    st.caption(f"{len(imagens)} imagem(ns) em {OUTPUT_DIR}")

    cols = st.columns(3)
    for i, img in enumerate(imagens[:12]):
        with cols[i % 3]:
            st.image(str(img), caption=img.stem, use_container_width=True)
            with open(img, "rb") as f:
                st.download_button(
                    "⬇️",
                    f,
                    file_name=img.name,
                    mime="image/png",
                    key=f"dl_{img.stem}",
                    use_container_width=True,
                )


# ─── GUIA ────────────────────────────────────────────────────────────────────

def _render_guia():
    st.subheader("Como usar o Designer de Conteúdo")
    st.markdown("""
### Fluxo de trabalho

1. **Descreva** o que você quer criar em linguagem natural (português)
2. **Escolha o formato** (feed, story, banner etc.)
3. **Selecione o gerador** (OpenAI ou Gemini)
4. O Claude cria um **prompt visual otimizado** em inglês automaticamente
5. A IA gera a imagem + sugere legenda e hashtags
6. Edite a legenda, baixe a imagem ou publique direto no Instagram

---

### Formatos disponíveis

| Formato | Dimensão | Uso ideal |
|---|---|---|
| Instagram Feed (quadrado) | 1:1 | Posts no grid do perfil |
| Instagram Story / TikTok | 9:16 | Stories e vídeos verticais |
| Instagram Retrato | 4:5 | Fotos que ocupam mais espaço no feed |
| Banner / Capa | 16:9 | Capas de Facebook, YouTube, anúncios |

---

### Dicas de prompt

✅ **Bom prompt:**
> "Foto de técnico uniformizado de desentupimento usando mangueira de alta pressão em cano externo de residência, uniforme azul escuro com logo, ambiente externo, dia ensolarado, São Paulo"

❌ **Prompt fraco:**
> "foto de serviço"

---

### Geradores disponíveis

**OpenAI gpt-image-2**
- Melhor para: fotos realistas, retratos, ambientes
- Qualidade "hd": mais detalhes, custo maior
- Tamanhos: 1:1, 9:16, 16:9

**Google Gemini gemini-3.1-flash-image-preview**
- Melhor para: ilustrações, artes digitais, composições criativas
- Mais rápido que OpenAI
- Bom para conceitos mais abstratos

---

### Configurar credenciais

```env
# .env
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AIzaSy...
```
    """)
