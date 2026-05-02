"""
Integração com Google Ads API (Basic Access).
Funções para buscar métricas reais e criar campanhas, grupos, keywords e RSA ads.
"""
import os
import sys
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

YAML_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config",
    "google-ads.yaml",
)


def _conectar() -> GoogleAdsClient:
    return GoogleAdsClient.load_from_storage(path=YAML_PATH)


# ─── RELATÓRIOS ────────────────────────────────────────────────────────────────

def listar_contas_mcc(manager_customer_id: str) -> list:
    """
    Lista todas as contas de cliente (nível 1) acessíveis a partir da MCC.
    Retorna apenas contas ENABLED, ordenadas por nome.
    """
    client = _conectar()
    ga_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
            customer_client.client_customer,
            customer_client.descriptive_name,
            customer_client.currency_code,
            customer_client.status
        FROM customer_client
        WHERE customer_client.level = 1
    """

    contas = []
    for row in ga_service.search(customer_id=manager_customer_id, query=query):
        cid = row.customer_client.client_customer.split("/")[-1]
        nome = row.customer_client.descriptive_name or f"Conta {cid}"
        status = row.customer_client.status.name
        contas.append({
            "id": cid,
            "nome": nome,
            "moeda": row.customer_client.currency_code,
            "status": status,
        })
    return sorted([c for c in contas if c["status"] == "ENABLED"], key=lambda x: x["nome"])


def listar_campanhas(customer_id: str) -> list:
    """
    Lista todas as campanhas não removidas com métricas dos últimos 30 dias.
    Retorna lista de dicts ordenada por custo descendente.
    """
    client = _conectar()
    ga_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign_budget.amount_micros,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_micros,
            metrics.conversions
        FROM campaign
        WHERE segments.date DURING LAST_30_DAYS
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
    """

    response = ga_service.search(customer_id=customer_id, query=query)
    campanhas = []
    for row in response:
        campanhas.append({
            "id": str(row.campaign.id),
            "nome": row.campaign.name,
            "status": row.campaign.status.name,
            "orcamento_diario_brl": row.campaign_budget.amount_micros / 1_000_000,
            "impressoes": row.metrics.impressions,
            "cliques": row.metrics.clicks,
            "ctr_pct": round(row.metrics.ctr * 100, 2),
            "cpc_medio_brl": round(row.metrics.average_cpc / 1_000_000, 2),
            "custo_total_brl": round(row.metrics.cost_micros / 1_000_000, 2),
            "conversoes": row.metrics.conversions,
        })
    return campanhas


