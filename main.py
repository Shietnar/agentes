"""
UNBOUND SALES — Terminal de Controle
Sistema de agentes para agência de marketing digital
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import criar_tabelas, SessionLocal, Cliente, Campanha, Lead, StatusLead
from agents.orchestrator import (
    fluxo_novo_cliente,
    fluxo_relatorio_mensal,
    fluxo_relatorio_mensal_google_ads,
    exibir_resultado,
)
from agents.lead_agent import simular_atendimento
from config.settings import GOOGLE_ADS_LOGIN_CUSTOMER_ID


def limpar_tela():
    os.system("clear" if os.name == "posix" else "cls")


def cabecalho():
    print("""
╔══════════════════════════════════════════════╗
║         UNBOUND SALES — PAINEL DE IA         ║
║    Agência de Marketing com Agentes          ║
╚══════════════════════════════════════════════╝
""")


def menu_principal():
    print("""
  MENU PRINCIPAL
  ──────────────
  1. Cadastrar novo cliente
  2. Criar estratégia + anúncios para cliente
  3. Gerar relatório mensal de campanha
  4. Simular atendimento de lead (funcionário virtual)
  5. Listar clientes cadastrados

  ── Google Ads ──
  6. Listar campanhas no Google Ads
  7. Criar campanha no Google Ads para cliente
  8. Agente Especialista — análise e otimização completa
  0. Sair
""")


def cadastrar_cliente():
    print("\n=== CADASTRAR NOVO CLIENTE ===")
    nome = input("Nome da empresa: ").strip()
    segmento = input("Segmento (ex: desentupidora, gasista, chaveiro): ").strip()
    cidade = input("Cidade: ").strip()
    telefone = input("Telefone: ").strip()
    email = input("E-mail: ").strip()
    personalidade = input("Personalidade do atendente virtual (deixe em branco para padrão): ").strip()

    db = SessionLocal()
    cliente = Cliente(
        nome=nome,
        segmento=segmento,
        cidade=cidade,
        telefone=telefone,
        email=email,
        prompt_personalizado=personalidade or "simpático, profissional, direto ao ponto e ágil"
    )
    db.add(cliente)
    db.commit()
    print(f"\nCliente '{nome}' cadastrado com sucesso! ID: {cliente.id}")
    db.close()


def listar_clientes():
    db = SessionLocal()
    clientes = db.query(Cliente).all()
    db.close()

    if not clientes:
        print("\nNenhum cliente cadastrado ainda.")
        return None

    print("\n=== CLIENTES CADASTRADOS ===")
    for c in clientes:
        print(f"  [{c.id}] {c.nome} — {c.segmento} — {c.cidade}")

    return clientes


def selecionar_cliente():
    clientes = listar_clientes()
    if not clientes:
        return None

    try:
        cliente_id = int(input("\nDigite o ID do cliente: "))
        db = SessionLocal()
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        db.close()
        return cliente
    except ValueError:
        print("ID inválido.")
        return None


def menu_novo_cliente():
    cliente = selecionar_cliente()
    if not cliente:
        return

    print(f"\n=== BRIEFING PARA: {cliente.nome} ===")
    print("Descreva informações adicionais da campanha (orçamento, diferenciais, metas):")
    print("(Pressione Enter duas vezes para finalizar)\n")

    linhas = []
    while True:
        linha = input()
        if linha == "" and linhas and linhas[-1] == "":
            break
        linhas.append(linha)

    briefing = f"""
