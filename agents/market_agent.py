"""
Agente Especialista em Negócios e Mercado — UnboundSales
Analisa nicho, posicionamento, personas, pricing e estratégia de atração.
Foco: serviços locais de emergência no mercado brasileiro.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from config.settings import ANTHROPIC_API_KEY, DEFAULT_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Você é o Agente Especialista em Negócios e Mercado da UnboundSales.
Você combina profundo conhecimento de estratégia de negócios com expertise no mercado brasileiro de serviços locais de emergência.

Você domina as nuances de cada nicho:

🔧 DESENTUPIDORAS
• Sazonalidade: pico nas chuvas (Nov–Mar no Sudeste), alto volume em SP e RJ
• Ticket médio: R$ 180–600 dependendo do serviço (cano externo vs interno vs caixa de gordura)
• Decisão de compra: imediata, emocional, zero tolerância a demora ou preço opaco
• Concorrência desleal: muitos autônomos sem CNPJ que competem no preço mas falham na garantia
• Diferencial estratégico: tempo de chegada + garantia escrita + preço fixo (sem surpresas)

⛽ GASISTAS
• Sazonalidade: pico no inverno (Jun–Ago, aquecedores), mas emergências são constantes
• Ticket médio: R$ 200–1.500 (detecção de vazamento vs instalação completa)
• Alto gatilho de medo/segurança: o risco de explosão e CO são comunicações poderosas
• Certificação obrigatória: CREA/CRO em locais que o exigem — usar como diferencial de autoridade
• Decisão de compra: entre 5–20 min para emergência, mais lenta para instalação nova
• Personas: proprietários de imóvel com > 50 anos (resistentes a infomais), imobiliárias, condomínios

🔑 CHAVEIROS
• Alta concorrência e alto nível de fraude no mercado (golpes de preço após abertura)
• Ticket médio: R$ 80–350
• Decisão: imediata, 100% mobile, busca no momento da crise
• Diferencial estratégico: transparência de preço ANTES do atendimento + foto de credencial
• Risco: anúncios com preço muito baixo geram leads ruim; melhor qualificar pelo serviço

⚡ ELETRICISTAS
• Sazonalidade: pico no verão (ar-condicionado), mas demanda constante
• Ticket médio: R$ 150–800
• Persona primária: imóveis novos e reformas vs emergência (curto-circuito, queda de energia)
• Diferencial: CREA/ART para laudos, NBR-5410, garantia 1 ano nas instalações

🌿 OUTROS (dedetizadoras, vidraceiros, encanadores, pintores)
• Cada nicho tem suas próprias sazonalidades e personas — sempre pergunte antes de generalizar

━━━ SUA METODOLOGIA DE ANÁLISE ━━━

Para cada negócio, você produz:

1. ANÁLISE DE MERCADO
   • Tamanho estimado e crescimento do nicho na cidade/região
   • Sazonalidade com meses de pico e vale
   • Nível de concorrência e principais players
   • Tendências (crescimento de apps, marketplaces como GetNinjas)

2. PERSONAS DE COMPRA (mínimo 2)
   • Nome, idade, contexto
   • Gatilhos de compra: o que dispara a busca?
   • Objeções: o que impede a conversão?
   • O que os faz escolher um fornecedor vs outro?

3. POSICIONAMENTO E DIFERENCIAÇÃO
   • Proposta de valor única (UVP) adaptada ao contexto do cliente
   • Como comunicar diferencial em 30 caracteres (headline de Google Ads)
   • Posicionamento de preço: premium, intermediário ou popular?

4. ESTRATÉGIA DE PRICING
   • Preço como qualificador de lead vs como barreira
   • Psicologia do preço em emergência (preço fixo vs orçamento)
   • Tabela de preços visível no anúncio/LP: prós e contras para o segmento

5. CANAIS DE ATRAÇÃO
   • Google Ads: quais campanhas e tipos de campanha priorizar
   • Google Meu Negócio: importância e estratégia de avaliações
   • Marketplaces: GetNinjas, Habitissimo (quando entrar, quando evitar)
   • WhatsApp Business: qualificação e resposta rápida
   • SEO local: termos prioritários

6. PLANO DE AÇÃO (30/60/90 dias)
   • Ações imediatas (quick wins)
   • Ações de médio prazo (consolidação)
   • Ações de longo prazo (crescimento/expansão)

Seja específico, use dados reais do mercado brasileiro, e sempre adapte ao segmento e cidade do cliente."""

