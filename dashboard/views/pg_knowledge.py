"""Treinar Agentes — gerenciamento da base de conhecimento dos agentes managed."""
import streamlit as st
import sys
import os
import re
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.models import SessionLocal, FonteConhecimento
from dashboard.components import page_header

# ─── CONSTANTES ───────────────────────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_KNOWLEDGE_DIR = _PROJECT_ROOT / "agents" / "knowledge"

_AGENTES = {
    "pedro":   {"nome": "Pedro",   "emoji": "🎯", "desc": "Google Ads"},
    "rodrigo": {"nome": "Rodrigo", "emoji": "✍️", "desc": "Copywriter"},
    "ana":     {"nome": "Ana",     "emoji": "🔬", "desc": "Landing Pages"},
    "lucas":   {"nome": "Lucas",   "emoji": "📊", "desc": "Estratégia"},
    "social":  {"nome": "Social",  "emoji": "📱", "desc": "Mídias Sociais"},
}

_TIPO_ICON = {
    "youtube_video":    "🎥",
    "youtube_playlist": "📋",
    "web_article":      "🌐",
    "pdf":              "📄",
    "instagram":        "📸",
    "course_video":     "🎓",
    "manual":           "✍️",
}

_ID_MAP_KEYS = {
    "pedro":   "PEDRO",
    "rodrigo": "RODRIGO",
    "ana":     "ANA",
    "lucas":   "LUCAS",
    "social":  "SOCIAL",
}


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _slugify(texto: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', texto.lower()).strip('_')


def _stats_disk(agent_key: str) -> dict:
    """Contagem de chars e arquivos nos .md em disco."""
    agent_dir = _KNOWLEDGE_DIR / agent_key
    if not agent_dir.exists():
        return {"arquivos": 0, "chars": 0, "fontes": []}
    fontes = []
    for md_file in sorted(agent_dir.glob("*.md")):
        if md_file.name.startswith("_"):
            continue
        conteudo = md_file.read_text(encoding="utf-8")
        fontes.append({
            "arquivo": md_file.name,
            "topico": md_file.stem.replace("_", " ").title(),
            "chars": len(conteudo),
            "path": md_file,
        })
    total = sum(f["chars"] for f in fontes)
    return {"arquivos": len(fontes), "chars": total, "fontes": fontes}


def _fontes_db(agent_key: str) -> list:
    """Busca fontes com status 'ok' do banco para um agente."""
    db = SessionLocal()
    try:
        return (
            db.query(FonteConhecimento)
            .filter(FonteConhecimento.agent_key == agent_key)
            .order_by(FonteConhecimento.criado_em.desc())
            .all()
        )
    finally:
        db.close()


def _salvar_md_disk(agent_key: str, topico: str, md: str):
    """Salva markdown em disco em agents/knowledge/{agent_key}/{slug}.md."""
    agent_dir = _KNOWLEDGE_DIR / agent_key
    agent_dir.mkdir(parents=True, exist_ok=True)
    slug = _slugify(topico)
    caminho = agent_dir / f"{slug}.md"
    caminho.write_text(md, encoding="utf-8")
    return caminho


def _remover_md_disk(agent_key: str, topico: str):
    """Remove arquivo .md de disco se existir."""
    agent_dir = _KNOWLEDGE_DIR / agent_key
    slug = _slugify(topico)
    caminho = agent_dir / f"{slug}.md"
    if caminho.exists():
        caminho.unlink()


def _aplicar_agente(agent_key: str) -> tuple:
    """
    Empurra system prompt atualizado para o agente managed.
    Retorna (sucesso: bool, mensagem: str).
    """
    try:
        from config.settings import (
            ANTHROPIC_API_KEY,
            AGENT_PEDRO_ID,
            AGENT_RODRIGO_ID,
            AGENT_ANA_ID,
            AGENT_LUCAS_ID,
            AGENT_MODERADOR_ID,
        )
    except ImportError as e:
        return False, f"Erro ao importar settings: {e}"

    _id_map = {
        "PEDRO":   AGENT_PEDRO_ID,
        "RODRIGO": AGENT_RODRIGO_ID,
        "ANA":     AGENT_ANA_ID,
        "LUCAS":   AGENT_LUCAS_ID,
        "SOCIAL":  None,
    }

    agent_key_upper = _ID_MAP_KEYS.get(agent_key, agent_key.upper())
    agent_id = _id_map.get(agent_key_upper)

    if not agent_id:
        return False, (
            f"ID do agente '{agent_key_upper}' não configurado no .env. "
            "Adicione AGENT_{}_ID.".format(agent_key_upper)
        )

    try:
        from agents.setup_agents import AGENTES
        cfg = next((a for a in AGENTES if a["key"] == agent_key_upper), None)
        if not cfg:
            return False, f"Configuração do agente '{agent_key_upper}' não encontrada em setup_agents.py"

        import anthropic
        client_api = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        ag = client_api.beta.agents.retrieve(agent_id)
        kwargs = {
            "version": ag.version,
            "system": cfg["system"],
        }
        if cfg.get("tools"):
            kwargs["tools"] = cfg["tools"]
        client_api.beta.agents.update(agent_id, **kwargs)
        chars = len(cfg["system"])
        return True, f"Agente {agent_key_upper} atualizado com sucesso! ({chars:,} chars no system prompt)"
    except Exception as e:
        return False, f"Erro ao atualizar agente: {e}"


# ─── RENDER PRINCIPAL ─────────────────────────────────────────────────────────

def render(cliente):
    st.markdown(
        page_header("🧠", "Treinar Agentes", "Adicione conhecimento especializado a cada agente"),
        unsafe_allow_html=True,
    )

    tab_labels = [
        f"{info['emoji']} {info['nome']} ({info['desc']})"
        for info in _AGENTES.values()
    ]
    tabs = st.tabs(tab_labels)

    for tab, (agent_key, info) in zip(tabs, _AGENTES.items()):
        with tab:
            _render_agent_tab(agent_key, info)


def _render_agent_tab(agent_key: str, info: dict):
    """Renderiza a aba de um agente específico."""
    stats_disk = _stats_disk(agent_key)
    fontes_db = _fontes_db(agent_key)

    fontes_db_ok = [f for f in fontes_db if f.status == "ok"]
    chars_db = sum(f.chars_extraidos or 0 for f in fontes_db_ok)
    total_chars = stats_disk["chars"] + chars_db
    total_arquivos = stats_disk["arquivos"] + len(fontes_db_ok)

    # ── Métricas ──────────────────────────────────────────────────────────────
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Base de Conhecimento", f"{total_chars:,} chars")
    with col_m2:
        st.metric("Fontes Totais", f"{total_arquivos}")
    with col_m3:
        st.metric("Adicionadas via Dashboard", f"{len(fontes_db_ok)}")

    st.divider()

    # ── Adicionar nova fonte ──────────────────────────────────────────────────
    st.markdown(
        "<p style='font-size:11px;font-weight:700;text-transform:uppercase;"
        "letter-spacing:1px;color:#3d5166;margin-bottom:12px'>Adicionar fonte de conhecimento</p>",
        unsafe_allow_html=True,
    )

    tab_url, tab_curso, tab_pdf = st.tabs(["🌐 URL (YouTube / Artigo)", "🎓 Vídeo de Curso (acesso pago)", "📄 PDF"])

    with tab_url:
        with st.form(f"form_url_{agent_key}", clear_on_submit=True):
            url_input = st.text_input(
                "URL da fonte",
                placeholder="https://youtube.com/watch?v=... ou https://artigo.com/...",
            )
            topico_input = st.text_input(
                "Nome do tópico",
                placeholder="ex: Estratégia de lances Google Ads",
            )
            submit_url = st.form_submit_button(
                "Processar URL", type="primary", use_container_width=True
            )

        if submit_url:
            if not url_input or not topico_input:
                st.warning("Preencha a URL e o nome do tópico.")
            else:
                _processar_e_salvar_url(agent_key, url_input, topico_input)

    with tab_curso:
        _render_curso_tab(agent_key)

    with tab_pdf:
        pdf_file = st.file_uploader(
            "Upload de PDF",
            type=["pdf"],
            key=f"pdf_{agent_key}",
            help="Faça upload de um PDF para extrair conhecimento",
        )
        topico_pdf = st.text_input(
            "Tópico do PDF",
            placeholder="ex: Manual de vendas",
            key=f"topico_pdf_{agent_key}",
        )
        if st.button("Processar PDF", key=f"btn_pdf_{agent_key}", use_container_width=True):
            if not pdf_file or not topico_pdf:
                st.warning("Selecione um PDF e informe o tópico.")
            else:
                _processar_e_salvar_pdf(agent_key, pdf_file, topico_pdf)

    st.divider()

    # ── Lista de fontes ───────────────────────────────────────────────────────
    st.markdown(
        "<p style='font-size:11px;font-weight:700;text-transform:uppercase;"
        "letter-spacing:1px;color:#3d5166;margin-bottom:12px'>Base de conhecimento atual</p>",
        unsafe_allow_html=True,
    )

    # Fontes em disco (read-only)
    if stats_disk["fontes"]:
        st.markdown(
            "<p style='font-size:12px;color:#475569;margin-bottom:8px'>"
            "✍️ Arquivos manuais (somente leitura)</p>",
            unsafe_allow_html=True,
        )
        for fonte in stats_disk["fontes"]:
            col_info, col_chars = st.columns([4, 1])
            with col_info:
                st.markdown(
                    f"<div style='font-size:13px;color:#94a3b8;padding:6px 0'>"
                    f"✍️ <strong>{fonte['topico']}</strong> "
                    f"<span style='color:#3d5166;font-size:11px'>({fonte['arquivo']})</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with col_chars:
                st.markdown(
                    f"<div style='font-size:12px;color:#3d5166;padding:8px 0;text-align:right'>"
                    f"{fonte['chars']:,} chars</div>",
                    unsafe_allow_html=True,
                )

    # Fontes do banco
    if fontes_db:
        st.markdown(
            "<p style='font-size:12px;color:#475569;margin-top:12px;margin-bottom:8px'>"
            "📥 Fontes adicionadas via dashboard</p>",
            unsafe_allow_html=True,
        )
        for fonte in fontes_db:
            tipo_icon = _TIPO_ICON.get(fonte.tipo or "web_article", "🌐")
            status_color = "#22c55e" if fonte.status == "ok" else ("#ef4444" if fonte.status == "erro" else "#f59e0b")
            status_label = fonte.status or "pendente"

            col_icon, col_info, col_meta, col_action = st.columns([1, 5, 2, 2])
            with col_icon:
                st.markdown(
                    f"<div style='font-size:20px;padding:4px 0'>{tipo_icon}</div>",
                    unsafe_allow_html=True,
                )
            with col_info:
                url_display = (fonte.url or "")[:60] + ("..." if len(fonte.url or "") > 60 else "")
                st.markdown(
                    f"<div style='font-size:13px;color:#e2e8f0;font-weight:600'>{fonte.topico}</div>"
                    f"<div style='font-size:11px;color:#3d5166'>{url_display}</div>",
                    unsafe_allow_html=True,
                )
            with col_meta:
                chars_display = f"{fonte.chars_extraidos:,} chars" if fonte.chars_extraidos else "—"
                data_display = fonte.criado_em.strftime("%d/%m/%y") if fonte.criado_em else ""
                st.markdown(
                    f"<div style='font-size:11px;color:{status_color};font-weight:700'>{status_label.upper()}</div>"
                    f"<div style='font-size:11px;color:#3d5166'>{chars_display} · {data_display}</div>",
                    unsafe_allow_html=True,
                )
            with col_action:
                if st.button("🗑 Remover", key=f"del_{fonte.id}", use_container_width=True):
                    _remover_fonte_db(fonte.id, agent_key, fonte.topico or "")
                    st.rerun()

            if fonte.status == "erro" and fonte.erro_msg:
                st.markdown(
                    f"<div style='font-size:11px;color:#ef4444;padding:4px 8px;background:rgba(239,68,68,0.08);"
                    f"border-radius:6px;margin-bottom:4px'>{fonte.erro_msg}</div>",
                    unsafe_allow_html=True,
                )

    if not stats_disk["fontes"] and not fontes_db:
        st.info("Nenhuma fonte de conhecimento ainda. Adicione URLs ou PDFs acima.")

    st.divider()

    # ── Aplicar ao agente ─────────────────────────────────────────────────────
    col_btn, col_desc = st.columns([2, 4])
    with col_btn:
        if st.button(
            f"🚀 Aplicar ao Agente {info['nome']}",
            key=f"apply_{agent_key}",
            type="primary",
            use_container_width=True,
        ):
            # Primeiro: sincroniza .md files das fontes DB para o disco
            _sincronizar_fontes_db_para_disk(agent_key)
            # Depois: faz push do system prompt
            with st.spinner("Enviando system prompt atualizado..."):
                sucesso, msg = _aplicar_agente(agent_key)
            if sucesso:
                st.success(msg)
            else:
                st.error(msg)
    with col_desc:
        st.caption(
            "Sincroniza o conhecimento em disco e envia o system prompt atualizado "
            "para o agente via Anthropic API."
        )


# ─── CURSO TAB ────────────────────────────────────────────────────────────────

def _render_curso_tab(agent_key: str):
    """Aba para importar vídeos de plataformas de cursos pagos."""
    st.markdown(
        """
        <div style='background:rgba(0,207,253,0.06);border:1px solid rgba(0,207,253,0.2);
        border-radius:8px;padding:12px 16px;margin-bottom:16px'>
        <div style='font-size:13px;font-weight:700;color:#00CFFD;margin-bottom:4px'>
        🎓 Importar vídeo de curso pago (Subido, Hotmart, Kiwify...)</div>
        <div style='font-size:12px;color:#64748b'>
        Cole o link do vídeo e faça upload do seu arquivo de cookies para autenticar.
        O sistema baixa o áudio, transcreve com Whisper e extrai o conhecimento com Claude.
        </div></div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("ℹ️ Como exportar cookies do browser", expanded=False):
        st.markdown("""
**Chrome / Edge:**
1. Instale a extensão **"Get cookies.txt LOCALLY"** (Chrome Web Store)
2. Acesse o curso e faça login
3. Clique na extensão e selecione **"Export"** → salva `cookies.txt`

**Firefox:**
1. Instale **"cookies.txt"** (addons.mozilla.org)
2. Acesse o curso logado → clique na extensão → **"Current Site"** → Download

O arquivo exportado é no formato Netscape (`.txt`). Ele contém sua sessão autenticada — não compartilhe com ninguém.
        """)

    with st.form(f"form_curso_{agent_key}", clear_on_submit=True):
        url_curso = st.text_input(
            "Link do vídeo do curso",
            placeholder="https://subido.com.br/cst/.../aula/...",
        )
        topico_curso = st.text_input(
            "Nome do tópico",
            placeholder="ex: Estrutura de campanhas Pedro Sobral",
        )
        cookies_upload = st.file_uploader(
            "Arquivo cookies.txt (autenticação)",
            type=["txt"],
            help="Exporte os cookies do seu browser enquanto está logado no curso.",
        )
        submit_curso = st.form_submit_button(
            "🎓 Baixar e Transcrever Vídeo", type="primary", use_container_width=True
        )

    if submit_curso:
        if not url_curso or not topico_curso:
            st.warning("Preencha o link e o nome do tópico.")
        elif not cookies_upload:
            st.warning("Faça upload do arquivo cookies.txt para autenticar no curso.")
        else:
            _processar_e_salvar_curso(agent_key, url_curso, topico_curso, cookies_upload)


# ─── AÇÕES ────────────────────────────────────────────────────────────────────

def _processar_e_salvar_curso(agent_key: str, url: str, topico: str, cookies_file_upload):
    """Processa um vídeo de curso com autenticação via cookies."""
    import tempfile
    from etl.processar_fonte import processar_url

    cookies_bytes = cookies_file_upload.read()
    mensagens = []

    def on_status(msg):
        mensagens.append(msg)

    with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as tmp:
        tmp.write(cookies_bytes)
        cookies_path = tmp.name

    try:
        with st.status("Baixando e transcrevendo vídeo de curso...", expanded=True) as status_widget:
            resultado = processar_url(
                url=url,
                agent_key=agent_key,
                topico=topico,
                on_status=on_status,
                cookies_file=cookies_path,
            )
            for msg in mensagens:
                st.write(msg)

            if resultado["erro"]:
                status_widget.update(label="Erro ao processar", state="error")
                _salvar_fonte_db(
                    agent_key=agent_key,
                    tipo="course_video",
                    url=url,
                    topico=topico,
                    status="erro",
                    md_gerado=None,
                    chars=0,
                    erro_msg=resultado["erro"],
                )
                st.error(resultado["erro"])
            else:
                _salvar_md_disk(agent_key, topico, resultado["md"])
                _salvar_fonte_db(
                    agent_key=agent_key,
                    tipo="course_video",
                    url=url,
                    topico=topico,
                    status="ok",
                    md_gerado=resultado["md"],
                    chars=resultado["chars"],
                    erro_msg=None,
                )
                chars = resultado["chars"]
                status_widget.update(
                    label=f"Concluído! {chars:,} chars extraídos",
                    state="complete",
                )
                st.success(f"Vídeo de curso processado: {chars:,} chars sobre '{topico}'")
    finally:
        import os as _os
        try:
            _os.unlink(cookies_path)
        except Exception:
            pass

    st.rerun()


def _processar_e_salvar_url(agent_key: str, url: str, topico: str):
    """Processa uma URL, salva no banco e em disco."""
    from etl.processar_fonte import processar_url

    mensagens = []

    def on_status(msg):
        mensagens.append(msg)

    with st.status("Processando URL...", expanded=True) as status_widget:
        resultado = processar_url(
            url=url,
            agent_key=agent_key,
            topico=topico,
            on_status=on_status,
        )
        for msg in mensagens:
            st.write(msg)

        if resultado["erro"]:
            status_widget.update(label="Erro ao processar", state="error")
            _salvar_fonte_db(
                agent_key=agent_key,
                tipo=resultado["tipo"],
                url=url,
                topico=topico,
                status="erro",
                md_gerado=None,
                chars=0,
                erro_msg=resultado["erro"],
            )
            st.error(resultado["erro"])
        else:
            _salvar_md_disk(agent_key, topico, resultado["md"])
            _salvar_fonte_db(
                agent_key=agent_key,
                tipo=resultado["tipo"],
                url=url,
                topico=topico,
                status="ok",
                md_gerado=resultado["md"],
                chars=resultado["chars"],
                erro_msg=None,
            )
            chars = resultado["chars"]
            tipo = resultado["tipo"]
            status_widget.update(
                label=f"Concluído! {chars:,} chars extraídos ({tipo})",
                state="complete",
            )
            st.success(f"Conhecimento adicionado: {chars:,} chars sobre '{topico}'")

    st.rerun()


def _processar_e_salvar_pdf(agent_key: str, pdf_file, topico: str):
    """Processa um PDF, salva no banco e em disco."""
    from etl.processar_fonte import processar_pdf

    conteudo_bytes = pdf_file.read()
    nome_arquivo = pdf_file.name
    mensagens = []

    def on_status(msg):
        mensagens.append(msg)

    with st.status("Processando PDF...", expanded=True) as status_widget:
        resultado = processar_pdf(
            conteudo_bytes=conteudo_bytes,
            nome_arquivo=nome_arquivo,
            agent_key=agent_key,
            topico=topico,
            on_status=on_status,
        )
        for msg in mensagens:
            st.write(msg)

        if resultado["erro"]:
            status_widget.update(label="Erro ao processar PDF", state="error")
            _salvar_fonte_db(
                agent_key=agent_key,
                tipo="pdf",
                url=nome_arquivo,
                topico=topico,
                status="erro",
                md_gerado=None,
                chars=0,
                erro_msg=resultado["erro"],
            )
            st.error(resultado["erro"])
        else:
            _salvar_md_disk(agent_key, topico, resultado["md"])
            _salvar_fonte_db(
                agent_key=agent_key,
                tipo="pdf",
                url=nome_arquivo,
                topico=topico,
                status="ok",
                md_gerado=resultado["md"],
                chars=resultado["chars"],
                erro_msg=None,
            )
            chars = resultado["chars"]
            status_widget.update(
                label=f"Concluído! {chars:,} chars extraídos",
                state="complete",
            )
            st.success(f"PDF processado: {chars:,} chars sobre '{topico}'")

    st.rerun()


def _salvar_fonte_db(
    agent_key: str,
    tipo: str,
    url: str,
    topico: str,
    status: str,
    md_gerado,
    chars: int,
    erro_msg,
):
    """Insere ou atualiza um registro de FonteConhecimento no banco."""
    db = SessionLocal()
    try:
        fonte = FonteConhecimento(
            agent_key=agent_key,
            tipo=tipo,
            url=url,
            topico=topico,
            status=status,
            md_gerado=md_gerado,
            chars_extraidos=chars,
            erro_msg=erro_msg,
            processado_em=datetime.now() if status in ("ok", "erro") else None,
        )
        db.add(fonte)
        db.commit()
    finally:
        db.close()


def _remover_fonte_db(fonte_id: int, agent_key: str, topico: str):
    """Remove fonte do banco e o arquivo .md correspondente em disco."""
    db = SessionLocal()
    try:
        fonte = db.query(FonteConhecimento).filter(FonteConhecimento.id == fonte_id).first()
        if fonte:
            db.delete(fonte)
            db.commit()
    finally:
        db.close()

    _remover_md_disk(agent_key, topico)


def _sincronizar_fontes_db_para_disk(agent_key: str):
    """Garante que todos os md_gerado OK do banco existam como arquivos em disco."""
    db = SessionLocal()
    try:
        fontes = (
            db.query(FonteConhecimento)
            .filter(
                FonteConhecimento.agent_key == agent_key,
                FonteConhecimento.status == "ok",
                FonteConhecimento.md_gerado.isnot(None),
            )
            .all()
        )
        for f in fontes:
            if f.md_gerado and f.topico:
                _salvar_md_disk(agent_key, f.topico, f.md_gerado)
    finally:
        db.close()