Cliente: {cliente.nome}
Segmento: {cliente.segmento}
Cidade: {cliente.cidade}
Informações adicionais:
{chr(10).join(linhas)}
"""

    resultado = fluxo_novo_cliente(briefing, cliente.nome)
    exibir_resultado(resultado)
    input("\nPressione Enter para voltar ao menu...")


def menu_relatorio():
    cliente = selecionar_cliente()
    if not cliente:
        return

    # Verifica se o cliente tem campanhas com google_ads_id cadastrado
    db = SessionLocal()
    campanhas_db = db.query(Campanha).filter(
        Campanha.cliente_id == cliente.id,
        Campanha.google_ads_id.isnot(None)
    ).all()
    db.close()

    usar_google_ads = False
    campaign_id = None

    if campanhas_db:
        print(f"\n=== CAMPANHAS GOOGLE ADS DE {cliente.nome} ===")
        for c in campanhas_db:
            print(f"  [{c.google_ads_id}] {c.nome}")
        resp = input("\nBuscar métricas reais do Google Ads? (s/N): ").strip().lower()
        if resp == "s":
            usar_google_ads = True
            campaign_id = input("ID da campanha Google Ads: ").strip()

    if usar_google_ads and campaign_id:
        dias_str = input("Período em dias (7/14/30) [padrão: 30]: ").strip()
        dias = int(dias_str) if dias_str in ("7", "14", "30") else 30
        customer_id = GOOGLE_ADS_LOGIN_CUSTOMER_ID or ""
        resultado = fluxo_relatorio_mensal_google_ads(customer_id, campaign_id, cliente.nome, dias)
    else:
        print(f"\n=== DADOS DA CAMPANHA: {cliente.nome} ===")
        print("Cole os dados da campanha (período, impressões, cliques, CTR, CPC, conversões, etc.):")
        print("(Pressione Enter duas vezes para finalizar)\n")

        linhas = []
        while True:
            linha = input()
            if linha == "" and linhas and linhas[-1] == "":
                break
            linhas.append(linha)

        dados = chr(10).join(linhas)
        resultado = fluxo_relatorio_mensal(dados, cliente.nome)

    exibir_resultado(resultado)
    input("\nPressione Enter para voltar ao menu...")


def menu_atendimento():
    cliente = selecionar_cliente()
    if not cliente:
        return

    simular_atendimento(cliente.id)
    input("\nPressione Enter para voltar ao menu...")


def menu_listar_campanhas_google_ads():
    from tools.google_ads import listar_campanhas
    from google.ads.googleads.errors import GoogleAdsException

    customer_id = input(
        f"\nCustomer ID [Enter para usar {GOOGLE_ADS_LOGIN_CUSTOMER_ID}]: "
    ).strip() or GOOGLE_ADS_LOGIN_CUSTOMER_ID

    print(f"\n[Google Ads] Buscando campanhas da conta {customer_id}...")
    try:
        campanhas = listar_campanhas(customer_id)
    except GoogleAdsException as e:
        print(f"\nErro na API Google Ads: {e.failure.errors[0].message}")
        return

    if not campanhas:
        print("Nenhuma campanha encontrada nesta conta.")
        return

    print(f"\n{'─'*70}")
    print(f"  {'ID':<15} {'Nome':<30} {'Status':<10} {'Custo (30d)'}")
    print(f"{'─'*70}")
    for c in campanhas:
        print(
            f"  {c['id']:<15} {c['nome'][:29]:<30} {c['status']:<10} "
            f"R$ {c['custo_total_brl']:.2f}"
        )
        print(
            f"  {'':15} Impressões: {c['impressoes']:,} | Cliques: {c['cliques']:,} | "
            f"CTR: {c['ctr_pct']}% | Conversões: {c['conversoes']:.0f}"
        )
        print(f"  {'':15}{'-'*54}")


def menu_criar_campanha_google_ads():
    from tools.google_ads import criar_campanha, criar_grupo_anuncios, adicionar_keywords
    from google.ads.googleads.errors import GoogleAdsException

    cliente = selecionar_cliente()
    if not cliente:
        return

    customer_id = input(
        f"\nCustomer ID [Enter para usar {GOOGLE_ADS_LOGIN_CUSTOMER_ID}]: "
    ).strip() or GOOGLE_ADS_LOGIN_CUSTOMER_ID

    print(f"\n=== CRIAR CAMPANHA GOOGLE ADS — {cliente.nome} ===")
    nome_camp = input("Nome da campanha: ").strip()
    if not nome_camp:
        print("Nome obrigatório.")
        return

    try:
        orcamento = float(input("Orçamento diário (R$): ").strip())
    except ValueError:
        print("Valor inválido.")
        return

    print("\n[1/3] Criando campanha...")
    try:
        campaign_resource = criar_campanha(customer_id, nome_camp, orcamento)
    except GoogleAdsException as e:
        print(f"\nErro ao criar campanha: {e.failure.errors[0].message}")
        return

    campaign_id = campaign_resource.split("/")[-1]

    print("[2/3] Criando grupo de anúncios principal...")
    nome_grupo = input(f"Nome do grupo de anúncios [padrão: '{nome_camp} - Principal']: ").strip()
    nome_grupo = nome_grupo or f"{nome_camp} - Principal"
    try:
        cpc_max = float(input("CPC máximo do grupo (R$) [padrão: 5.00]: ").strip() or "5")
    except ValueError:
        cpc_max = 5.0

    try:
        ag_resource = criar_grupo_anuncios(customer_id, campaign_resource, nome_grupo, cpc_max)
    except GoogleAdsException as e:
        print(f"\nErro ao criar grupo: {e.failure.errors[0].message}")
        return

    print("\n[3/3] Adicionar palavras-chave (opcional)")
    print("Cole uma por linha no formato: palavra|TIPO (ex: desentupidora sp|PHRASE)")
    print("Tipos: BROAD, PHRASE, EXACT. Deixe em branco e pressione Enter para pular.\n")

    palavras_chave = []
    while True:
        linha = input("Palavra-chave: ").strip()
        if not linha:
            break
        partes = linha.split("|")
        texto = partes[0].strip()
        tipo = partes[1].strip().upper() if len(partes) > 1 else "PHRASE"
        palavras_chave.append({"texto": texto, "tipo": tipo})

    if palavras_chave:
        try:
            adicionar_keywords(customer_id, ag_resource, palavras_chave)
        except GoogleAdsException as e:
            print(f"\nErro ao adicionar keywords: {e.failure.errors[0].message}")

    # Salva no banco de dados
    db = SessionLocal()
    campanha_db = Campanha(
        cliente_id=cliente.id,
        nome=nome_camp,
        google_ads_id=campaign_id,
        orcamento_diario=orcamento,
        status="PAUSED",
    )
    db.add(campanha_db)
    db.commit()
    db.close()

    print(f"""
