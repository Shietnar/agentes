"""
Design System — UnboundSales
Componentes reutilizáveis para UX/UI consistente em todas as páginas.
"""

# ─── PALETA ───────────────────────────────────────────────────────────────────

COLORS = {
    "red":    {"bg": "#FEF2F2", "text": "#B91C1C", "border": "#FECACA", "solid": "#E53935"},
    "green":  {"bg": "#F0FDF4", "text": "#166534", "border": "#BBF7D0", "solid": "#16A34A"},
    "amber":  {"bg": "#FFFBEB", "text": "#92400E", "border": "#FDE68A", "solid": "#D97706"},
    "blue":   {"bg": "#EFF6FF", "text": "#1D4ED8", "border": "#BFDBFE", "solid": "#2563EB"},
    "purple": {"bg": "#FAF5FF", "text": "#6D28D9", "border": "#DDD6FE", "solid": "#7C3AED"},
    "gray":   {"bg": "#F8FAFC", "text": "#475569", "border": "#E2E8F0", "solid": "#64748B"},
    "orange": {"bg": "#FFF7ED", "text": "#9A3412", "border": "#FED7AA", "solid": "#EA580C"},
}

AGENT_COLORS = {
    "lucas":   {"solid": "#2563EB",  "bg": "#EFF6FF"},
    "pedro":   {"solid": "#DC2626",  "bg": "#FEF2F2"},
    "rodrigo": {"solid": "#16A34A",  "bg": "#F0FDF4"},
    "ana":     {"solid": "#7C3AED",  "bg": "#FAF5FF"},
    "social":  {"solid": "#EA580C",  "bg": "#FFF7ED"},
    "moderador": {"solid": "#0F172A","bg": "#F8FAFC"},
}


# ─── HEADERS ─────────────────────────────────────────────────────────────────

def page_header(icon: str, title: str, subtitle: str = "") -> str:
    """Header premium com ícone em card vermelho."""
    sub = (
        f"<p style='margin:5px 0 0;color:#64748B;font-size:14px;font-weight:400'>{subtitle}</p>"
        if subtitle else ""
    )
    return f"""
    <div style='display:flex;align-items:center;gap:16px;margin-bottom:8px;padding-bottom:20px;
                border-bottom:1px solid #E2E8F0'>
      <div style='width:52px;height:52px;background:#FEF2F2;border-radius:14px;
                  display:flex;align-items:center;justify-content:center;font-size:26px;
                  border:1px solid #FECACA;flex-shrink:0'>{icon}</div>
      <div>
        <h1 style='margin:0;font-size:22px;font-weight:800;color:#0F172A;letter-spacing:-0.3px'>{title}</h1>
        {sub}
      </div>
    </div>
    """


def section_title(text: str, margin_top: int = 24) -> str:
    """Título de seção pequeno e discreto."""
    return (
        f"<p style='font-size:11px;font-weight:700;text-transform:uppercase;"
        f"letter-spacing:1px;color:#94A3B8;margin:{margin_top}px 0 10px'>{text}</p>"
    )


# ─── CARDS ────────────────────────────────────────────────────────────────────

def card(content: str, padding: str = "20px 24px", extra_style: str = "") -> str:
    return (
        f"<div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;"
        f"padding:{padding};box-shadow:0 1px 3px rgba(15,23,42,0.04);{extra_style}'>"
        f"{content}</div>"
    )


def stat_card(label: str, value: str, color_key: str = "gray",
              icon: str = "", subtitle: str = "") -> str:
    """Card de métrica estilizado (para uso em st.markdown)."""
    c = COLORS.get(color_key, COLORS["gray"])
    sub = (
        f"<div style='font-size:11px;color:{c['text']};margin-top:4px;opacity:0.8'>{subtitle}</div>"
        if subtitle else ""
    )
    ico = f"<div style='font-size:20px;margin-bottom:8px'>{icon}</div>" if icon else ""
    return f"""
    <div style='background:{c['bg']};border:1px solid {c['border']};border-radius:12px;
                padding:18px 20px;text-align:center'>
      {ico}
      <div style='font-size:28px;font-weight:800;color:{c['text']};line-height:1'>{value}</div>
      <div style='font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;
                  color:{c['solid']};margin-top:6px;opacity:0.8'>{label}</div>
      {sub}
    </div>
    """


def pipeline_card(label: str, value: int, color: str) -> str:
    """Card de pipeline com número grande."""
    return f"""
    <div style='background:#FFFFFF;border:1px solid #E2E8F0;border-top:3px solid {color};
                border-radius:0 0 10px 10px;padding:16px;text-align:center;
                box-shadow:0 1px 3px rgba(15,23,42,0.04)'>
      <div style='font-size:32px;font-weight:800;color:{color};line-height:1'>{value}</div>
      <div style='font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;
                  color:#94A3B8;margin-top:6px'>{label}</div>
    </div>
    """


# ─── BADGES ──────────────────────────────────────────────────────────────────

def badge(text: str, color_key: str = "gray", size: str = "sm") -> str:
    c = COLORS.get(color_key, COLORS["gray"])
    pad = "2px 8px" if size == "sm" else "4px 12px"
    fs  = "10px" if size == "sm" else "12px"
    return (
        f"<span style='background:{c['bg']};color:{c['text']};border:1px solid {c['border']};"
        f"padding:{pad};border-radius:99px;font-size:{fs};font-weight:700;"
        f"letter-spacing:0.4px;text-transform:uppercase;white-space:nowrap'>{text}</span>"
    )


