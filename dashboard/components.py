"""
Design System — UnboundSales
Paleta dark com identidade visual da marca: cyan #00CFFD, fundo #0a0a0f.
"""

# ─── TOKENS ───────────────────────────────────────────────────────────────────

_BG    = "#0a0a0f"
_SURF  = "#0f1117"
_SURF2 = "#141920"
_CYAN  = "#00CFFD"
_CYAN2 = "#00b8e0"
_TEXT  = "#e2e8f0"
_TEXT2 = "#94a3b8"
_MUTED = "#3d5166"
_BORDER = "rgba(0,207,253,0.12)"
_BORDER2 = "rgba(255,255,255,0.07)"

COLORS = {
    "cyan":   {"bg": "rgba(0,207,253,0.08)",  "text": "#00CFFD", "border": "rgba(0,207,253,0.25)", "solid": "#00CFFD"},
    "green":  {"bg": "rgba(0,230,160,0.08)",  "text": "#00e6a0", "border": "rgba(0,230,160,0.25)", "solid": "#00e6a0"},
    "red":    {"bg": "rgba(239,68,68,0.08)",   "text": "#f87171", "border": "rgba(239,68,68,0.25)",  "solid": "#ef4444"},
    "amber":  {"bg": "rgba(251,191,36,0.08)",  "text": "#fbbf24", "border": "rgba(251,191,36,0.25)", "solid": "#f59e0b"},
    "blue":   {"bg": "rgba(59,130,246,0.08)",  "text": "#60a5fa", "border": "rgba(59,130,246,0.25)", "solid": "#3b82f6"},
    "purple": {"bg": "rgba(139,92,246,0.08)",  "text": "#a78bfa", "border": "rgba(139,92,246,0.25)", "solid": "#8b5cf6"},
    "orange": {"bg": "rgba(249,115,22,0.08)",  "text": "#fb923c", "border": "rgba(249,115,22,0.25)", "solid": "#f97316"},
    "gray":   {"bg": _SURF,                    "text": _TEXT2,    "border": _BORDER2,                "solid": _TEXT2},
}

AGENT_COLORS = {
    "lucas":     {"solid": "#3b82f6",  "glow": "rgba(59,130,246,0.20)"},
    "pedro":     {"solid": "#00CFFD",  "glow": "rgba(0,207,253,0.20)"},
    "rodrigo":   {"solid": "#00e6a0",  "glow": "rgba(0,230,160,0.20)"},
    "ana":       {"solid": "#a78bfa",  "glow": "rgba(139,92,246,0.20)"},
    "social":    {"solid": "#fb923c",  "glow": "rgba(249,115,22,0.20)"},
    "moderador": {"solid": "#e2e8f0",  "glow": "rgba(226,232,240,0.10)"},
}


# ─── HEADERS ─────────────────────────────────────────────────────────────────

def page_header(icon: str, title: str, subtitle: str = "") -> str:
    sub = (
        f"<p style='margin:5px 0 0;color:{_MUTED};font-size:14px;font-weight:400'>{subtitle}</p>"
        if subtitle else ""
    )
    return f"""
    <div style='display:flex;align-items:center;gap:16px;margin-bottom:8px;padding-bottom:20px;
                border-bottom:1px solid {_BORDER}'>
      <div style='width:50px;height:50px;background:rgba(0,207,253,0.08);border-radius:14px;
                  display:flex;align-items:center;justify-content:center;font-size:24px;
                  border:1px solid rgba(0,207,253,0.20);flex-shrink:0;
                  box-shadow:0 0 16px rgba(0,207,253,0.12)'>{icon}</div>
      <div>
        <h1 style='margin:0;font-size:22px;font-weight:800;color:{_TEXT};letter-spacing:-0.3px'>{title}</h1>
        {sub}
      </div>
    </div>
    """