✅ CAMPANHA CRIADA COM SUCESSO!

  Cliente:      {cliente.nome}
  Campanha:     {nome_camp}
  ID Google Ads: {campaign_id}
  Orçamento:    R$ {orcamento:.2f}/dia
  Status:       PAUSADA (ative após revisar)

  ➡  Acesse o Google Ads para adicionar anúncios RSA e ativar a campanha.
""")


def menu_agente_especialista():
    from agents.expert_agent import rodar_especialista
    from google.ads.googleads.errors import GoogleAdsException

    cliente = selecionar_cliente()
    if not cliente:
        return

    customer_id = input(
        f"\nCustomer ID [Enter para usar {GOOGLE_ADS_LOGIN_CUSTOMER_ID}]: "
    ).strip() or GOOGLE_ADS_LOGIN_CUSTOMER_ID

    # Verifica se há campanhas cadastradas no banco para o cliente
    db = SessionLocal()
    campanhas_db = db.query(Campanha).filter(
        Campanha.cliente_id == cliente.id,
        Campanha.google_ads_id.isnot(None)
    ).all()
    db.close()

    campaign_id = None
    if campanhas_db:
        print(f"\n  Campanhas cadastradas para {cliente.nome}:")
        for c in campanhas_db:
            print(f"    [{c.google_ads_id}] {c.nome}")
        campaign_id = input("\n  ID da campanha (ou informe outro): ").strip()
    else:
        campaign_id = input("\n  ID da campanha Google Ads: ").strip()

    if not campaign_id:
        print("  ID obrigatório.")
        return

    try:
        rodar_especialista(customer_id, campaign_id, cliente.nome)
    except GoogleAdsException as e:
        print(f"\n  Erro Google Ads: {e.failure.errors[0].message}")
    except KeyboardInterrupt:
        print("\n\n  Sessão interrompida pelo usuário.")


def main():
    # Garante que o banco está criado
    criar_tabelas()

    while True:
        limpar_tela()
        cabecalho()
        menu_principal()

        opcao = input("  Escolha uma opção: ").strip()

        if opcao == "1":
            cadastrar_cliente()
            input("\nPressione Enter para continuar...")
        elif opcao == "2":
            menu_novo_cliente()
        elif opcao == "3":
            menu_relatorio()
        elif opcao == "4":
            menu_atendimento()
        elif opcao == "5":
            listar_clientes()
            input("\nPressione Enter para continuar...")
        elif opcao == "6":
            menu_listar_campanhas_google_ads()
            input("\nPressione Enter para continuar...")
        elif opcao == "7":
            menu_criar_campanha_google_ads()
            input("\nPressione Enter para continuar...")
        elif opcao == "8":
            menu_agente_especialista()
            input("\nPressione Enter para continuar...")
        elif opcao == "0":
            print("\nAté logo!\n")
            sys.exit(0)
        else:
            print("Opção inválida. Tente novamente.")
            input("Pressione Enter para continuar...")


if __name__ == "__main__":
    main()
