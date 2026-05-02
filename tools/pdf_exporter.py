"""
PDF Exporter — UnboundSales
Gera relatórios PDF formatados a partir dos resultados dos agentes.
Usa fpdf2 (puro Python, sem dependências de sistema).
"""
from fpdf import FPDF
from datetime import datetime
import io
import re


# ─── TEMA ────────────────────────────────────────────────────────────────────

_AZUL      = (0,   207, 253)   # #00CFFD
_AZUL_ESC  = (10,  30,  50)    # fundo escuro
_CINZA_ESC = (30,  41,  59)    # slate-800
_CINZA_MED = (71,  85, 105)    # slate-600
_BRANCO    = (255, 255, 255)
_PRETO     = (15,  23,  42)    # quase preto
_VERDE     = (34, 197, 94)
_VERMELHO  = (239, 68,  68)
_AMARELO   = (245, 158, 11)


_UNICODE_MAP = {
    '—': '--', '–': '-', '‘': "'", '’': "'",
    '“': '"',  '”': '"', '•': '*',  '…': '...',
    'é': 'e',  'ã': 'a', 'ç': 'c',  'á': 'a',
    'ê': 'e',  'í': 'i', 'ó': 'o',  'ú': 'u',
    'â': 'a',  'ô': 'o', 'õ': 'o',  'ü': 'u',
    'É': 'E',  'Ã': 'A', 'Ç': 'C',  'Á': 'A',
    'Ê': 'E',  'Í': 'I', 'Ó': 'O',  'Ú': 'U',
    'Â': 'A',  'Ô': 'O', 'Õ': 'O',
    '→': '>',  '←': '<', '↑': '^',  '↓': 'v',
    '✔': '[X]', '✖': '[!]', '●': '*',
    '®': '(R)', '©': '(c)', '™': '(TM)',
    '°': 'o',  '·': '.',
}
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002700-\U000027BF"
    "\U000024C2-\U0001F251"
    "\U0001f926-\U0001f937"
    "\U00010000-\U0010ffff"
    "♀-♂"
    "☀-⭕"
    "‍⏏⏩⌚️〰"
    "]+", flags=re.UNICODE
)


def _strip(txt: str) -> str:
    """Remove markdown e normaliza para Latin-1 compatível com fpdf2/Helvetica."""
    if not txt:
        return ""
    txt = re.sub(r'\*\*(.+?)\*\*', r'\1', txt)
    txt = re.sub(r'\*(.+?)\*', r'\1', txt)
    txt = re.sub(r'#{1,6}\s*', '', txt)
    txt = re.sub(r'`(.+?)`', r'\1', txt)
    # Remove emojis
    txt = _EMOJI_RE.sub('', txt)
    # Substitui caracteres Unicode conhecidos
    for src, dst in _UNICODE_MAP.items():
        txt = txt.replace(src, dst)
    # Fallback: remove qualquer caractere fora do range latin-1
    txt = txt.encode('latin-1', errors='ignore').decode('latin-1')
    return txt.strip()


