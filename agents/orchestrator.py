"""
Orquestrador principal da UnboundSales.
Coordena todos os agentes e decide qual usar em cada situação.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.strategy_agent import criar_estrategia
from agents.copywriter_agent import criar_anuncios
from agents.analyst_agent import analisar_campanha, analisar_campanha_google_ads, gerar_relatorio_cliente


def fluxo_novo_cliente(briefing: str, nome_cliente: str) -> dict:
    """
    Fluxo completo para um novo cliente:
    1. Estrategista cria a estratégia
    2. Copywriter cria os anúncios
    Retorna tudo consolidado.
    """
    print(f"\n{'='*60}")
    print(f"  UNBOUND SALES — PROCESSANDO NOVO CLIENTE: {nome_cliente}")
    print(f"{'='*60}")

    estrategia = criar_estrategia(briefing)
    anuncios = criar_anuncios(briefing, estrategia)

    resultado = {
        "cliente": nome_cliente,
        "estrategia": estrategia,
        "anuncios": anuncios
    }

    print(f"\n{'='*60}")
    print(f"  CONCLUÍDO — {nome_cliente}")
    print(f"{'='*60}")

    return resultado


def fluxo_relatorio_mensal(dados_campanha: str, nome_cliente: str) -> dict:
    """
    Fluxo de análise mensal:
    1. Analista analisa os dados
    2. Gera relatório para o cliente
    """
    print(f"\n{'='*60}")
    print(f"  UNBOUND SALES — RELATÓRIO MENSAL: {nome_cliente}")
    print(f"{'='*60}")

    analise = analisar_campanha(dados_campanha)
    relatorio = gerar_relatorio_cliente(analise, nome_cliente)

    resultado = {
        "cliente": nome_cliente,
        "analise_tecnica": analise,
        "relatorio_cliente": relatorio
    }

    print(f"\n{'='*60}")
    print(f"  RELATÓRIO CONCLUÍDO — {nome_cliente}")
    print(f"{'='*60}")

    return resultado


def fluxo_relatorio_mensal_google_ads(
    customer_id: str,
    campaign_id: str,
    nome_cliente: str,
    dias: int = 30,
) -> dict:
    """
    Fluxo de análise mensal com dados reais do Google Ads.
    Busca métricas via API e gera análise + relatório para o cliente.
    """
    print(f"\n{'='*60}")
    print(f"  UNBOUND SALES — RELATÓRIO REAL (GOOGLE ADS): {nome_cliente}")
    print(f"{'='*60}")

    analise = analisar_campanha_google_ads(customer_id, campaign_id, dias)
    relatorio = gerar_relatorio_cliente(analise, nome_cliente)

    resultado = {
        "cliente": nome_cliente,
        "analise_tecnica": analise,
        "relatorio_cliente": relatorio,
    }

    print(f"\n{'='*60}")
    print(f"  RELATÓRIO CONCLUÍDO — {nome_cliente}")
    print(f"{'='*60}")

    return resultado


def exibir_resultado(resultado: dict):
    """Exibe os resultados de forma organizada no terminal."""
    for chave, valor in resultado.items():
        if chave == "cliente":
            continue
        print(f"\n{'─'*60}")
        print(f"  {chave.upper().replace('_', ' ')}")
        print(f"{'─'*60}")
        print(valor)
