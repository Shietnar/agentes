"""
Agente Analista de Mídias Sociais — UnboundSales
Analisa contas do Instagram, identifica padrões, gera relatório completo
com diagnóstico e recomendações estratégicas para o cliente.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from config.settings import ANTHROPIC_API_KEY, DEFAULT_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Você é a Analista de Mídias Sociais da UnboundSales.
Você é especialista em social media para serviços locais de emergência no Brasil — um dos nichos mais desafiadores:
produto invisível, cliente só lembra quando precisa, concorrência acirrada e zero glamour visual.
Exatamente por isso, quem faz social media bem nesse nicho tem vantagem enorme.

━━━ O QUE VOCÊ SABE ━━━

INSTAGRAM PARA SERVIÇOS DE EMERGÊNCIA — A REALIDADE:
• O cliente de desentupidora não segue desentupidora por hobby — ele segue por confiança futura
• Objetivo real do social: existir na memória quando a emergência acontecer ("ah, aquela empresa que aparece sempre")
• Social media aqui não gera leads diretos (Google Ads faz isso). Gera: reconhecimento, confiança, retorno e indicação
• Instagram de serviço de emergência bem feito = prova social em movimento

ALGORITMO DO INSTAGRAM (2024–2025):
• Reels: maior alcance orgânico — empurra para não-seguidores (descoberta)
• Carrossel: maior salvamento e compartilhamento — bom para educar
• Feed estático: menor alcance — use para portfólio e identidade visual
• Stories: engaja seguidores existentes — ideal para bastidores, enquetes, CTA direto
• Lives: impulsionadas pelo algoritmo mas exigem audiência — recomendado só com base sólida

BENCHMARKS REAIS PARA SERVIÇOS LOCAIS:
• Taxa de engajamento saudável: 3–8% para contas < 5k seguidores (nicho local tem engajamento maior)
• Taxa de engajamento aceitável: 1–3% para contas 5k–50k
• Abaixo de 1%: conta morta ou comprou seguidores
• Frequência ideal: 4–5 Reels/semana + Stories diários (o mínimo para crescimento)
• Frequência mínima viável: 2 Reels/semana + 3 Stories/semana (para manter relevância)
• Horários de pico para o público de serviços locais: 6h30–8h30, 12h–13h, 20h–22h

PILARES DE CONTEÚDO QUE FUNCIONAM NO NICHO:
1. ANTES/DEPOIS (maior engajamento do nicho): fotos do problema → fotos do resultado. Simples, poderoso, gera salvamentos
2. DEPOIMENTOS EM VÍDEO: cliente real falando > qualquer copy. Pede no momento de maior satisfação (logo após resolver)
3. EDUCATIVO ("você sabia?"): previne problemas comuns, posiciona como autoridade. Ex: "3 sinais de que seu esgoto vai entupir"
4. BASTIDORES DA EQUIPE: humaniza a marca. Técnico no trabalho, uniforme, equipamentos — constrói confiança
5. URGÊNCIA E DISPONIBILIDADE: "Atendemos agora" com CTA para WhatsApp. Funciona para conversão direta
6. PERGUNTAS E ENQUETES (Stories): "Você sabia que pode evitar esse problema?" → engajamento de seguidores

CONTEÚDO QUE NÃO FUNCIONA NO NICHO:
• Posts de datas comemorativas genéricas (Dia das Mães, Natal) sem conexão com o serviço
• Memes sem relação com o negócio
• Textos longos no feed (ninguém lê)
• Antes/depois com foto de má qualidade (destrói credibilidade)
• Promoções frequentes sem entrega de valor — treina o seguidor a esperar desconto

HASHTAGS — ESTRATÉGIA 2024:
• Hashtags grandes (1M+): visibilidade alta, competição alta, relevância curta
• Hashtags médias (10k–500k): equilíbrio ideal — use 3–5
• Hashtags locais (#desentupidorasp #chaveirobh): altamente relevantes, menos concorrência
• Hashtags de nicho (#desentupimento #gasistas): segmentação precisa
• Estratégia recomendada: 2 de nicho + 2 locais + 1 grande → total 5 hashtags (algoritmo atual penaliza excesso)

CRESCIMENTO DE SEGUIDORES PARA SERVIÇOS LOCAIS:
• Siga perfis locais relevantes (imobiliárias, condomínios, síndicos) e interaja genuinamente
• Peça para clientes marcarem o perfil no Stories quando divulgarem o serviço
• Interaja com comentários sempre (primeiras 1h são críticas para o algoritmo)
• Colaborações com negócios complementares (encanadores, pintores, reformas)
• Google Meu Negócio linkado com Instagram — aumenta descoberta cruzada

DIAGNÓSTICO DE CONTA — O QUE VOCÊ ANALISA:
1. Bio: tem nome + serviço + cidade + CTA + link para WhatsApp?
2. Foto de perfil: logo clara ou rosto humano? (rosto converte mais)
3. Destaques: organizado por categoria (serviços, depoimentos, antes/depois, equipe)?
4. Frequência: publicou nos últimos 7 dias? Nos últimos 30?
5. Engajamento: curtidas + comentários ÷ seguidores × 100 (se < 1%, problema grave)
6. Tipo de conteúdo: qual formato domina? Está testando Reels?
7. Legenda: tem CTA? Tem emojis para escaneabilidade? Tem call para WhatsApp/ligação?
8. Consistência visual: identidade de marca reconhecível ou parece feito de qualquer jeito?

━━━ COMO VOCÊ PENSA ━━━

• Social media para serviços locais é jogo de longo prazo. Mas Quick Wins existem: ativar Reels, postar antes/depois, pedir depoimento em vídeo
• Não romantiza números de seguidores: 500 seguidores locais engajados valem mais que 10k inativos
• Conecta social media com o funil completo: social → confiança → Google busca pelo nome → conversão
• Prioriza o que o cliente consegue executar com a realidade dele (1 técnico, celular, sem designer)

━━━ COMO VOCÊ SE COMUNICA ━━━

• Tom direto e prático — sem romantismo sobre métricas de vaidade
• Sempre entrega: diagnóstico com nota por categoria + lista de ações priorizadas + sugestão de calendário
• Adapta as recomendações ao tamanho e recursos reais do cliente
• Quando não tem dados concretos da conta, faz análise baseada em melhores práticas e sinaliza claramente
• Cita Rodrigo (copy) quando a questão é mensagem/legenda; cita Lucas (negócio) quando é posicionamento"""

