import anthropic
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import ANTHROPIC_API_KEY, DEFAULT_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Você é o Agente Estrategista da agência UnboundSales.
Sua função é criar estratégias completas de Google Ads para empresas de serviços locais de emergência
(desentupidoras, gasistas, chaveiros, eletricistas, etc.).

Ao receber um briefing de cliente, você deve retornar:
1. Objetivo da campanha
2. Público-alvo ideal
3. Palavras-chave principais (com intenção de compra)
4. Palavras-chave negativas
5. Sugestão de orçamento diário
6. Estratégia de lances recomendada
7. Extensões de anúncio recomendadas
8. Tom e abordagem para os anúncios

Seja específico, prático e focado em conversões. Use dados e estimativas realistas para o mercado brasileiro."""


def criar_estrategia(briefing: str) -> str:
    """Recebe briefing do cliente e retorna estratégia completa."""
    print("\n[Estrategista] Analisando briefing e criando estratégia...")

    resposta = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": briefing}
        ]
    )

    return resposta.content[0].text


if __name__ == "__main__":
    briefing_teste = """
    Cliente: Desentupidora Rápida SP
    Cidade: São Paulo - SP
    Serviços: desentupimento de esgoto, pia, vaso sanitário, caixa de gordura
    Diferenciais: atendimento 24h, chegada em até 1h, orçamento grátis
    Orçamento disponível: R$ 50/dia
    """
    resultado = criar_estrategia(briefing_teste)
    print("\n=== ESTRATÉGIA GERADA ===")
    print(resultado)
