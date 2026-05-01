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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── BASE ── */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    .main { background: #F8FAFC !important; }
    .main .block-container {
        padding: 28px 36px 64px !important;
        max-width: 1140px !important;
    }
    [data-testid="stHeader"] { background: transparent !important; border-bottom: none !important; }
    [data-testid="stAppViewContainer"] > section:first-child { padding-top: 0 !important; }

    /* ── SIDEBAR — DARK PREMIUM ── */
    section[data-testid="stSidebar"] { min-width: 230px !important; max-width: 248px !important; }
    section[data-testid="stSidebar"] > div:first-child {
        background: #0F172A !important;
        border-right: 1px solid #1E293B !important;
        padding-top: 0 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p { color: #475569 !important; }
    section[data-testid="stSidebar"] label { color: #475569 !important; font-size: 11px !important; font-weight: 600 !important; letter-spacing: 0.5px !important; text-transform: uppercase !important; }
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] small { color: #475569 !important; }
    section[data-testid="stSidebar"] hr { border-top: 1px solid #1E293B !important; margin: 8px 0 !important; }

    /* Sidebar selectbox */
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] span { color: #CBD5E1 !important; font-size: 13px !important; }
    section[data-testid="stSidebar"] [data-baseweb="select"] svg { fill: #475569 !important; }

    /* Sidebar nav buttons */
    section[data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        color: #64748B !important;
        border: none !important;
        border-radius: 8px !important;
        text-align: left !important;
        padding: 9px 12px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        width: 100% !important;
        transition: background 0.15s, color 0.15s !important;
        box-shadow: none !important;
        letter-spacing: 0 !important;
        margin: 1px 0 !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.07) !important;
        color: #CBD5E1 !important;
        transform: none !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: rgba(229,57,53,0.15) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-left: 3px solid #E53935 !important;
        border-radius: 0 8px 8px 0 !important;
        padding-left: 14px !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: rgba(229,57,53,0.22) !important;
    }

    /* ── METRICS ── */
    [data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 18px 20px !important;
        box-shadow: 0 1px 3px rgba(15,23,42,0.04) !important;
        transition: box-shadow 0.2s !important;
    }
    [data-testid="stMetric"]:hover { box-shadow: 0 4px 14px rgba(15,23,42,0.08) !important; }
    [data-testid="stMetricLabel"] > div {
        font-size: 11px !important; font-weight: 700 !important;
        text-transform: uppercase !important; letter-spacing: 0.8px !important; color: #94A3B8 !important;
    }
    [data-testid="stMetricValue"] > div {
        font-size: 30px !important; font-weight: 800 !important;
        color: #0F172A !important; line-height: 1.1 !important;
    }
    [data-testid="stMetricDelta"] { font-size: 12px !important; font-weight: 500 !important; }

    /* ── BUTTONS — MAIN CONTENT ── */
    .main .stButton > button {
        border-radius: 8px !important; font-size: 13px !important; font-weight: 600 !important;
        padding: 9px 18px !important; transition: all 0.18s !important;
        letter-spacing: 0.1px !important; cursor: pointer !important;
    }
    .main .stButton > button[kind="primary"] {
        background: #E53935 !important; color: #FFFFFF !important; border: none !important;
        box-shadow: 0 2px 8px rgba(229,57,53,0.25) !important;
    }
    .main .stButton > button[kind="primary"]:hover {
        background: #C62828 !important; box-shadow: 0 4px 14px rgba(229,57,53,0.32) !important;
        transform: translateY(-1px) !important;
    }
    .main .stButton > button[kind="primary"]:active { transform: translateY(0) !important; }
    .main .stButton > button[kind="secondary"] {
        background: #FFFFFF !important; color: #374151 !important;
        border: 1px solid #D1D5DB !important; box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
    }
    .main .stButton > button[kind="secondary"]:hover {
        background: #F9FAFB !important; border-color: #9CA3AF !important;
        transform: translateY(-1px) !important;
    }

    /* ── INPUTS ── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        border: 1px solid #E2E8F0 !important; border-radius: 8px !important;
        font-size: 14px !important; color: #0F172A !important;
        padding: 10px 14px !important; transition: border-color 0.2s, box-shadow 0.2s !important;
        background: #FFFFFF !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #E53935 !important;
        box-shadow: 0 0 0 3px rgba(229,57,53,0.10) !important;
    }
    .stTextArea > div > div > textarea {
        border: 1px solid #E2E8F0 !important; border-radius: 8px !important;
        font-size: 14px !important; color: #0F172A !important;
        transition: border-color 0.2s, box-shadow 0.2s !important; background: #FFFFFF !important;
    }
    .stTextArea > div > div > textarea:focus {
        border-color: #E53935 !important; box-shadow: 0 0 0 3px rgba(229,57,53,0.10) !important;
    }
    .stTextInput label, .stTextArea label, .stSelectbox label,
    .stNumberInput label, .stMultiSelect label, .stDateInput label,
    .stRadio label:first-child, .stCheckbox label:first-child {
        font-size: 11px !important; font-weight: 700 !important; color: #64748B !important;
        text-transform: uppercase !important; letter-spacing: 0.6px !important;
    }

    /* ── SELECT / MULTISELECT ── */
    .main [data-baseweb="select"] > div {
        border: 1px solid #E2E8F0 !important; border-radius: 8px !important;
        font-size: 14px !important; background: #FFFFFF !important;
    }
    [data-baseweb="tag"] {
        background: #FEF2F2 !important; border: none !important; border-radius: 6px !important;
    }
    [data-baseweb="tag"] span { color: #B91C1C !important; font-weight: 600 !important; font-size: 12px !important; }

    /* ── TABS ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0 !important; background: #F1F5F9 !important; border-radius: 10px !important;
        padding: 4px !important; border-bottom: none !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important; border: none !important; border-radius: 7px !important;
        padding: 8px 18px !important; font-size: 13px !important; font-weight: 500 !important;
        color: #64748B !important; transition: all 0.15s !important;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #374151 !important; background: rgba(255,255,255,0.5) !important; }
    .stTabs [aria-selected="true"] {
        background: #FFFFFF !important; color: #0F172A !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.10), 0 1px 2px rgba(0,0,0,0.06) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 20px !important; }

    /* ── EXPANDERS ── */
    [data-testid="stExpander"] {
        border: 1px solid #E2E8F0 !important; border-radius: 10px !important;
        background: #FFFFFF !important; overflow: hidden !important;
        box-shadow: 0 1px 3px rgba(15,23,42,0.03) !important; margin-bottom: 8px !important;
    }
    [data-testid="stExpander"] summary {
        padding: 14px 18px !important; font-size: 13px !important;
        font-weight: 600 !important; color: #374151 !important;
    }
    [data-testid="stExpander"] summary:hover { background: #F8FAFC !important; }
    [data-testid="stExpander"] > div:last-child { padding: 0 18px 16px !important; }

    /* ── FORMS ── */
    [data-testid="stForm"] {
        border: 1px solid #E2E8F0 !important; border-radius: 12px !important;
        background: #FFFFFF !important; padding: 24px !important;
        box-shadow: 0 1px 3px rgba(15,23,42,0.04) !important;
    }

    /* ── ALERTS ── */
    [data-testid="stAlert"] { border-radius: 10px !important; padding: 12px 16px !important; font-size: 13px !important; }

    /* ── DIVIDERS ── */
    hr { border: none !important; border-top: 1px solid #E2E8F0 !important; margin: 20px 0 !important; }

    /* ── PROGRESS / SPINNER ── */
    .stProgress > div > div { background: #F1F5F9 !important; border-radius: 99px !important; height: 6px !important; }
    .stProgress > div > div > div { background: #E53935 !important; border-radius: 99px !important; }

    /* ── DOWNLOAD BUTTON ── */
    .stDownloadButton > button {
        background: #F8FAFC !important; border: 1px solid #E2E8F0 !important;
        color: #374151 !important; border-radius: 8px !important;
        font-size: 13px !important; font-weight: 500 !important;
    }
    .stDownloadButton > button:hover { background: #F1F5F9 !important; border-color: #CBD5E1 !important; }

    /* ── DATAFRAME ── */
    [data-testid="stDataFrame"] { border: 1px solid #E2E8F0 !important; border-radius: 10px !important; overflow: hidden !important; }

    /* ── STATUS WIDGET ── */
    [data-testid="stStatus"] { border: 1px solid #E2E8F0 !important; border-radius: 10px !important; background: #FFFFFF !important; }

    /* ── CAPTIONS ── */
    .stCaption { font-size: 12px !important; color: #94A3B8 !important; }

    /* ── RADIO ── */
    .stRadio > div { gap: 6px !important; }
    .stRadio > div > label { font-size: 13px !important; font-weight: 400 !important; color: #374151 !important; }

    /* ── PLOTLY ── */
    .js-plotly-plot { border-radius: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── INICIALIZAÇÃO ─────────────────────────────────────────────────────────────

criar_tabelas()

# ─── SIDEBAR + ROTEAMENTO ─────────────────────────────────────────────────────

cliente = render_sidebar()

# Páginas que funcionam sem cliente selecionado
_PAGINAS_SEM_CLIENTE = {"consulta", "director"}

if cliente is None and st.session_state.get("page", "overview") not in _PAGINAS_SEM_CLIENTE:
    # Tela de boas-vindas quando não há cliente
    st.markdown(
        """
        <div style='text-align:center;padding:72px 24px 40px'>
          <div style='display:inline-flex;width:72px;height:72px;background:#FEF2F2;
                      border-radius:20px;align-items:center;justify-content:center;
                      font-size:36px;border:1px solid #FECACA;margin-bottom:20px'>🚀</div>
          <h1 style='font-size:28px;font-weight:900;color:#0F172A;margin:0 0 8px;
                     letter-spacing:-0.5px'>
            Unbound<span style='color:#E53935'>Sales</span>
          </h1>
          <p style='color:#64748B;font-size:15px;margin:0'>
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
                "<p style='font-size:13px;font-weight:700;color:#0F172A;margin-bottom:16px'>"
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
    from dashboard.pages.pg_overview import render
elif page == "team":
    from dashboard.pages.pg_team import render
elif page == "market":
    from dashboard.pages.pg_market import render
elif page == "copywriter":
    from dashboard.pages.pg_copywriter import render
elif page == "expert":
    from dashboard.pages.pg_expert import render
elif page == "landing":
    from dashboard.pages.pg_landing import render
elif page == "leads":
    from dashboard.pages.pg_leads import render
elif page == "social":
    from dashboard.pages.pg_social import render
elif page == "designer":
    from dashboard.pages.pg_designer import render
elif page == "consulta":
    from dashboard.pages.pg_consulta import render
elif page == "director":
    from dashboard.pages.pg_director import render
elif page == "clientes":
    from dashboard.pages.pg_clientes import render
else:
    from dashboard.pages.pg_overview import render

render(cliente)