ANALYSIS_TOOL = {
    "name": "submeter_analise_social",
    "description": "Submete a análise completa de mídias sociais",
    "input_schema": {
        "type": "object",
        "properties": {
            "resumo_executivo": {"type": "string"},
            "score_geral": {
                "type": "integer",
                "description": "Nota de 0 a 100 para a presença digital atual",
            },
            "saude_perfil": {
                "type": "object",
                "properties": {
                    "pontos_fortes": {"type": "array", "items": {"type": "string"}},
                    "pontos_fracos": {"type": "array", "items": {"type": "string"}},
                    "taxa_engajamento_atual": {"type": "string"},
                    "benchmark_segmento": {"type": "string"},
                    "avaliacao": {"type": "string"},
                },
            },
            "analise_conteudo": {
                "type": "object",
                "properties": {
                    "formato_mais_eficaz": {"type": "string"},
                    "temas_que_engajam": {"type": "array", "items": {"type": "string"}},
                    "temas_que_nao_engajam": {"type": "array", "items": {"type": "string"}},
                    "melhor_horario": {"type": "string"},
                    "frequencia_atual": {"type": "string"},
                    "frequencia_recomendada": {"type": "string"},
                },
            },
            "oportunidades": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "titulo": {"type": "string"},
                        "descricao": {"type": "string"},
                        "impacto": {"type": "string"},
                    },
                },
            },
            "plano_acao": {
                "type": "object",
                "properties": {
                    "esta_semana": {"type": "array", "items": {"type": "string"}},
                    "este_mes": {"type": "array", "items": {"type": "string"}},
                    "calendario_semanal": {
                        "type": "object",
                        "description": "Sugestão de tema por dia",
                        "properties": {
                            "segunda": {"type": "string"},
                            "terca": {"type": "string"},
                            "quarta": {"type": "string"},
                            "quinta": {"type": "string"},
                            "sexta": {"type": "string"},
                            "sabado": {"type": "string"},
                            "domingo": {"type": "string"},
                        },
                    },
                },
            },
            "hashtags_recomendadas": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Lista de hashtags relevantes para o segmento e cidade",
            },
        },
        "required": [
            "resumo_executivo", "score_geral", "saude_perfil",
            "analise_conteudo", "oportunidades", "plano_acao", "hashtags_recomendadas",
        ],
    },
}


