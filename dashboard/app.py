"""
UnboundSales — Painel de Controle Visual
Execute com: streamlit run dashboard/app.py
"""
import streamlit as st
import sys
import os

# Garante que o root do projeto está no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importação lazy das páginas (evita carregar todos os agentes na inicialização)
from dashboard.sidebar import render_sidebar
from database.models import criar_tabelas

# ─── CONFIGURAÇÃO DA PÁGINA ────────────────────────────────────────────────────

st.set_page_config(
    page_title="UnboundSales | Painel de IA",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "UnboundSales — Sistema de agentes de IA para agências de marketing digital.",
    },
)

# ─── CSS GLOBAL ───────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ── BASE — UnboundSales Dark Theme ── */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    .main { background: #0a0a0f !important; }
    .main .block-container {
        padding: 28px 36px 64px !important;
        max-width: 1180px !important;
    }
    [data-testid="stHeader"] { background: transparent !important; border-bottom: none !important; }
    [data-testid="stAppViewContainer"] > section:first-child { padding-top: 0 !important; }

    /* ── SIDEBAR ── */
    section[data-testid="stSidebar"] { min-width: 234px !important; max-width: 252px !important; }
    section[data-testid="stSidebar"] > div:first-child {
        background: #050508 !important;
        border-right: 1px solid rgba(0,207,253,0.10) !important;
        padding-top: 0 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p { color: #3d4f63 !important; }
    section[data-testid="stSidebar"] label {
        color: #3d5166 !important; font-size: 10px !important; font-weight: 700 !important;
        letter-spacing: 1.2px !important; text-transform: uppercase !important;
    }
    section[data-testid="stSidebar"] hr { border-top: 1px solid rgba(0,207,253,0.08) !important; margin: 8px 0 !important; }

    /* Sidebar selectbox */
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: rgba(0,207,253,0.05) !important;
        border: 1px solid rgba(0,207,253,0.15) !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] span { color: #94a8bd !important; font-size: 13px !important; }
    section[data-testid="stSidebar"] [data-baseweb="select"] svg { fill: #3d5166 !important; }

    /* Sidebar nav buttons */
    section[data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        color: #4a6070 !important;
        border: none !important;
        border-radius: 6px !important;
        text-align: left !important;
        padding: 8px 12px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        width: 100% !important;
        transition: all 0.15s !important;
        box-shadow: none !important;
        letter-spacing: 0 !important;
        margin: 1px 0 !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(0,207,253,0.07) !important;
        color: #a0c4d4 !important;
        transform: none !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: rgba(0,207,253,0.10) !important;
        color: #00CFFD !important;
        font-weight: 700 !important;
        border-left: 3px solid #00CFFD !important;
        border-radius: 0 6px 6px 0 !important;
        padding-left: 14px !important;
        box-shadow: 0 0 12px rgba(0,207,253,0.15) !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: rgba(0,207,253,0.15) !important;
        box-shadow: 0 0 18px rgba(0,207,253,0.22) !important;
    }

    /* ── METRICS ── */
    [data-testid="stMetric"] {
        background: #0f1117 !important;
        border: 1px solid rgba(0,207,253,0.12) !important;
        border-radius: 12px !important;
        padding: 18px 20px !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    [data-testid="stMetric"]:hover {
        border-color: rgba(0,207,253,0.28) !important;
        box-shadow: 0 0 20px rgba(0,207,253,0.08) !important;
    }
    [data-testid="stMetricLabel"] > div {
        font-size: 10px !important; font-weight: 700 !important;
        text-transform: uppercase !important; letter-spacing: 1px !important;
        color: #3d5166 !important;
    }
    [data-testid="stMetricValue"] > div {
        font-size: 28px !important; font-weight: 800 !important;
        color: #e2e8f0 !important; line-height: 1.1 !important;
    }
    [data-testid="stMetricDelta"] { font-size: 12px !important; font-weight: 500 !important; }

    /* ── BUTTONS ── */
    .stButton > button {
        border-radius: 8px !important; font-size: 13px !important; font-weight: 600 !important;
        padding: 9px 18px !important; transition: all 0.18s !important;
        letter-spacing: 0.2px !important; cursor: pointer !important;
    }
    .stButton > button[kind="primary"] {
        background: #00CFFD !important; color: #000000 !important; border: none !important;
        box-shadow: 0 0 16px rgba(0,207,253,0.35) !important; font-weight: 700 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #00b8e0 !important;
        box-shadow: 0 0 28px rgba(0,207,253,0.50) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button[kind="primary"]:active { transform: translateY(0) !important; }
    .stButton > button[kind="secondary"] {
        background: rgba(255,255,255,0.04) !important;
        color: #94a3b8 !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: rgba(0,207,253,0.08) !important;
        border-color: rgba(0,207,253,0.25) !important;
        color: #00CFFD !important;
        transform: translateY(-1px) !important;
    }

    /* ── INPUTS ── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: #0f1117 !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
        font-size: 14px !important;
        padding: 10px 14px !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #00CFFD !important;
        box-shadow: 0 0 0 3px rgba(0,207,253,0.12) !important;
    }
    .stTextArea > div > div > textarea {
        background: #0f1117 !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
        font-size: 14px !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    .stTextArea > div > div > textarea:focus {
        border-color: #00CFFD !important;
        box-shadow: 0 0 0 3px rgba(0,207,253,0.12) !important;
    }
    .stTextInput label, .stTextArea label, .stSelectbox label,
    .stNumberInput label, .stMultiSelect label, .stDateInput label,
    .stRadio > label, .stCheckbox > label {
        font-size: 10px !important; font-weight: 700 !important; color: #3d5166 !important;
        text-transform: uppercase !important; letter-spacing: 1px !important;
    }

    /* ── SELECT / MULTISELECT ── */
    [data-baseweb="select"] > div {
        background: #0f1117 !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
    }
    [data-baseweb="select"] > div:focus-within {
        border-color: #00CFFD !important;
        box-shadow: 0 0 0 3px rgba(0,207,253,0.12) !important;
    }
    [data-baseweb="tag"] {
        background: rgba(0,207,253,0.12) !important;
        border: 1px solid rgba(0,207,253,0.25) !important;
        border-radius: 6px !important;
    }
    [data-baseweb="tag"] span { color: #00CFFD !important; font-weight: 600 !important; font-size: 12px !important; }
    [data-baseweb="menu"] { background: #0f1117 !important; border: 1px solid rgba(0,207,253,0.15) !important; }
    [role="option"]:hover { background: rgba(0,207,253,0.08) !important; }

    /* ── TABS ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0 !important;
        background: #0f1117 !important;
        border-radius: 10px !important;
        padding: 4px !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important; border: none !important; border-radius: 7px !important;
        padding: 8px 18px !important; font-size: 13px !important; font-weight: 500 !important;
        color: #4a6070 !important; transition: all 0.15s !important;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #94a3b8 !important; }
    .stTabs [aria-selected="true"] {
        background: rgba(0,207,253,0.12) !important;
        color: #00CFFD !important;
        font-weight: 700 !important;
        box-shadow: 0 0 10px rgba(0,207,253,0.15) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 20px !important; }

    /* ── EXPANDERS ── */
    [data-testid="stExpander"] {
        border: 1px solid rgba(255,255,255,0.07) !important;
        border-radius: 10px !important;
        background: #0f1117 !important;
        overflow: hidden !important;
        margin-bottom: 8px !important;
    }
    [data-testid="stExpander"]:hover { border-color: rgba(0,207,253,0.20) !important; }
    [data-testid="stExpander"] summary {
        padding: 14px 18px !important; font-size: 13px !important;
        font-weight: 600 !important; color: #94a3b8 !important;
    }
    [data-testid="stExpander"] > div:last-child { padding: 0 18px 16px !important; }

    /* ── FORMS ── */
    [data-testid="stForm"] {
        border: 1px solid rgba(0,207,253,0.12) !important;
        border-radius: 12px !important;
        background: #0f1117 !important;
        padding: 24px !important;
    }

    /* ── ALERTS ── */
    [data-testid="stAlert"] { border-radius: 10px !important; padding: 12px 16px !important; font-size: 13px !important; }

    /* ── DIVIDERS ── */
    hr { border: none !important; border-top: 1px solid rgba(255,255,255,0.06) !important; margin: 20px 0 !important; }

    /* ── PROGRESS ── */
    .stProgress > div > div { background: #1a2030 !important; border-radius: 99px !important; height: 4px !important; }
    .stProgress > div > div > div { background: #00CFFD !important; border-radius: 99px !important; box-shadow: 0 0 8px rgba(0,207,253,0.5) !important; }

    /* ── DOWNLOAD BUTTON ── */
    .stDownloadButton > button {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        color: #94a3b8 !important; border-radius: 8px !important;
        font-size: 13px !important; font-weight: 500 !important;
    }
    .stDownloadButton > button:hover {
        border-color: rgba(0,207,253,0.30) !important;
        color: #00CFFD !important;
    }

    /* ── STATUS WIDGET ── */
    [data-testid="stStatus"] {
        border: 1px solid rgba(0,207,253,0.15) !important;
        border-radius: 10px !important;
        background: #0f1117 !important;
    }

    /* ── DATAFRAME ── */
    [data-testid="stDataFrame"] { border: 1px solid rgba(255,255,255,0.07) !important; border-radius: 10px !important; overflow: hidden !important; }

    /* ── CAPTIONS ── */
    .stCaption, small { font-size: 12px !important; color: #3d5166 !important; }

    /* ── RADIO ── */
    .stRadio > div { gap: 6px !important; }

    /* ── CONTAINERS ── */
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background: #0f1117 !important;
        border: 1px solid rgba(0,207,253,0.10) !important;
        border-radius: 10px !important;
    }

    /* ── CHAT MESSAGES (agent conversations) ── */
    [data-testid="stChatMessage"] {
        background: #0f1117 !important;
        border: 1px solid rgba(255,255,255,0.07) !important;
        border-radius: 12px !important;
        margin-bottom: 12px !important;
    }

    /* ── PLOTLY ── */
    .js-plotly-plot { border-radius: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── AUTENTICAÇÃO ────────────────────────────────────────────────────────────

def _tela_login():
    col_l, col_c, col_r = st.columns([1, 1, 1])
    with col_c:
        st.markdown(
            """
            <div style='text-align:center;padding:64px 0 36px'>
              <div style='display:inline-flex;width:68px;height:68px;
                          background:rgba(0,207,253,0.08);
                          border-radius:20px;align-items:center;justify-content:center;
                          font-size:32px;border:1px solid rgba(0,207,253,0.25);
                          margin-bottom:24px;box-shadow:0 0 24px rgba(0,207,253,0.15)'>🔐</div>
              <h1 style='font-size:28px;font-weight:900;margin:0 0 6px;letter-spacing:-0.5px'>
                <span style='color:#e2e8f0'>Unbound</span><span style='color:#00CFFD;
                text-shadow:0 0 16px rgba(0,207,253,0.6)'>Sales</span>
              </h1>
              <p style='color:#3d5166;font-size:14px;margin:0;letter-spacing:0.3px'>Acesso restrito</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("form_login"):
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)
        if entrar:
            import hashlib
            from config.settings import APP_PASSWORD
            esperado = APP_PASSWORD or ""
            if senha == esperado:
                st.session_state["_auth"] = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

if not st.session_state.get("_auth", False):
    _tela_login()

# ─── INICIALIZAÇÃO ─────────────────────────────────────────────────────────────

criar_tabelas()

# ─── SIDEBAR + ROTEAMENTO ─────────────────────────────────────────────────────

cliente = render_sidebar()

# Páginas que funcionam sem cliente selecionado
_PAGINAS_SEM_CLIENTE = {"consulta", "director", "knowledge"}

if cliente is None and st.session_state.get("page", "overview") not in _PAGINAS_SEM_CLIENTE:
    # Tela de boas-vindas quando não há cliente
    st.markdown(
        """
        <div style='text-align:center;padding:72px 24px 40px'>
          <div style='display:inline-flex;width:72px;height:72px;
                      background:rgba(0,207,253,0.08);
                      border-radius:20px;align-items:center;justify-content:center;
                      font-size:36px;border:1px solid rgba(0,207,253,0.25);
                      margin-bottom:24px;box-shadow:0 0 28px rgba(0,207,253,0.12)'>🚀</div>
          <h1 style='font-size:30px;font-weight:900;margin:0 0 10px;letter-spacing:-0.5px'>
            <span style='color:#e2e8f0'>Unbound</span><span style='color:#00CFFD;
            text-shadow:0 0 18px rgba(0,207,253,0.6)'>Sales</span>
          </h1>
          <p style='color:#3d5166;font-size:15px;margin:0'>
            Painel de IA para agências de marketing digital.<br>
            Cadastre seu primeiro cliente para começar.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        from database.models import SessionLocal, Cliente as ClienteModel
        with st.form("form_primeiro_cliente"):
            st.markdown(
                "<p style='font-size:11px;font-weight:700;text-transform:uppercase;"
                "letter-spacing:1px;color:#3d5166;margin-bottom:16px'>"
                "Cadastrar primeiro cliente</p>",
                unsafe_allow_html=True,
            )
            nome     = st.text_input("Nome da empresa")
            col_a, col_b = st.columns(2)
            segmento = col_a.text_input("Segmento", placeholder="desentupidora")
            cidade   = col_b.text_input("Cidade")
            if st.form_submit_button("Começar", type="primary", use_container_width=True):
                if nome and segmento:
                    db = SessionLocal()
                    try:
                        c = ClienteModel(nome=nome, segmento=segmento, cidade=cidade,
                                         prompt_personalizado="simpático e profissional")
                        db.add(c)
                        db.commit()
                    finally:
                        db.close()
                    st.rerun()
    st.stop()

# ─── DISPATCH DE PÁGINAS ──────────────────────────────────────────────────────

page = st.session_state.get("page", "overview")

if page == "overview":
    from dashboard.views.pg_overview import render
elif page == "team":
    from dashboard.views.pg_team import render
elif page == "market":
    from dashboard.views.pg_market import render
elif page == "copywriter":
    from dashboard.views.pg_copywriter import render
elif page == "expert":
    from dashboard.views.pg_expert import render
elif page == "landing":
    from dashboard.views.pg_landing import render
elif page == "leads":
    from dashboard.views.pg_leads import render
elif page == "social":
    from dashboard.views.pg_social import render
elif page == "designer":
    from dashboard.views.pg_designer import render
elif page == "consulta":
    from dashboard.views.pg_consulta import render
elif page == "director":
    from dashboard.views.pg_director import render
elif page == "clientes":
    from dashboard.views.pg_clientes import render
elif page == "knowledge":
    from dashboard.views.pg_knowledge import render
else:
    from dashboard.views.pg_overview import render

render(cliente)
