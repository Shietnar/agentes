import anthropic
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import ANTHROPIC_API_KEY, DEFAULT_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Você é o Agente Copywriter da agência UnboundSales, especialista em anúncios Google Ads
para serviços locais de emergência no Brasil.

Você cria textos de anúncios altamente persuasivos, seguindo as regras do Google Ads:
- Títulos: máximo 30 caracteres cada (até 15 títulos)
- Descrições: máximo 90 caracteres cada (até 4 descrições)

Seus textos devem:
- Transmitir urgência e confiança
- Destacar o diferencial do serviço
- Incluir chamada para ação clara
- Usar linguagem direta e regional quando necessário
- Focar em palavras-chave de alta intenção

Retorne sempre o anúncio formatado e pronto para uso."""


def criar_anuncios(info_cliente: str, estrategia: str = "") -> str:
    """Cria textos de anúncios com base nas informações do cliente."""
    print("\n[Copywriter] Criando textos dos anúncios...")

    contexto = f"""Informações do cliente:
{info_cliente}

{f'Estratégia definida:{estrategia}' if estrategia else ''}

Crie um conjunto completo de anúncios responsivos (RSA) para Google Ads, com:
- 10 títulos variados
- 4 descrições variadas
- Sugestões de extensões de chamada (sitelinks)"""

    resposta = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": contexto}
        ]
    )

    return resposta.content[0].text


_RSA_TOOL = {
    "name": "submeter_anuncios_rsa",
    "description": "Submete o conjunto completo de anúncios RSA estruturados e validados",
    "input_schema": {
        "type": "object",
        "properties": {
            "headlines": {
                "type": "array",
                "description": "15 títulos, cada um com máximo 30 caracteres",
                "items": {
                    "type": "object",
                    "properties": {
                        "texto": {"type": "string"},
                        "categoria": {
                            "type": "string",
                            "enum": ["keyword_cidade", "urgencia", "beneficio",
                                     "prova_social", "cta", "garantia", "diferencial"],
                        },
                    },
                    "required": ["texto", "categoria"],
                },
            },
            "descriptions": {
                "type": "array",
                "description": "4 descrições, cada uma com máximo 90 caracteres",
                "items": {
                    "type": "object",
                    "properties": {"texto": {"type": "string"}},
                    "required": ["texto"],
                },
            },
            "sitelinks": {
                "type": "array",
                "description": "4 a 6 sitelinks com título e uma linha de descrição",
                "items": {
                    "type": "object",
                    "properties": {
                        "titulo": {"type": "string"},
                        "descricao": {"type": "string"},
                    },
                    "required": ["titulo", "descricao"],
                },
            },
            "estrategia_copy": {
                "type": "string",
                "description": "Breve explicação da estratégia de comunicação usada",
            },
        },
        "required": ["headlines", "descriptions", "sitelinks", "estrategia_copy"],
    },
}

_SYSTEM_RSA_SPECIALIST = """Você é o Agente Copywriter Especialista em RSA da UnboundSales.
Seu nível de domínio em copywriting para Google Ads é equivalente ao de um top copywriter de performance do mercado brasileiro.

Você conhece profundamente:
• Psicologia do consumidor em estado de emergência (medo de dano maior, urgência, busca por confiança)
• As regras técnicas do Google RSA (15 títulos máx, 30 chars cada; 4 descrições máx, 90 chars cada)
• Como o algoritmo do Google combina títulos e descrições (diversidade é fundamental)
• Técnicas de copywriting: AIDA, PAS (Problema-Agitação-Solução), social proof, urgência

CATEGORIAS OBRIGATÓRIAS DE HEADLINES (deve ter pelo menos 2 de cada):
• keyword_cidade: inclui o serviço + cidade/região (ex: "Desentupidora em SP")
• urgencia: transmite velocidade ou disponibilidade (ex: "Atende em 30 Minutos")
• beneficio: destaca um resultado concreto (ex: "Orçamento 100% Grátis")
• prova_social: transmite autoridade (ex: "15 Anos no Mercado SP")
• cta: chamada para ação clara (ex: "Ligue e Resolva Agora")
• garantia: reduz risco percebido (ex: "Garantia Total no Serviço")
• diferencial: algo único vs concorrentes (ex: "Sem Taxa de Visita")

