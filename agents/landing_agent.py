"""
Agente Especialista em Landing Pages — UnboundSales
Analisa LPs existentes (via URL) e gera novas LPs otimizadas para Google Ads.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from config.settings import ANTHROPIC_API_KEY, DEFAULT_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ─── SISTEMA PROMPT BASE ───────────────────────────────────────────────────────

SYSTEM_ANALISE = """Você é o Agente Especialista em Landing Pages da UnboundSales.
Você analisa landing pages de serviços locais de emergência com o rigor de um especialista em CRO (Conversion Rate Optimization) e Google Ads.

Você avalia 6 dimensões críticas para conversão em Google Ads:

1. RELEVÂNCIA DE PALAVRAS-CHAVE
   • Keyword principal está no <title>? No <h1>? Na meta description?
   • Há correspondência semântica com as queries de busca esperadas?
   • Densidades adequadas sem keyword stuffing?

2. CTA (Call-to-Action)
   • Existe botão/link de telefone com href="tel:" acima da dobra no mobile?
   • WhatsApp visível e funcional?
   • Formulário de captura presente?
   • CTAs têm urgência (Ligue Agora, Chame Já)?

3. ELEMENTOS DE CONFIANÇA (Trust Elements)
   • CNPJ ou registro profissional visível?
   • Certificações exibidas (CREA, CRBIO, etc.)?
   • Avaliações do Google ou depoimentos com nome/foto?
   • Anos de experiência ou número de clientes atendidos?
   • Garantia explícita?

4. MOBILE-READINESS
   • Meta viewport presente?
   • Texto legível em 375px sem zoom?
   • Botões com área de toque >= 48px?
   • Imagens responsivas?

5. VELOCIDADE PERCEBIDA
   • Fontes externas (Google Fonts, CDNs)?
   • Scripts de terceiros desnecessários?
   • Imagens muito pesadas (sem indicação de lazy loading)?

6. ESTRUTURA PERSUASIVA
   • Sequência lógica: Problema > Solução > Benefícios > Prova > CTA?
   • Hero section clara com proposta de valor imediata?
   • Prova social acima da dobra?
   • Senso de urgência ou escassez presente?

Use notas: A (ótimo), B (bom), C (atenção), D (problema sério), F (crítico/ausente)"""

SYSTEM_GERACAO = """Você é o Agente Especialista em Landing Pages da UnboundSales.
Sua tarefa é gerar um HTML COMPLETO e STANDALONE para uma landing page de serviço local de emergência.

REQUISITOS TÉCNICOS OBRIGATÓRIOS:
• HTML5 válido com <!DOCTYPE html>
• Meta viewport obrigatória: <meta name="viewport" content="width=device-width, initial-scale=1.0">
• Todo CSS inline no <style> — sem CDN externo, sem Google Fonts
• Fontes: system-ui, -apple-system, Arial, sans-serif (apenas system fonts)
• Todo JS inline no <script> — zero dependências externas
• Totalmente funcional offline (standalone)
• Mobile-first: layout em coluna por padrão, grid para desktop (min-width: 768px)

ESTRUTURA OBRIGATÓRIA (nesta ordem):
1. <head> com title (50-60 chars), meta description (120-155 chars), canonical, Open Graph básico
2. Header: logo/nome empresa + número de telefone grande + botão WhatsApp
3. Hero: H1 com keyword principal + subtítulo com benefício + dois CTAs (tel + WhatsApp)
4. Barra de confiança: ícones + texto (Atende 24h, Anos de experiência, Avaliação Google, Garantia)
5. Serviços: grid de cards com cada serviço oferecido
6. Por que nos escolher: 3-4 benefícios com ícones SVG inline
7. Área de cobertura: menção explícita à cidade e bairros/regiões
8. Depoimentos: mínimo 3 com nome, avaliação em estrelas e texto curto
9. CTA final: banner com fundo colorido, headline de urgência, botão grande de telefone
10. Formulário de contato simples: nome, telefone, mensagem, botão enviar (apenas frontend)
11. Footer: CNPJ, endereço, horário de atendimento, links de redes sociais (placeholder)

PADRÕES DE COPY PARA SERVIÇOS DE EMERGÊNCIA:
• H1 deve conter: Serviço + "em" + Cidade (ex: "Desentupidora em São Paulo")
• Subtítulo deve conter: urgência + benefício (ex: "Atendemos em até 1 hora • Orçamento Grátis")
• CTAs com texto de ação: "Ligar Agora", "Chamar no WhatsApp", "Solicitar Orçamento"
• Botão de telefone deve ser grande (min 56px altura) e ter cor contrastante
• Cor primária deve refletir o segmento: azul/verde para gasistas, laranja/vermelho para desentupidoras, amarelo/preto para chaveiros