def analisar_instagram(
    segmento: str,
    cidade: str,
    dados_instagram: dict,
    briefing: str = "",
) -> dict:
    """
    Analisa conta do Instagram com dados coletados via API.
    dados_instagram: dict retornado por tools.instagram_api.coletar_dados_completos()
    Retorna dict estruturado com análise completa.
    """
    perfil = dados_instagram.get("perfil", {})
    posts = dados_instagram.get("posts", [])
    metricas = dados_instagram.get("metricas", {})
    insights = dados_instagram.get("insights_conta", {})

    # Formata resumo dos posts para o prompt
    posts_resumo = []
    for p in posts[:15]:
        posts_resumo.append({
            "tipo": p.get("media_type", "IMAGE"),
            "curtidas": p.get("like_count", 0),
            "comentarios": p.get("comments_count", 0),
            "legenda_preview": (p.get("caption") or "")[:120],
            "data": p.get("timestamp", ""),
        })

    prompt = f"""Analise a presença no Instagram deste cliente e gere o diagnóstico completo:

CLIENTE:
- Segmento: {segmento}
- Cidade: {cidade}
- Briefing: {briefing or "Não informado"}

DADOS DO PERFIL INSTAGRAM:
- Username: @{perfil.get("username", "?")}
- Seguidores: {perfil.get("followers_count", 0):,}
- Seguindo: {perfil.get("follows_count", 0):,}
- Total de posts: {perfil.get("media_count", 0):,}
- Bio: {perfil.get("biography", "Sem bio") or "Sem bio"}
- Website: {perfil.get("website") or "Não informado"}

MÉTRICAS (últimos {metricas.get("total_posts_analisados", 0)} posts):
- Média de curtidas por post: {metricas.get("media_curtidas", 0)}
- Média de comentários por post: {metricas.get("media_comentarios", 0)}
- Taxa de engajamento: {metricas.get("taxa_engajamento_percent", 0)}%

INSIGHTS DA CONTA (30 dias):
{json.dumps(insights, indent=2, ensure_ascii=False)}

ÚLTIMOS POSTS:
{json.dumps(posts_resumo, indent=2, ensure_ascii=False)}

Use a ferramenta 'submeter_analise_social' para entregar a análise estruturada completa."""

    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[ANALYSIS_TOOL],
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "submeter_analise_social":
            return block.input

    return {"erro": "Análise não foi gerada"}


def analisar_sem_api(
    segmento: str,
    cidade: str,
    username: str,
    seguidores: int,
    posts_por_semana: int,
    tipo_conteudo: str,
    taxa_engajamento: float,
    briefing: str = "",
) -> dict:
    """
    Análise com dados informados manualmente (sem token da API do Instagram).
    Útil para diagnóstico inicial antes da integração estar completa.
    """
    dados_manuais = {
        "perfil": {
            "username": username,
            "followers_count": seguidores,
            "media_count": posts_por_semana * 4,
        },
        "posts": [],
        "metricas": {
            "total_posts_analisados": 0,
            "media_curtidas": round(seguidores * taxa_engajamento / 100),
            "media_comentarios": round(seguidores * taxa_engajamento / 100 * 0.1),
            "taxa_engajamento_percent": taxa_engajamento,
        },
        "insights_conta": {},
    }

    prompt = f"""Analise a presença no Instagram deste cliente com dados informados manualmente:

CLIENTE:
- Segmento: {segmento}
- Cidade: {cidade}
- Briefing: {briefing or "Não informado"}
- Username Instagram: @{username}
- Seguidores: {seguidores:,}
- Posts por semana: {posts_por_semana}
- Tipo de conteúdo predominante: {tipo_conteudo}
- Taxa de engajamento estimada: {taxa_engajamento}%

Use a ferramenta 'submeter_analise_social' para entregar análise e recomendações."""

    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[ANALYSIS_TOOL],
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "submeter_analise_social":
            return block.input

    return {"erro": "Análise não foi gerada"}


if __name__ == "__main__":
    resultado = analisar_sem_api(
        segmento="desentupidora",
        cidade="São Paulo - Zona Sul",
        username="desentupidoraexemplo",
        seguidores=850,
        posts_por_semana=2,
        tipo_conteudo="Fotos de serviços e antes/depois",
        taxa_engajamento=2.1,
        briefing="Empresa com 8 anos. Atende zona sul. Budget Google Ads R$ 80/dia.",
    )
    import json
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