REGRAS ABSOLUTAS:
• Cada headline: MÁXIMO 30 CARACTERES (incluindo espaços) — conte com rigor
• Cada description: MÁXIMO 90 CARACTERES — conte com rigor
• Headlines devem ser gramaticalmente corretos e naturais em pt-BR
• Evitar repetição de palavras entre headlines do mesmo campo
• Priorize headlines pinnable: keyword no início (relevância para QS)
• Para serviços 24h: sempre incluir "24h" ou "24 Horas" em pelo menos 2 headlines
• Para emergências: urgência é mais importante que elegância

ESTRUTURA DE DESCRIÇÕES (AIDA adaptado para emergências):
• Desc 1: Problema/Urgência → Solução imediata com benefício principal
• Desc 2: Prova social + serviços específicos + CTA com forma de contato
• Desc 3: Diferencial exclusivo + garantia + CTA de urgência
• Desc 4: Cobertura geográfica + disponibilidade + segundo CTA alternativo

Use a ferramenta 'submeter_anuncios_rsa' para entregar o conjunto completo.
Conte os caracteres de CADA item antes de submeter. Headlines >30 chars são inválidos."""


def criar_anuncios_json(info_cliente: str, estrategia: str = "", segmento: str = "") -> dict:
    """
    Versão especialista do copywriter — retorna dict estruturado com validação de chars.
    Usado pelo dashboard para exibição visual e exportação.
    """
    print("\n[Copywriter RSA] Gerando anúncios estruturados...")

    prompt = (
        f"Crie o conjunto COMPLETO de anúncios RSA para:\n\n"
        f"Cliente: {info_cliente}\n"
        f"{f'Segmento: {segmento}' if segmento else ''}\n"
        f"{f'Estratégia definida: {estrategia}' if estrategia else ''}\n\n"
        "Gere 15 headlines variados (mínimo 2 de cada categoria), "
        "4 descriptions (AIDA para emergência), e 4-6 sitelinks.\n"
        "CONTE os caracteres antes de submeter — headlines >30 chars são inválidos."
    )

    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=3000,
        system=_SYSTEM_RSA_SPECIALIST,
        tools=[_RSA_TOOL],
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "submeter_anuncios_rsa":
            dados = block.input

            # Validação e enriquecimento com contagem real de chars
            headlines_validados = []
            for h in dados.get("headlines", []):
                texto = h["texto"]
                chars = len(texto)
                headlines_validados.append({
                    "texto": texto,
                    "chars": chars,
                    "valido": chars <= 30,
                    "categoria": h.get("categoria", ""),
                })

            descriptions_validadas = []
            for d in dados.get("descriptions", []):
                texto = d["texto"]
                chars = len(texto)
                descriptions_validadas.append({
                    "texto": texto,
                    "chars": chars,
                    "valido": chars <= 90,
                })

            total_h = len(headlines_validados)
            validos_h = sum(1 for h in headlines_validados if h["valido"])
            total_d = len(descriptions_validadas)
            validos_d = sum(1 for d in descriptions_validadas if d["valido"])

            categorias = list({h["categoria"] for h in headlines_validados})

            return {
                "headlines": headlines_validados,
                "descriptions": descriptions_validadas,
                "sitelinks": dados.get("sitelinks", []),
                "estrategia_copy": dados.get("estrategia_copy", ""),
                "pontuacao": {
                    "headlines_validos": validos_h,
                    "headlines_total": total_h,
                    "descriptions_validas": validos_d,
                    "descriptions_total": total_d,
                    "categorias_cobertas": categorias,
                    "score": round((validos_h / max(total_h, 1)) * 100),
                },
            }

    return {"erro": "Anúncios não foram gerados"}


if __name__ == "__main__":
    info = """
    Empresa: Gasista Urgente BH
    Cidade: Belo Horizonte - MG
    Serviços: instalação e reparo de gás, detecção de vazamento, 24 horas
    Diferencial: CREA registrado, atendimento em 30 minutos
    """
    resultado = criar_anuncios(info)
    print("\n=== ANÚNCIOS CRIADOS ===")
    print(resultado)