class RelatorioPDF(FPDF):
    """PDF com cabeçalho e rodapé padrão UnboundSales."""

    def __init__(self, cliente_nome: str, titulo_relatorio: str):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.cliente_nome = _strip(cliente_nome)
        self.titulo_relatorio = _strip(titulo_relatorio)
        self.data_str = datetime.now().strftime("%d/%m/%Y")
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 18, 18)

    def s(self, txt) -> str:
        """Normaliza qualquer string para Latin-1 antes de passar ao fpdf2."""
        return _strip(str(txt)) if txt else ""

    # Sobrescreve cell e multi_cell para sempre normalizar o texto
    def cell(self, *args, **kwargs):
        # Normaliza o parâmetro 'text' (3o posicional ou keyword)
        if len(args) >= 3:
            args = list(args)
            args[2] = _strip(str(args[2]))
            args = tuple(args)
        elif "text" in kwargs:
            kwargs["text"] = _strip(str(kwargs["text"]))
        elif "txt" in kwargs:
            kwargs["txt"] = _strip(str(kwargs["txt"]))
        return super().cell(*args, **kwargs)

    def multi_cell(self, *args, **kwargs):
        # Normaliza o parâmetro 'text' (3o posicional ou keyword)
        if len(args) >= 3:
            args = list(args)
            args[2] = _strip(str(args[2]))
            args = tuple(args)
        elif "text" in kwargs:
            kwargs["text"] = _strip(str(kwargs["text"]))
        elif "txt" in kwargs:
            kwargs["txt"] = _strip(str(kwargs["txt"]))
        return super().multi_cell(*args, **kwargs)

    def header(self):
        # Faixa azul escura no topo
        self.set_fill_color(*_AZUL_ESC)
        self.rect(0, 0, 210, 14, "F")
        # Logo texto
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*_AZUL)
        self.set_xy(10, 3)
        self.cell(30, 8, "Unbound", ln=0)
        self.set_text_color(*_BRANCO)
        self.cell(20, 8, "Sales", ln=0)
        # Título do relatório
        self.set_font("Helvetica", "", 9)
        self.set_text_color(180, 200, 220)
        self.set_xy(50, 3)
        self.cell(100, 8, self.titulo_relatorio, align="C", ln=0)
        # Data
        self.set_xy(150, 3)
        self.cell(50, 8, self.data_str, align="R", ln=0)
        self.ln(16)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*_CINZA_MED)
        rodape = f"Cliente: {self.cliente_nome}  |  UnboundSales IA  |  Pag. {self.page_no()}"
        self.cell(0, 6, rodape, align="C")

    def titulo_secao(self, texto: str, cor: tuple = _AZUL):
        """Título de seção com linha abaixo."""
        self.ln(3)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*cor)
        self.cell(0, 8, _strip(texto), ln=True)
        # Linha separadora fina
        self.set_draw_color(*cor)
        self.set_line_width(0.3)
        self.line(self.get_x(), self.get_y(), self.get_x() + 174, self.get_y())
        self.set_draw_color(0, 0, 0)
        self.ln(3)

    def texto_normal(self, texto: str, cor: tuple = _PRETO):
        """Parágrafo de texto normal com quebra automática."""
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*cor)
        self.multi_cell(0, 5.5, _strip(texto), ln=True)
        self.ln(1)

    def bullet(self, texto: str, cor_ponto: tuple = _AZUL, nivel: int = 0):
        """Item com bullet point."""
        indent = nivel * 8
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*cor_ponto)
        self.set_x(self.l_margin + indent)
        self.cell(5, 6, chr(149), ln=0)  # bullet •
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*_PRETO)
        self.multi_cell(0, 6, _strip(texto), ln=True)

    def badge_linha(self, badge_txt: str, badge_cor: tuple, titulo: str, corpo: str = ""):
        """Linha com badge colorido + título + corpo."""
        self.set_fill_color(*badge_cor)
        self.set_text_color(*_BRANCO)
        self.set_font("Helvetica", "B", 8)
        self.cell(22, 6, badge_txt, fill=True, ln=0,
                  align="C", border=0)
        self.set_text_color(*_PRETO)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 6, f"  {_strip(titulo)}", ln=True)
        if corpo:
            self.set_x(self.l_margin + 24)
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*_CINZA_MED)
            self.multi_cell(150, 5, _strip(corpo), ln=True)
        self.ln(1)

    def caixa_destaque(self, texto: str, cor_borda: tuple = _AZUL, cor_fundo: tuple = None):
        """Caixa com borda colorida para destaques."""
        if cor_fundo is None:
            cor_fundo = (240, 248, 255)
        self.set_fill_color(*cor_fundo)
        self.set_draw_color(*cor_borda)
        self.set_line_width(0.5)
        y_antes = self.get_y()
        self.rect(self.l_margin, y_antes, 174, 0)  # desenha só depois
        self.set_x(self.l_margin + 3)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*_PRETO)
        self.multi_cell(170, 5.5, _strip(texto), ln=True)
        y_depois = self.get_y() + 2
        self.rect(self.l_margin, y_antes - 1, 174, y_depois - y_antes + 2, "FD")
        self.set_y(y_depois + 2)

    def score_visual(self, score: int, maximo: int = 10):
        """Score numérico com barra de progresso colorida."""
        pct = score / maximo
        cor = _VERMELHO if score <= 4 else _AMARELO if score <= 6 else _VERDE
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(*cor)
        self.cell(20, 14, f"{score}", ln=0)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*_CINZA_MED)
        self.cell(8, 14, f"/{maximo}", ln=0)
        # Barra
        x, y = self.get_x() + 4, self.get_y() + 5
        w_total = 100
        self.set_fill_color(220, 220, 220)
        self.rect(x, y, w_total, 4, "F")
        self.set_fill_color(*cor)
        self.rect(x, y, w_total * pct, 4, "F")
        self.ln(16)

    def tabela(self, cabecalhos: list, linhas: list, col_widths: list = None):
        """Tabela simples com cabeçalho cinza escuro."""
        n = len(cabecalhos)
        if col_widths is None:
            col_widths = [174 // n] * n

        # Cabeçalho
        self.set_fill_color(*_CINZA_ESC)
        self.set_text_color(*_BRANCO)
        self.set_font("Helvetica", "B", 9)
        for i, cab in enumerate(cabecalhos):
            self.cell(col_widths[i], 7, cab, border=0, fill=True, ln=0, align="C")
        self.ln()

        # Linhas alternadas
        self.set_font("Helvetica", "", 9)
        for j, linha in enumerate(linhas):
            fill = j % 2 == 0
            self.set_fill_color(245, 248, 252) if fill else self.set_fill_color(255, 255, 255)
            self.set_text_color(*_PRETO)
            for i, cel in enumerate(linha):
                self.cell(col_widths[i], 6, str(cel)[:40], border=0, fill=True, ln=0)
            self.ln()
        self.ln(3)


# ─── GERADORES ESPECÍFICOS POR PÁGINA ─────────────────────────────────────────

def gerar_pdf_google_ads(analise: dict, dados: dict, cliente_nome: str) -> bytes:
    """Gera PDF do relatório de análise Google Ads."""
    pdf = RelatorioPDF(cliente_nome, "Análise Google Ads")
    pdf.add_page()

    # ── Capa / Score ──────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*_PRETO)
    pdf.cell(0, 10, f"Relatório Google Ads — {cliente_nome}", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*_CINZA_MED)
    camp_id = analise.get("campaign_id", "")
    pdf.cell(0, 7, f"Campanha: {camp_id}  |  {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(4)

    score = analise.get("score_campanha", 0)
    pdf.titulo_secao("Score da Campanha")
    pdf.score_visual(score)

    # ── Resumo executivo ──────────────────────────────────────────────────────
    pdf.titulo_secao("Diagnóstico Executivo")
    pdf.texto_normal(analise.get("resumo_executivo", ""))

    # ── Métricas ──────────────────────────────────────────────────────────────
    metricas = dados.get("metricas", {})
    if metricas and isinstance(metricas, dict) and "impressoes" in metricas:
        pdf.titulo_secao("Métricas (últimos 30 dias)")
        linhas = [[
            f"{metricas.get('impressoes', 0):,}",
            f"{metricas.get('cliques', 0):,}",
            f"{metricas.get('ctr_pct', 0):.1f}%",
            f"R$ {metricas.get('cpc_medio_brl', 0):.2f}",
            f"R$ {metricas.get('custo_total_brl', 0):.2f}",
            f"{metricas.get('conversoes', 0):.0f}",
        ]]
        pdf.tabela(
            ["Impressões", "Cliques", "CTR", "CPC médio", "Custo", "Conversões"],
            linhas,
            [30, 25, 22, 27, 35, 35],
        )

    # ── Problemas e pontos fortes ─────────────────────────────────────────────
    col1_items = analise.get("pontos_criticos", [])
    col2_items = analise.get("pontos_positivos", [])

    if col1_items:
        pdf.titulo_secao("Problemas Identificados", cor=_VERMELHO)
        for p in col1_items:
            pdf.bullet(p, cor_ponto=_VERMELHO)

    if col2_items:
        pdf.titulo_secao("Pontos Fortes", cor=_VERDE)
        for p in col2_items:
            pdf.bullet(p, cor_ponto=_VERDE)

    # ── Recomendações ─────────────────────────────────────────────────────────
    recomendacoes = analise.get("recomendacoes", [])
    if recomendacoes:
        pdf.titulo_secao("Recomendações e Ajustes Propostos")
        _BADGE_MAP = {
            "CRITICO":    ("CRÍTICO",    _VERMELHO),
            "IMPORTANTE": ("IMPORTANTE", _AMARELO),
            "MELHORIA":   ("MELHORIA",   _VERDE),
        }
        for rec in recomendacoes:
            badge_txt, badge_cor = _BADGE_MAP.get(rec.get("prioridade", ""), ("INFO", _CINZA_MED))
            corpo = rec.get("justificativa", "")
            if rec.get("impacto_esperado"):
                corpo += f"\nImpacto esperado: {rec['impacto_esperado']}"
            acao = rec.get("acao", "informativo")
            if acao and acao != "informativo":
                params = rec.get("parametros", {})
                if params:
                    import json as _json
                    corpo += f"\nAção: {acao} → {_json.dumps(params, ensure_ascii=False)}"
            pdf.badge_linha(badge_txt, badge_cor, rec.get("titulo", ""), corpo)

    # ── Keywords com QS baixo ─────────────────────────────────────────────────
    keywords = dados.get("keywords", [])
    kws_ruins = [k for k in keywords if isinstance(k, dict) and k.get("quality_score", 10) <= 6]
    if kws_ruins:
        pdf.titulo_secao("Keywords com Quality Score Baixo")
        linhas_kw = [
            [k.get("texto", "")[:35], k.get("match_type", ""),
             str(k.get("quality_score", "?")), f"R$ {k.get('custo_total_brl', 0):.2f}"]
            for k in kws_ruins[:20]
        ]
        pdf.tabela(["Keyword", "Match Type", "QS", "Custo"], linhas_kw, [75, 35, 20, 44])

    return bytes(pdf.output())


def gerar_pdf_estrategia(resultado: dict, cliente_nome: str, segmento: str = "") -> bytes:
    """Gera PDF do relatório de Estratégia de Negócio."""
    pdf = RelatorioPDF(cliente_nome, "Estratégia de Negócio")
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*_PRETO)
    pdf.cell(0, 10, f"Estratégia de Negócio — {cliente_nome}", ln=True)
    if segmento:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*_CINZA_MED)
        pdf.cell(0, 6, f"Segmento: {segmento}  |  {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(4)

    # Resumo
    pdf.titulo_secao("Resumo Executivo")
    pdf.texto_normal(resultado.get("resumo_executivo", ""))

    # Mercado
    m = resultado.get("analise_mercado", {})
    if m:
        pdf.titulo_secao("Análise de Mercado")
        pdf.texto_normal(m.get("tamanho_e_crescimento", ""))
        pdf.texto_normal(f"Concorrência: {m.get('nivel_concorrencia', '')}")
        saz = m.get("sazonalidade", {})
        if saz.get("observacao"):
            pdf.bullet(f"Sazonalidade: {saz['observacao']}")
        for t in m.get("tendencias", []):
            pdf.bullet(t)

    # Posicionamento
    pos = resultado.get("posicionamento", {})
    if pos:
        pdf.titulo_secao("Posicionamento")
        pdf.caixa_destaque(f"Proposta de Valor: {pos.get('uvp', '')}")
        pdf.bullet(f"Headline Google Ads: {pos.get('uvp_30_chars', '')}")
        pdf.bullet(f"Estratégia de Preço: {pos.get('estrategia_preco', '')}")
        pdf.bullet(f"Diferencial Principal: {pos.get('diferencial_principal', '')}")

    # Personas
    personas = resultado.get("personas", [])
    if personas:
        pdf.titulo_secao("Personas")
        for p in personas:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*_PRETO)
            pdf.cell(0, 7, f"{p.get('nome', '')} — {p.get('perfil', '')}", ln=True)
            for g in p.get("gatilhos_compra", []):
                pdf.bullet(f"Gatilho: {g}", cor_ponto=_VERDE, nivel=1)
            for o in p.get("objecoes", []):
                pdf.bullet(f"Objeção: {o}", cor_ponto=_VERMELHO, nivel=1)
            pdf.ln(2)

    # Canais
    canais = resultado.get("canais_atracao", [])
    if canais:
        pdf.titulo_secao("Canais de Atração")
        cor_map = {"alta": _VERMELHO, "média": _AMARELO, "baixa": _VERDE}
        for c in canais:
            pri = c.get("prioridade", "média").lower()
            cor = cor_map.get(pri, _CINZA_MED)
            pdf.badge_linha(
                c.get("prioridade", "").upper(), cor,
                c.get("canal", ""),
                c.get("estrategia", ""),
            )

    # Plano de ação
    pa = resultado.get("plano_acao", {})
    if pa:
        pdf.titulo_secao("Plano de Ação")
        for periodo, key, cor in [
            ("30 dias — Quick Wins", "dias_30", _VERDE),
            ("60 dias — Consolidação", "dias_60", _AMARELO),
            ("90 dias — Crescimento", "dias_90", _AZUL),
        ]:
            acoes = pa.get(key, [])
            if acoes:
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(*cor)
                pdf.cell(0, 7, periodo, ln=True)
                for a in acoes:
                    pdf.bullet(a, cor_ponto=cor, nivel=1)

    return bytes(pdf.output())