IMPORTANTE: Retorne APENAS o HTML completo, sem texto antes ou depois. Comece com <!DOCTYPE html>."""

ANALYSIS_TOOL = {
    "name": "submeter_analise_lp",
    "description": "Submete a análise completa da landing page com notas por dimensão e recomendações",
    "input_schema": {
        "type": "object",
        "properties": {
            "nota_geral": {"type": "string", "enum": ["A", "B", "C", "D", "F"]},
            "score_percentual": {"type": "integer", "minimum": 0, "maximum": 100},
            "dimensoes": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "object",
                        "properties": {
                            "nota": {"type": "string"},
                            "obs": {"type": "string"},
                        },
                    },
                    "cta": {
                        "type": "object",
                        "properties": {
                            "nota": {"type": "string"},
                            "obs": {"type": "string"},
                        },
                    },
                    "trust_elements": {
                        "type": "object",
                        "properties": {
                            "nota": {"type": "string"},
                            "obs": {"type": "string"},
                        },
                    },
                    "mobile_readiness": {
                        "type": "object",
                        "properties": {
                            "nota": {"type": "string"},
                            "obs": {"type": "string"},
                        },
                    },
                    "velocidade_percebida": {
                        "type": "object",
                        "properties": {
                            "nota": {"type": "string"},
                            "obs": {"type": "string"},
                        },
                    },
                    "estrutura_persuasiva": {
                        "type": "object",
                        "properties": {
                            "nota": {"type": "string"},
                            "obs": {"type": "string"},
                        },
                    },
                },
            },
            "problemas_criticos": {"type": "array", "items": {"type": "string"}},
            "recomendacoes_priorizadas": {"type": "array", "items": {"type": "string"}},
            "pontos_positivos": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["nota_geral", "score_percentual", "dimensoes",
                     "problemas_criticos", "recomendacoes_priorizadas"],
    },
}


def analisar_landing_page(url: str) -> dict:
    """
    Busca a URL e analisa a landing page para Google Ads.
    Retorna dict com notas por dimensão, problemas e recomendações.
    """
    from tools.html_fetcher import fetch_html, extrair_metadados, extrair_texto_visivel

    print(f"\n[LP Analyst] Buscando {url}...")
    resultado_fetch = fetch_html(url)

    if "erro" in resultado_fetch:
        return {"erro": resultado_fetch["erro"]}

    html = resultado_fetch["html"]
    metadados = extrair_metadados(html)
    texto = extrair_texto_visivel(html)

    print("[LP Analyst] Analisando com IA...")

    prompt = (
        f"Analise esta landing page de serviço local de emergência.\n\n"
        f"URL: {url}\n"
        f"Status HTTP: {resultado_fetch['status_code']}\n\n"
        f"METADADOS EXTRAÍDOS:\n{json.dumps(metadados, ensure_ascii=False, indent=2)}\n\n"
        f"TEXTO VISÍVEL DA PÁGINA:\n{texto}\n\n"
        "Use a ferramenta 'submeter_analise_lp' com a análise completa."
    )

    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=3000,
        system=SYSTEM_ANALISE,
        tools=[ANALYSIS_TOOL],
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "submeter_analise_lp":
            return {"url": url, **block.input}

    return {"erro": "Análise não foi gerada"}


def gerar_landing_page_html(
    nome_empresa: str,
    segmento: str,
    cidade: str,
    telefone: str,
    telefone_whatsapp: str,
    servicos: list,
    diferenciais: list,
    anos_experiencia: int = None,
    cor_primaria: str = "#e53935",
    keywords_principais: list = None,
) -> str:
    """
    Gera HTML completo e standalone para uma landing page de serviço de emergência.
    Retorna a string HTML pronta para salvar e hospedar.
    """
    print("\n[LP Generator] Gerando landing page...")

    keywords_str = ", ".join(keywords_principais or [segmento, cidade])
    servicos_str = "\n".join(f"  - {s}" for s in servicos)
    diferenciais_str = "\n".join(f"  - {d}" for d in diferenciais)
    experiencia_str = f"{anos_experiencia} anos de experiência" if anos_experiencia else ""

    prompt = (
        f"Gere a landing page completa para:\n\n"
        f"Empresa: {nome_empresa}\n"
        f"Segmento: {segmento}\n"
        f"Cidade: {cidade}\n"
        f"Telefone: {telefone}\n"
        f"WhatsApp: {telefone_whatsapp}\n"
        f"Cor primária: {cor_primaria}\n"
        f"Keywords principais: {keywords_str}\n"
        f"{f'Experiência: {experiencia_str}' if experiencia_str else ''}\n\n"
        f"Serviços oferecidos:\n{servicos_str}\n\n"
        f"Diferenciais:\n{diferenciais_str}\n\n"
        "Gere o HTML completo seguindo todos os requisitos do sistema."
    )

    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=8096,
        system=SYSTEM_GERACAO,
        messages=[{"role": "user", "content": prompt}],
    )

    html = response.content[0].text.strip()

    # Validação básica
    if not html.startswith("<!DOCTYPE html>") and "<!DOCTYPE html>" in html:
        html = html[html.index("<!DOCTYPE html>"):]

    return html


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        url = sys.argv[1]
        resultado = analisar_landing_page(url)
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        html = gerar_landing_page_html(
            nome_empresa="Desentupidora Rápida SP",
            segmento="Desentupidora",
            cidade="São Paulo",
            telefone="(11) 9999-0000",
            telefone_whatsapp="5511999990000",
            servicos=["Desentupimento de esgoto", "Desentupimento de pia", "Caixa de gordura", "Vaso sanitário"],
            diferenciais=["Chega em até 1 hora", "Orçamento grátis", "Atendimento 24h", "Garantia no serviço"],
            anos_experiencia=12,
            cor_primaria="#e53935",
        )
        with open("/tmp/landing_page_test.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML gerado: {len(html)} chars. Salvo em /tmp/landing_page_test.html")