def section_title(text: str, margin_top: int = 24) -> str:
    return (
        f"<p style='font-size:10px;font-weight:700;text-transform:uppercase;"
        f"letter-spacing:1.5px;color:{_MUTED};margin:{margin_top}px 0 10px'>{text}</p>"
    )


# ─── CARDS ────────────────────────────────────────────────────────────────────

def card(content: str, padding: str = "20px 24px", extra_style: str = "") -> str:
    return (
        f"<div style='background:{_SURF};border:1px solid {_BORDER2};border-radius:12px;"
        f"padding:{padding};{extra_style}'>"
        f"{content}</div>"
    )


def stat_card(label: str, value: str, color_key: str = "cyan",
              icon: str = "", subtitle: str = "") -> str:
    c = COLORS.get(color_key, COLORS["cyan"])
    sub = (
        f"<div style='font-size:11px;color:{c[\"text\"]};margin-top:4px;opacity:0.75'>{subtitle}</div>"
        if subtitle else ""
    )
    ico = f"<div style='font-size:20px;margin-bottom:8px'>{icon}</div>" if icon else ""
    return f"""
    <div style='background:{c["bg"]};border:1px solid {c["border"]};border-radius:12px;
                padding:18px 20px;text-align:center'>
      {ico}
      <div style='font-size:28px;font-weight:800;color:{c["text"]};line-height:1'>{value}</div>
      <div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;
                  color:{c["solid"]};margin-top:6px;opacity:0.85'>{label}</div>
      {sub}
    </div>
    """


def pipeline_card(label: str, value: int, color: str) -> str:
    return f"""
    <div style='background:{_SURF};border:1px solid {_BORDER2};border-top:2px solid {color};
                border-radius:0 0 10px 10px;padding:16px;text-align:center;
                box-shadow:0 0 20px rgba(0,0,0,0.3)'>
      <div style='font-size:32px;font-weight:800;color:{color};line-height:1;
                  text-shadow:0 0 12px {color}80'>{value}</div>
      <div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;
                  color:{_MUTED};margin-top:6px'>{label}</div>
    </div>
    """


# ─── BADGES ──────────────────────────────────────────────────────────────────

def badge(text: str, color_key: str = "gray", size: str = "sm") -> str:
    c = COLORS.get(color_key, COLORS["gray"])
    pad = "2px 8px" if size == "sm" else "4px 12px"
    fs  = "10px" if size == "sm" else "12px"
    return (
        f"<span style='background:{c[\"bg\"]};color:{c[\"text\"]};border:1px solid {c[\"border\"]};"
        f"padding:{pad};border-radius:99px;font-size:{fs};font-weight:700;"
        f"letter-spacing:0.4px;text-transform:uppercase;white-space:nowrap'>{text}</span>"
    )


def status_dot(color: str) -> str:
    return (
        f"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;"
        f"background:{color};box-shadow:0 0 6px {color};margin-right:6px'></span>"
    )


# ─── AGENTES ─────────────────────────────────────────────────────────────────

def agent_response_card(agent_key: str, label: str, content: str) -> str:
    c = AGENT_COLORS.get(agent_key, AGENT_COLORS["moderador"])
    safe = content.replace("\n", "<br>") if content else "—"
    return f"""
    <div style='background:{_SURF};border:1px solid {_BORDER2};
                border-left:3px solid {c["solid"]};
                border-radius:0 12px 12px 0;padding:18px 20px;margin-bottom:12px;
                box-shadow:0 0 20px {c["glow"]}'>
      <div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;
                  color:{c["solid"]};margin-bottom:10px;
                  text-shadow:0 0 8px {c["solid"]}80'>{label}</div>
      <div style='color:{_TEXT2};font-size:14px;line-height:1.75'>{safe}</div>
    </div>
    """


