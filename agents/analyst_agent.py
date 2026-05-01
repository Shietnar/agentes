import anthropic
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import ANTHROPIC_API_KEY, DEFAULT_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Você é o Agente Analista de Métricas da agência UnboundSales.
Você analisa dados de campanhas Google Ads e transforma números em insights e recomendações claras.

Ao receber dados de uma campanha, você deve:
1. Avaliar o desempenho geral (bom / regular / ruim)
2. Identificar os pontos fortes da campanha
3. Identificar problemas e oportunidades
4. Dar recomendações prioritárias de otimização
5. Estimar impacto das mudanças sugeridas
6. Gerar um resumo executivo para o cliente (linguagem simples)

Métricas que você conhece: impressões, cliques, CTR, CPC médio, custo total,
conversões, taxa de conversão, CPA, ROAS, índice de qualidade, parcela de impressões."""


def analisar_campanha(dados_campanha: str) -> str:
    """Analisa os dados de uma campanha e retorna relatório com recomendações."""
    print("\n[Analista] Analisando dados da campanha...")

    resposta = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Analise os dados desta campanha:\n\n{dados_campanha}"}
        ]
    )

    return resposta.content[0].text


def gerar_relatorio_cliente(analise: str, nome_cliente: str) -> str:
    """Transforma a análise técnica em relatório simples para o cliente."""
    print("\n[Analista] Gerando relatório para o cliente...")

    resposta = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Com base nesta análise técnica, crie um relatório mensal
simples e visual (use emojis) para o cliente '{nome_cliente}'.
O relatório deve ser fácil de entender para quem não conhece Google Ads.

Análise técnica:
{analise}"""
            }
        ]
    )

    return resposta.content[0].text


def analisar_campanha_google_ads(customer_id: str, campaign_id: str, dias: int = 30) -> str:
    """Busca métricas reais do Google Ads e executa análise via IA."""
    from tools.google_ads import obter_metricas_campanha

    print(f"\n[Analista] Buscando métricas reais do Google Ads (últimos {dias} dias)...")
    m = obter_metricas_campanha(customer_id, campaign_id, dias)
    if not m:
        return "Não foi possível obter dados do Google Ads para esta campanha."

    dados = f"""
    Período: últimos {m['periodo_dias']} dias
    Campanha: {m['nome']}
    Status: {m['status']}
    Impressões: {m['impressoes']:,}
    Cliques: {m['cliques']:,}
    CTR: {m['ctr_pct']}%
    CPC médio: R$ {m['cpc_medio_brl']:.2f}
    Custo total: R$ {m['custo_total_brl']:.2f}
    Conversões: {m['conversoes']:.0f}
    Taxa de conversão: {m['taxa_conversao_pct']}%
    CPA: R$ {m['cpa_brl']:.2f}
    Parcela de impressões de busca: {m['parcela_impressoes_busca_pct']}%
    Parcela de impressões no topo: {m['parcela_impressoes_topo_pct']}%
    """

    return analisar_campanha(dados)


if __name__ == "__main__":
    dados_teste = """
    Período: últimos 30 dias
    Campanha: Desentupidora SP - Pesquisa
    Impressões: 4.520
    Cliques: 187
    CTR: 4,1%
    CPC médio: R$ 3,80
    Custo total: R$ 710,60
    Conversões (ligações): 23
    Taxa de conversão: 12,3%
    CPA: R$ 30,90
    """
    analise = analisar_campanha(dados_teste)
    print("\n=== ANÁLISE TÉCNICA ===")
    print(analise)

    relatorio = gerar_relatorio_cliente(analise, "Desentupidora Rápida SP")
    print("\n=== RELATÓRIO PARA O CLIENTE ===")
    print(relatorio)