def gerar_pdf_copy(resultado: dict, cliente_nome: str, segmento: str = "") -> bytes:
    """Gera PDF dos anúncios RSA gerados pelo Copywriter."""
    pdf = RelatorioPDF(cliente_nome, "Anúncios RSA — Google Ads")
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*_PRETO)
    pdf.cell(0, 10, f"Anúncios RSA — {cliente_nome}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*_CINZA_MED)
    pdf.cell(0, 6, f"Segmento: {segmento}  |  {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(4)

    # Score
    pont = resultado.get("pontuacao", {})
    if pont:
        pdf.titulo_secao("Pontuação dos Anúncios")
        linhas = [[
            f"{pont.get('headlines_validos')}/{pont.get('headlines_total')}",
            f"{pont.get('descriptions_validas')}/{pont.get('descriptions_total')}",
            f"{pont.get('score', 0)}%",
            str(len(pont.get("categorias_cobertas", []))),
        ]]
        pdf.tabela(
            ["Headlines válidos", "Descrições válidas", "Diversidade", "Categorias"],
            linhas, [45, 45, 45, 39],
        )

    # Headlines
    pdf.titulo_secao("Headlines (máx. 30 chars)")
    for h in resultado.get("headlines", []):
        valido = h.get("valido", True)
        cor = _VERDE if valido else _VERMELHO
        chars = h.get("chars", len(h.get("texto", "")))
        pdf.badge_linha(
            f"{chars}/30", cor,
            h.get("texto", ""),
            h.get("categoria", ""),
        )

    # Descrições
    pdf.titulo_secao("Descrições (máx. 90 chars)")
    for i, d in enumerate(resultado.get("descriptions", [])):
        valido = d.get("valido", True)
        cor = _VERDE if valido else _VERMELHO
        chars = d.get("chars", len(d.get("texto", "")))
        pdf.badge_linha(
            f"Desc {i+1}", cor,
            d.get("texto", ""),
            f"{chars}/90 chars",
        )

    # Sitelinks
    sitelinks = resultado.get("sitelinks", [])
    if sitelinks:
        pdf.titulo_secao("Sitelinks")
        linhas_sl = [[sl.get("titulo", ""), sl.get("descricao", "")] for sl in sitelinks]
        pdf.tabela(["Título", "Descrição"], linhas_sl, [70, 104])

    # Estratégia
    estrategia = resultado.get("estrategia_copy", "")
    if estrategia:
        pdf.titulo_secao("Estratégia de Comunicação")
        pdf.texto_normal(estrategia)

    return bytes(pdf.output())


def gerar_pdf_relatorio_agente(titulo: str, conteudo_md: str, cliente_nome: str) -> bytes:
    """
    Gerador genérico: converte texto Markdown em PDF.
    Usado para Director, Team, Social e outros agentes que retornam texto livre.
    """
    pdf = RelatorioPDF(cliente_nome, titulo)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*_PRETO)
    pdf.cell(0, 10, f"{titulo} — {cliente_nome}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*_CINZA_MED)
    pdf.cell(0, 6, datetime.now().strftime("%d/%m/%Y %H:%M"), ln=True)
    pdf.ln(4)

    # Processa linha a linha o markdown
    for linha in conteudo_md.split("\n"):
        linha_strip = linha.strip()
        if not linha_strip:
            pdf.ln(2)
            continue
        if linha_strip.startswith("### "):
            pdf.titulo_secao(linha_strip[4:], cor=_CINZA_ESC)
        elif linha_strip.startswith("## "):
            pdf.titulo_secao(linha_strip[3:])
        elif linha_strip.startswith("# "):
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(*_PRETO)
            pdf.cell(0, 9, _strip(linha_strip[2:]), ln=True)
        elif linha_strip.startswith("- ") or linha_strip.startswith("• "):
            pdf.bullet(linha_strip[2:])
        elif linha_strip.startswith("**") and linha_strip.endswith("**"):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*_PRETO)
            pdf.cell(0, 6, _strip(linha_strip), ln=True)
        else:
            pdf.texto_normal(linha_strip)

    return bytes(pdf.output())