def tool_step(icon: str, label: str, state: str = "done", preview: str = "") -> str:
    if state == "loading":
        bg  = "rgba(0,207,253,0.05)"
        bc  = "rgba(0,207,253,0.20)"
        tc  = _CYAN
        suffix = "<span style='color:#3d5166;font-size:12px;margin-left:6px'>consultando…</span>"
    else:
        bg  = "rgba(0,230,160,0.05)"
        bc  = "rgba(0,230,160,0.20)"
        tc  = "#00e6a0"
        suffix = ""
    prev = (
        f"<div style='font-size:12px;color:{_MUTED};margin-top:4px;font-style:italic'>{preview[:180]}…</div>"
        if preview else ""
    )
    return f"""
    <div style='display:flex;align-items:flex-start;gap:10px;padding:10px 14px;
                background:{bg};border:1px solid {bc};border-radius:8px;margin-bottom:6px'>
      <span style='font-size:15px;flex-shrink:0'>{icon}</span>
      <div style='flex:1'>
        <span style='font-size:13px;font-weight:600;color:{tc}'>{label}</span>
        {suffix}
        {prev}
      </div>
    </div>
    """


# ─── EMPTY STATES ─────────────────────────────────────────────────────────────

def empty_state(icon: str, title: str, subtitle: str = "") -> str:
    sub = (
        f"<p style='margin:6px 0 0;color:{_MUTED};font-size:13px'>{subtitle}</p>"
        if subtitle else ""
    )
    return f"""
    <div style='text-align:center;padding:48px 24px;
                background:{_SURF};border:1px dashed rgba(0,207,253,0.15);
                border-radius:12px;margin:8px 0'>
      <div style='font-size:36px;margin-bottom:12px'>{icon}</div>
      <p style='font-weight:600;color:{_TEXT2};margin:0;font-size:15px'>{title}</p>
      {sub}
    </div>
    """


# ─── CAMPAIGN / CLIENT CARDS ──────────────────────────────────────────────────

def campaign_row(nome: str, ads_id: str, orcamento: str,
                 status: str, selected: bool = False) -> str:
    color  = "#00e6a0" if status == "ENABLED" else _MUTED
    label  = "Ativa" if status == "ENABLED" else (status or "—")
    borda  = _CYAN if selected else _BORDER2
    glow   = f"box-shadow:0 0 16px rgba(0,207,253,0.12);" if selected else ""
    return f"""
    <div style='background:{_SURF};border:1px solid {borda};border-radius:10px;
                padding:14px 18px;margin-bottom:8px;{glow}
                display:flex;align-items:center;justify-content:space-between'>
      <div>
        <div style='font-size:14px;font-weight:600;color:{_TEXT}'>{nome}</div>
        <div style='font-size:12px;color:{_MUTED};margin-top:2px'>
          ID: {ads_id or "—"} &nbsp;·&nbsp; R$ {orcamento or "—"}/dia
        </div>
      </div>
      <span style='background:{"rgba(0,230,160,0.10)" if status=="ENABLED" else _SURF};
                   color:{color};border:1px solid {"rgba(0,230,160,0.25)" if status=="ENABLED" else _BORDER2};
                   padding:3px 10px;border-radius:99px;font-size:10px;font-weight:700;
                   text-transform:uppercase'>{label}</span>
    </div>
    """


def client_row(nome: str, segmento: str, cidade: str,
               telefone: str, email: str, selected: bool = False) -> str:
    borda = _CYAN if selected else _BORDER2
    bg    = "rgba(0,207,253,0.04)" if selected else _SURF
    sel_badge = badge("Selecionado", "cyan") if selected else ""
    return f"""
    <div style='background:{bg};border:1px solid {borda};border-radius:10px;
                padding:16px 20px;margin-bottom:8px'>
      <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:6px'>
        <span style='font-size:15px;font-weight:700;color:{_TEXT}'>{nome}</span>
        {sel_badge}
      </div>
      <div style='font-size:12px;color:{_MUTED}'>
        {segmento or "—"} &nbsp;·&nbsp; {cidade or "—"}
        {"&nbsp;·&nbsp; " + telefone if telefone else ""}
        {"&nbsp;·&nbsp; " + email if email else ""}
      </div>
    </div>
    """