def status_dot(color: str) -> str:
    return f"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:{color};margin-right:6px'></span>"


# ─── AGENTES ─────────────────────────────────────────────────────────────────

def agent_response_card(agent_key: str, label: str, content: str) -> str:
    """Card para resposta de um agente especialista."""
    c = AGENT_COLORS.get(agent_key, AGENT_COLORS["moderador"])
    safe = content.replace("\n", "<br>") if content else "—"
    return f"""
    <div style='background:#FFFFFF;border:1px solid #E2E8F0;border-left:4px solid {c['solid']};
                border-radius:0 12px 12px 0;padding:18px 20px;margin-bottom:12px;
                box-shadow:0 1px 3px rgba(15,23,42,0.04)'>
      <div style='font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;
                  color:{c['solid']};margin-bottom:10px'>{label}</div>
      <div style='color:#374151;font-size:14px;line-height:1.7'>{safe}</div>
    </div>
    """


def tool_step(icon: str, label: str, state: str = "done", preview: str = "") -> str:
    """Linha de progresso de ferramenta do Diretor."""
    if state == "loading":
        bg, bc, tc = "#F8FAFC", "#E2E8F0", "#64748B"
        suffix = "<span style='color:#94A3B8;font-size:12px'>consultando...</span>"
    else:
        bg, bc, tc = "#F0FDF4", "#BBF7D0", "#166534"
        suffix = ""
    prev = (
        f"<div style='font-size:12px;color:#64748B;margin-top:4px;font-style:italic'>{preview[:180]}…</div>"
        if preview else ""
    )
    return f"""
    <div style='display:flex;align-items:flex-start;gap:10px;padding:10px 14px;
                background:{bg};border:1px solid {bc};border-radius:8px;margin-bottom:6px'>
      <span style='font-size:16px;flex-shrink:0'>{icon}</span>
      <div style='flex:1'>
        <span style='font-size:13px;font-weight:600;color:{tc}'>{label}</span>
        {' ' + suffix if suffix else ''}
        {prev}
      </div>
    </div>
    """


# ─── EMPTY STATES ─────────────────────────────────────────────────────────────

def empty_state(icon: str, title: str, subtitle: str = "") -> str:
    sub = (
        f"<p style='margin:6px 0 0;color:#94A3B8;font-size:13px'>{subtitle}</p>"
        if subtitle else ""
    )
    return f"""
    <div style='text-align:center;padding:48px 24px;background:#FAFAFA;
                border:1px dashed #E2E8F0;border-radius:12px;margin:8px 0'>
      <div style='font-size:36px;margin-bottom:12px'>{icon}</div>
      <p style='font-weight:600;color:#64748B;margin:0;font-size:15px'>{title}</p>
      {sub}
    </div>
    """


# ─── CAMPAIGN / CLIENT CARDS ──────────────────────────────────────────────────

def campaign_row(nome: str, ads_id: str, orcamento: str,
                 status: str, selected: bool = False) -> str:
    color = "#16A34A" if status == "ENABLED" else "#94A3B8"
    label = "Ativa" if status == "ENABLED" else (status or "—")
    borda = "#E53935" if selected else "#E2E8F0"
    return f"""
    <div style='background:#FFFFFF;border:1px solid {borda};border-radius:10px;
                padding:14px 18px;margin-bottom:8px;
                display:flex;align-items:center;justify-content:space-between'>
      <div>
        <div style='font-size:14px;font-weight:600;color:#0F172A'>{nome}</div>
        <div style='font-size:12px;color:#94A3B8;margin-top:2px'>
          ID: {ads_id or '—'} &nbsp;·&nbsp; R$ {orcamento or '—'}/dia
        </div>
      </div>
      <span style='background:{"#F0FDF4" if status=="ENABLED" else "#F8FAFC"};
                   color:{color};border:1px solid {"#BBF7D0" if status=="ENABLED" else "#E2E8F0"};
                   padding:3px 10px;border-radius:99px;font-size:11px;font-weight:700;
                   text-transform:uppercase'>{label}</span>
    </div>
    """


def client_row(nome: str, segmento: str, cidade: str,
               telefone: str, email: str, selected: bool = False) -> str:
    borda = "#E53935" if selected else "#E2E8F0"
    bg = "#FFFBFB" if selected else "#FFFFFF"
    sel_badge = badge("Selecionado", "red") if selected else ""
    return f"""
    <div style='background:{bg};border:1px solid {borda};border-radius:10px;
                padding:16px 20px;margin-bottom:8px'>
      <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:6px'>
        <span style='font-size:15px;font-weight:700;color:#0F172A'>{nome}</span>
        {sel_badge}
      </div>
      <div style='font-size:12px;color:#64748B'>
        {segmento or '—'} &nbsp;·&nbsp; {cidade or '—'}
        {'&nbsp;·&nbsp; ' + telefone if telefone else ''}
        {'&nbsp;·&nbsp; ' + email if email else ''}
      </div>
    </div>
    """