ANALYSIS_TOOL = {
    "name": "submeter_analise_mercado",
    "description": "Submete a análise de mercado completa e estruturada",
    "input_schema": {
        "type": "object",
        "properties": {
            "resumo_executivo": {"type": "string"},
            "analise_mercado": {
                "type": "object",
                "properties": {
                    "tamanho_e_crescimento": {"type": "string"},
                    "sazonalidade": {
                        "type": "object",
                        "properties": {
                            "meses_pico": {"type": "array", "items": {"type": "string"}},
                            "meses_vale": {"type": "array", "items": {"type": "string"}},
                            "observacao": {"type": "string"},
                        },
                    },
                    "nivel_concorrencia": {"type": "string"},
                    "tendencias": {"type": "array", "items": {"type": "string"}},
                },
            },
            "personas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "nome": {"type": "string"},
                        "perfil": {"type": "string"},
                        "gatilhos_compra": {"type": "array", "items": {"type": "string"}},
                        "objecoes": {"type": "array", "items": {"type": "string"}},
                        "criterio_decisao": {"type": "string"},
                    },
                },
            },
            "posicionamento": {
                "type": "object",
                "properties": {
                    "uvp": {"type": "string"},
                    "uvp_30_chars": {"type": "string"},
                    "estrategia_preco": {"type": "string"},
                    "diferencial_principal": {"type": "string"},
                },
            },
            "canais_atracao": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "canal": {"type": "string"},
                        "prioridade": {"type": "string"},
                        "estrategia": {"type": "string"},
                    },
                },
            },
            "plano_acao": {
                "type": "object",
                "properties": {
                    "dias_30": {"type": "array", "items": {"type": "string"}},
                    "dias_60": {"type": "array", "items": {"type": "string"}},
                    "dias_90": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "required": ["resumo_executivo", "analise_mercado", "personas", "posicionamento",
                     "canais_atracao", "plano_acao"],
    },
}


def analisar_mercado(segmento: str, cidade: str, briefing: str) -> dict:
    """
    Analisa mercado, nicho e estratégia de atração para o cliente.
    Retorna dict estruturado com análise completa.
    """
    prompt = (
        f"Analise o mercado e crie a estratégia de negócio completa para:\n\n"
        f"Segmento: {segmento}\n"
        f"Cidade/Região: {cidade}\n\n"
        f"Informações do cliente:\n{briefing}\n\n"
        f"Use a ferramenta 'submeter_analise_mercado' para entregar a análise estruturada."
    )

    print("\n[Negócios] Analisando mercado e estratégia...")

    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[ANALYSIS_TOOL],
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "submeter_analise_mercado":
            return block.input

    return {"erro": "Análise não foi gerada"}


def formatar_relatorio(analise: dict) -> str:
    """Converte o dict de análise para markdown legível no terminal."""
    if "erro" in analise:
        return f"Erro: {analise['erro']}"

    linhas = [
        f"# ANÁLISE DE MERCADO\n",
        f"## Resumo Executivo\n{analise.get('resumo_executivo', '')}\n",
    ]

    if "analise_mercado" in analise:
        m = analise["analise_mercado"]
        linhas.append("## Mercado")
        linhas.append(m.get("tamanho_e_crescimento", ""))
        saz = m.get("sazonalidade", {})
        if saz:
            linhas.append(f"\nSazonalidade: {saz.get('observacao', '')}")
            linhas.append(f"Picos: {', '.join(saz.get('meses_pico', []))}")
        linhas.append(f"\nConcorrência: {m.get('nivel_concorrencia', '')}\n")

    if "personas" in analise:
        linhas.append("## Personas")
        for p in analise["personas"]:
            linhas.append(f"\n**{p['nome']}** — {p['perfil']}")
            linhas.append(f"Gatilhos: {', '.join(p.get('gatilhos_compra', []))}")
            linhas.append(f"Decisão: {p.get('criterio_decisao', '')}")

    if "posicionamento" in analise:
        pos = analise["posicionamento"]
        linhas.append(f"\n## Posicionamento")
        linhas.append(f"UVP: {pos.get('uvp', '')}")
        linhas.append(f"Headline (30 chars): {pos.get('uvp_30_chars', '')}")
        linhas.append(f"Preço: {pos.get('estrategia_preco', '')}")

    if "plano_acao" in analise:
        pa = analise["plano_acao"]
        linhas.append("\n## Plano de Ação")
        for d, acoes in [("30 dias", pa.get("dias_30", [])),
                          ("60 dias", pa.get("dias_60", [])),
                          ("90 dias", pa.get("dias_90", []))]:
            linhas.append(f"\n**{d}:**")
            for a in acoes:
                linhas.append(f"  • {a}")

    return "\n".join(linhas)


if __name__ == "__main__":
    resultado = analisar_mercado(
        segmento="desentupidora",
        cidade="São Paulo - SP",
        briefing="Empresa com 5 anos, 3 técnicos, atende zona sul e centro. Diferencial: chegada em 45 min. Orçamento Google Ads: R$ 60/dia.",
    )
    print(formatar_relatorio(resultado))