def obter_metricas_campanha(customer_id: str, campaign_id: str, dias: int = 30) -> dict:
    """
    Retorna métricas detalhadas de uma campanha específica para o agente analista.
    dias: 7, 14 ou 30.
    """
    client = _conectar()
    ga_service = client.get_service("GoogleAdsService")

    periodo_map = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS"}
    periodo = periodo_map.get(dias, "LAST_30_DAYS")

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_micros,
            metrics.conversions,
            metrics.search_impression_share,
            metrics.search_top_impression_share
        FROM campaign
        WHERE campaign.id = {campaign_id}
          AND segments.date DURING {periodo}
    """

    response = ga_service.search(customer_id=customer_id, query=query)
    for row in response:
        custo = row.metrics.cost_micros / 1_000_000
        conversoes = row.metrics.conversions
        cliques = row.metrics.clicks
        cpa = custo / conversoes if conversoes > 0 else 0.0
        cvr = (conversoes / cliques * 100) if cliques > 0 else 0.0
        return {
            "id": str(row.campaign.id),
            "nome": row.campaign.name,
            "status": row.campaign.status.name,
            "periodo_dias": dias,
            "impressoes": row.metrics.impressions,
            "cliques": cliques,
            "ctr_pct": round(row.metrics.ctr * 100, 2),
            "cpc_medio_brl": round(row.metrics.average_cpc / 1_000_000, 2),
            "custo_total_brl": round(custo, 2),
            "conversoes": conversoes,
            "taxa_conversao_pct": round(cvr, 2),
            "cpa_brl": round(cpa, 2),
            "parcela_impressoes_busca_pct": round(
                row.metrics.search_impression_share * 100, 2
            ),
            "parcela_impressoes_topo_pct": round(
                row.metrics.search_top_impression_share * 100, 2
            ),
        }
    return {}


# ─── CRIAÇÃO ────────────────────────────────────────────────────────────────────

def criar_campanha(
    customer_id: str,
    nome: str,
    orcamento_diario_brl: float,
) -> str:
    """
    Cria campanha de Pesquisa com status PAUSADA (para revisão antes de ativar).
    Retorna o resource_name da campanha criada (ex: customers/123/campaigns/456).
    """
    client = _conectar()

    # 1. Orçamento
    budget_service = client.get_service("CampaignBudgetService")
    budget_op = client.get_type("CampaignBudgetOperation")
    budget = budget_op.create
    budget.name = f"Orçamento - {nome}"
    budget.amount_micros = int(orcamento_diario_brl * 1_000_000)
    budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
    budget_resp = budget_service.mutate_campaign_budgets(
        customer_id=customer_id, operations=[budget_op]
    )
    budget_resource = budget_resp.results[0].resource_name

    # 2. Campanha
    campaign_service = client.get_service("CampaignService")
    campaign_op = client.get_type("CampaignOperation")
    camp = campaign_op.create
    camp.name = nome
    camp.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
    camp.status = client.enums.CampaignStatusEnum.PAUSED
    camp.campaign_budget = budget_resource
    camp.network_settings.target_google_search = True
    camp.network_settings.target_search_network = True
    camp.network_settings.target_content_network = False
    camp.network_settings.target_partner_search_network = False
    camp.manual_cpc.enhanced_cpc_enabled = True

    camp_resp = campaign_service.mutate_campaigns(
        customer_id=customer_id, operations=[campaign_op]
    )
    resource = camp_resp.results[0].resource_name
    campaign_id = resource.split("/")[-1]
    print(
        f"[Google Ads] Campanha '{nome}' criada — ID: {campaign_id} (status: PAUSADA para revisão)"
    )
    return resource


def criar_grupo_anuncios(
    customer_id: str,
    campaign_resource: str,
    nome: str,
    cpc_max_brl: float = 5.0,
) -> str:
    """Cria grupo de anúncios na campanha. Retorna resource_name do grupo."""
    client = _conectar()

    ag_service = client.get_service("AdGroupService")
    ag_op = client.get_type("AdGroupOperation")
    ag = ag_op.create
    ag.name = nome
    ag.campaign = campaign_resource
    ag.status = client.enums.AdGroupStatusEnum.ENABLED
    ag.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
    ag.cpc_bid_micros = int(cpc_max_brl * 1_000_000)

    resp = ag_service.mutate_ad_groups(customer_id=customer_id, operations=[ag_op])
    resource = resp.results[0].resource_name
    ad_group_id = resource.split("/")[-1]
    print(f"[Google Ads] Grupo '{nome}' criado — ID: {ad_group_id}")
    return resource


def adicionar_keywords(
    customer_id: str,
    ad_group_resource: str,
    palavras_chave: list,
) -> list:
    """
    Adiciona palavras-chave ao grupo de anúncios.
    palavras_chave: [{"texto": "desentupidora sp", "tipo": "BROAD|PHRASE|EXACT"}, ...]
    Retorna lista de resource_names criados.
    """
    client = _conectar()
    tipo_map = {
        "BROAD": client.enums.KeywordMatchTypeEnum.BROAD,
        "PHRASE": client.enums.KeywordMatchTypeEnum.PHRASE,
        "EXACT": client.enums.KeywordMatchTypeEnum.EXACT,
    }

    crit_service = client.get_service("AdGroupCriterionService")
    operations = []
    for kw in palavras_chave:
        op = client.get_type("AdGroupCriterionOperation")
        c = op.create
        c.ad_group = ad_group_resource
        c.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
        c.keyword.text = kw["texto"]
        c.keyword.match_type = tipo_map.get(
            kw.get("tipo", "PHRASE"), client.enums.KeywordMatchTypeEnum.PHRASE
        )
        operations.append(op)

    resp = crit_service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=operations
    )
    print(f"[Google Ads] {len(resp.results)} palavra(s)-chave adicionada(s)")
    return [r.resource_name for r in resp.results]


def criar_anuncio_rsa(
    customer_id: str,
    ad_group_resource: str,
    titulos: list,
    descricoes: list,
    url_final: str,
    path1: str = "",
    path2: str = "",
) -> str:
    """
    Cria Responsive Search Ad (RSA) no grupo de anúncios.
    titulos: 3–15 strings | descricoes: 2–4 strings.
    Retorna resource_name do anúncio criado.
    """
    client = _conectar()

    ad_service = client.get_service("AdGroupAdService")
    op = client.get_type("AdGroupAdOperation")
    aga = op.create
    aga.ad_group = ad_group_resource
    aga.status = client.enums.AdGroupAdStatusEnum.ENABLED

    ad = aga.ad
    ad.final_urls.append(url_final)
    if path1:
        ad.responsive_search_ad.path1 = path1
    if path2:
        ad.responsive_search_ad.path2 = path2

    for texto in titulos[:15]:
        headline = client.get_type("AdTextAsset")
        headline.text = texto
        ad.responsive_search_ad.headlines.append(headline)

    for texto in descricoes[:4]:
        desc = client.get_type("AdTextAsset")
        desc.text = texto
        ad.responsive_search_ad.descriptions.append(desc)

    resp = ad_service.mutate_ad_group_ads(customer_id=customer_id, operations=[op])
    resource = resp.results[0].resource_name
    print(f"[Google Ads] Anúncio RSA criado — {resource}")
    return resource


# ─── LEITURA AVANÇADA (para o agente especialista) ─────────────────────────────

def obter_dados_grupos(customer_id: str, campaign_id: str, dias: int = 30) -> list:
    """Retorna todos os grupos de anúncios da campanha com métricas e lance atual."""
    client = _conectar()
    ga_service = client.get_service("GoogleAdsService")
    periodo_map = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS"}
    periodo = periodo_map.get(dias, "LAST_30_DAYS")

    query = f"""
        SELECT
            ad_group.id,
            ad_group.name,
            ad_group.status,
            ad_group.cpc_bid_micros,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_micros,
            metrics.conversions
        FROM ad_group
        WHERE campaign.id = {campaign_id}
          AND segments.date DURING {periodo}
          AND ad_group.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
    """

    grupos = []
    for row in ga_service.search(customer_id=customer_id, query=query):
        custo = row.metrics.cost_micros / 1_000_000
        conv = row.metrics.conversions
        clicks = row.metrics.clicks
        cvr = (conv / clicks * 100) if clicks > 0 else 0.0
        grupos.append({
            "id": str(row.ad_group.id),
            "nome": row.ad_group.name,
            "status": row.ad_group.status.name,
            "cpc_max_brl": round(row.ad_group.cpc_bid_micros / 1_000_000, 2),
            "impressoes": row.metrics.impressions,
            "cliques": clicks,
            "ctr_pct": round(row.metrics.ctr * 100, 2),
            "cpc_medio_brl": round(row.metrics.average_cpc / 1_000_000, 2),
            "custo_total_brl": round(custo, 2),
            "conversoes": conv,
            "taxa_conversao_pct": round(cvr, 2),
            "cpa_brl": round(custo / conv, 2) if conv > 0 else None,
        })
    return grupos


def obter_dados_keywords(customer_id: str, campaign_id: str, dias: int = 30) -> list:
    """
    Retorna keywords com métricas de desempenho e Quality Score.
    Inclui: texto, tipo de correspondência, QS, componentes do QS, custo, conversões.
    """
    client = _conectar()
    ga_service = client.get_service("GoogleAdsService")
    periodo_map = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS"}
    periodo = periodo_map.get(dias, "LAST_30_DAYS")

    query = f"""
        SELECT
            ad_group_criterion.criterion_id,
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.status,
            ad_group_criterion.quality_info.quality_score,
            ad_group_criterion.quality_info.creative_quality_score,
            ad_group_criterion.quality_info.post_click_quality_score,
            ad_group_criterion.quality_info.search_predicted_ctr,
            ad_group.id,
            ad_group.name,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_micros,
            metrics.conversions
        FROM keyword_view
        WHERE campaign.id = {campaign_id}
          AND segments.date DURING {periodo}
          AND ad_group_criterion.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
        LIMIT 100
    """

    keywords = []
    for row in ga_service.search(customer_id=customer_id, query=query):
        custo = row.metrics.cost_micros / 1_000_000
        conv = row.metrics.conversions
        qi = row.ad_group_criterion.quality_info
        keywords.append({
            "criterion_id": str(row.ad_group_criterion.criterion_id),
            "ad_group_id": str(row.ad_group.id),
            "ad_group_nome": row.ad_group.name,
            "texto": row.ad_group_criterion.keyword.text,
            "match_type": row.ad_group_criterion.keyword.match_type.name,
            "status": row.ad_group_criterion.status.name,
            "quality_score": qi.quality_score,
            "qs_anuncio": qi.creative_quality_score.name,
            "qs_landing_page": qi.post_click_quality_score.name,
            "qs_ctr_esperado": qi.search_predicted_ctr.name,
            "impressoes": row.metrics.impressions,
            "cliques": row.metrics.clicks,
            "ctr_pct": round(row.metrics.ctr * 100, 2),
            "cpc_medio_brl": round(row.metrics.average_cpc / 1_000_000, 2),
            "custo_total_brl": round(custo, 2),
            "conversoes": conv,
            "cpa_brl": round(custo / conv, 2) if conv > 0 else None,
        })
    return keywords


def obter_search_terms(
    customer_id: str, campaign_id: str, dias: int = 30, limite: int = 150
) -> list:
    """
    Retorna os termos de busca reais que ativaram os anúncios.
    CRÍTICO para identificar desperdício (negativar) e oportunidades (novas keywords).
    """
    client = _conectar()
    ga_service = client.get_service("GoogleAdsService")
    periodo_map = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS"}
    periodo = periodo_map.get(dias, "LAST_30_DAYS")

    query = f"""
        SELECT
            search_term_view.search_term,
            search_term_view.status,
            ad_group.name,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.cost_micros,
            metrics.conversions
        FROM search_term_view
        WHERE campaign.id = {campaign_id}
          AND segments.date DURING {periodo}
        ORDER BY metrics.cost_micros DESC
        LIMIT {limite}
    """

    termos = []
    for row in ga_service.search(customer_id=customer_id, query=query):
        custo = row.metrics.cost_micros / 1_000_000
        conv = row.metrics.conversions
        termos.append({
            "termo": row.search_term_view.search_term,
            "status": row.search_term_view.status.name,
            "grupo": row.ad_group.name,
            "impressoes": row.metrics.impressions,
            "cliques": row.metrics.clicks,
            "ctr_pct": round(row.metrics.ctr * 100, 2),
            "custo_brl": round(custo, 2),
            "conversoes": conv,
            "cpa_brl": round(custo / conv, 2) if conv > 0 else None,
        })
    return termos


def obter_dados_anuncios(customer_id: str, campaign_id: str, dias: int = 30) -> list:
    """Retorna anúncios RSA com Ad Strength e métricas de desempenho."""
    client = _conectar()
    ga_service = client.get_service("GoogleAdsService")
    periodo_map = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS"}
    periodo = periodo_map.get(dias, "LAST_30_DAYS")

    query = f"""
        SELECT
            ad_group_ad.ad.id,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            ad_group_ad.ad_strength,
            ad_group_ad.status,
            ad_group.id,
            ad_group.name,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.cost_micros,
            metrics.conversions
        FROM ad_group_ad
        WHERE campaign.id = {campaign_id}
          AND segments.date DURING {periodo}
          AND ad_group_ad.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
        LIMIT 20
    """

    anuncios = []
    for row in ga_service.search(customer_id=customer_id, query=query):
        rsa = row.ad_group_ad.ad.responsive_search_ad
        headlines = [h.text for h in rsa.headlines]
        descriptions = [d.text for d in rsa.descriptions]
        custo = row.metrics.cost_micros / 1_000_000
        conv = row.metrics.conversions
        anuncios.append({
            "ad_id": str(row.ad_group_ad.ad.id),
            "ad_group_id": str(row.ad_group.id),
            "ad_group_nome": row.ad_group.name,
            "status": row.ad_group_ad.status.name,
            "ad_strength": row.ad_group_ad.ad_strength.name,
            "titulos": headlines,
            "descricoes": descriptions,
            "impressoes": row.metrics.impressions,
            "cliques": row.metrics.clicks,
            "ctr_pct": round(row.metrics.ctr * 100, 2),
            "custo_brl": round(custo, 2),
            "conversoes": conv,
            "cpa_brl": round(custo / conv, 2) if conv > 0 else None,
        })
    return anuncios


def obter_performance_dispositivos(
    customer_id: str, campaign_id: str, dias: int = 30
) -> list:
    """Breakdown de performance por dispositivo (MOBILE, DESKTOP, TABLET)."""
    client = _conectar()
    ga_service = client.get_service("GoogleAdsService")
    periodo_map = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS"}
    periodo = periodo_map.get(dias, "LAST_30_DAYS")

    query = f"""
        SELECT
            segments.device,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_micros,
            metrics.conversions
        FROM campaign
        WHERE campaign.id = {campaign_id}
          AND segments.date DURING {periodo}
    """

    dispositivos = []
    for row in ga_service.search(customer_id=customer_id, query=query):
        custo = row.metrics.cost_micros / 1_000_000
        conv = row.metrics.conversions
        clicks = row.metrics.clicks
        cvr = (conv / clicks * 100) if clicks > 0 else 0.0
        dispositivos.append({
            "dispositivo": row.segments.device.name,
            "impressoes": row.metrics.impressions,
            "cliques": clicks,
            "ctr_pct": round(row.metrics.ctr * 100, 2),
            "cpc_medio_brl": round(row.metrics.average_cpc / 1_000_000, 2),
            "custo_brl": round(custo, 2),
            "conversoes": conv,
            "taxa_conversao_pct": round(cvr, 2),
            "cpa_brl": round(custo / conv, 2) if conv > 0 else None,
        })
    return sorted(dispositivos, key=lambda x: x["custo_brl"], reverse=True)


def obter_performance_horarios(
    customer_id: str, campaign_id: str, dias: int = 30
) -> list:
    """Performance hora a hora (0–23). Útil para identificar horários rentáveis vs desperdício."""
    client = _conectar()
    ga_service = client.get_service("GoogleAdsService")
    periodo_map = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS"}
    periodo = periodo_map.get(dias, "LAST_30_DAYS")

    query = f"""
        SELECT
            segments.hour,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions
        FROM campaign
        WHERE campaign.id = {campaign_id}
          AND segments.date DURING {periodo}
        ORDER BY segments.hour
    """

    horarios = []
    for row in ga_service.search(customer_id=customer_id, query=query):
        custo = row.metrics.cost_micros / 1_000_000
        conv = row.metrics.conversions
        horarios.append({
            "hora": row.segments.hour,
            "impressoes": row.metrics.impressions,
            "cliques": row.metrics.clicks,
            "custo_brl": round(custo, 2),
            "conversoes": conv,
            "cpa_brl": round(custo / conv, 2) if conv > 0 else None,
        })
    return horarios


# ─── MUTAÇÕES (para o agente especialista) ─────────────────────────────────────

def atualizar_orcamento_campanha(
    customer_id: str, campaign_id: str, novo_orcamento_brl: float
) -> dict:
    """Atualiza o orçamento diário de uma campanha."""
    from google.protobuf import field_mask_pb2

    client = _conectar()
    ga_service = client.get_service("GoogleAdsService")

    # Busca resource name do orçamento
    query = f"""
        SELECT campaign.campaign_budget
        FROM campaign
        WHERE campaign.id = {campaign_id}
        LIMIT 1
    """
    budget_resource = None
    for row in ga_service.search(customer_id=customer_id, query=query):
        budget_resource = row.campaign.campaign_budget
        break

    if not budget_resource:
        return {"erro": "Campanha não encontrada"}

    budget_service = client.get_service("CampaignBudgetService")
    op = client.get_type("CampaignBudgetOperation")
    budget = op.update
    budget.resource_name = budget_resource
    budget.amount_micros = int(novo_orcamento_brl * 1_000_000)
    op._pb.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=["amount_micros"]))

    budget_service.mutate_campaign_budgets(customer_id=customer_id, operations=[op])
    return {"sucesso": True, "novo_orcamento_brl": novo_orcamento_brl}


def pausar_ativar_keyword(
    customer_id: str, ad_group_id: str, criterion_id: str, pausar: bool
) -> dict:
    """Pausa (pausar=True) ou ativa (pausar=False) uma keyword."""
    from google.protobuf import field_mask_pb2

    client = _conectar()
    resource_name = f"customers/{customer_id}/adGroupCriteria/{ad_group_id}~{criterion_id}"

    crit_service = client.get_service("AdGroupCriterionService")
    op = client.get_type("AdGroupCriterionOperation")
    c = op.update
    c.resource_name = resource_name
    c.status = (
        client.enums.AdGroupCriterionStatusEnum.PAUSED
        if pausar
        else client.enums.AdGroupCriterionStatusEnum.ENABLED
    )
    op._pb.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=["status"]))

    crit_service.mutate_ad_group_criteria(customer_id=customer_id, operations=[op])
    acao = "pausada" if pausar else "ativada"
    return {"sucesso": True, "keyword": f"{ad_group_id}~{criterion_id}", "status": acao}


def adicionar_keywords_negativas_campanha(
    customer_id: str, campaign_id: str, keywords: list
) -> dict:
    """
    Adiciona negativos em nível de campanha (broad negativo).
    keywords: lista de strings com os termos a negativar.
    """
    client = _conectar()
    campaign_resource = f"customers/{customer_id}/campaigns/{campaign_id}"

    crit_service = client.get_service("CampaignCriterionService")
    operations = []
    for kw_text in keywords:
        op = client.get_type("CampaignCriterionOperation")
        c = op.create
        c.campaign = campaign_resource
        c.negative = True
        c.keyword.text = kw_text
        c.keyword.match_type = client.enums.KeywordMatchTypeEnum.BROAD
        operations.append(op)

    resp = crit_service.mutate_campaign_criteria(
        customer_id=customer_id, operations=operations
    )
    return {"sucesso": True, "negativos_adicionados": len(resp.results)}


def atualizar_lance_grupo(
    customer_id: str, ad_group_id: str, novo_cpc_brl: float
) -> dict:
    """Atualiza o CPC máximo de um grupo de anúncios."""
    from google.protobuf import field_mask_pb2

    client = _conectar()
    resource_name = f"customers/{customer_id}/adGroups/{ad_group_id}"

    ag_service = client.get_service("AdGroupService")
    op = client.get_type("AdGroupOperation")
    ag = op.update
    ag.resource_name = resource_name
    ag.cpc_bid_micros = int(novo_cpc_brl * 1_000_000)
    op._pb.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=["cpc_bid_micros"]))

    ag_service.mutate_ad_groups(customer_id=customer_id, operations=[op])
    return {"sucesso": True, "ad_group_id": ad_group_id, "novo_cpc_brl": novo_cpc_brl}
