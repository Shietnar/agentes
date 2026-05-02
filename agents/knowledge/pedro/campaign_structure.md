# Estrutura de Conta Google Ads — Serviços Locais de Emergência

## Princípio Fundamental (Pedro Sobral)

"Estruture sua conta pela intenção de busca do usuário, não pela sua organização interna."

Para serviços de emergência, existem 3 níveis de intenção:
1. **Emergência imediata:** "desentupidora agora", "chaveiro 24 horas", "gasista urgente" → maior intenção, maior CPC, maior CVR
2. **Pesquisa ativa:** "desentupidora preço", "melhor chaveiro sp", "gasista bairro X" → intenção média
3. **Informacional:** "como desentupir pia", "por que vaza gás", "chaveiro quanto custa" → baixa intenção, geralmente negativar

## Estrutura Ideal por Tipo de Serviço

### Campanha 1: Serviço Principal — Emergência (maior prioridade)
```
Campanha: [Serviço] — Urgência — [Cidade]
  Grupo 1: Termos de urgência explícita
    Keywords: "desentupidora urgente", "desentupimento emergência", "desentupidora 24h"
  Grupo 2: Serviço + localidade
    Keywords: "desentupidora [cidade]", "desentupimento [bairro]", "desentupidora perto"
```

### Campanha 2: Serviços Específicos
```
Campanha: [Serviço] — Tipos de Serviço
  Grupo 1: Esgoto/Cano
  Grupo 2: Pia/Cozinha
  Grupo 3: Banheiro/Vaso
  Grupo 4: Caixa de gordura
```

### Campanha 3: Marca (se houver histórico de busca)
```
Campanha: Marca — [Nome da Empresa]
  Keywords: nome da empresa + variações com erros ortográficos
  Lance: CPC Manual baixo (defesa de marca, CPCs naturalmente baixos)
```

## Regras de Estrutura

**Separar por serviço SEMPRE:**
- Desentupimento ≠ gasista ≠ chaveiro (intenções diferentes, CPAs diferentes, LPs diferentes)
- Uma campanha tentando fazer tudo vai ter QS baixo em tudo

**Match types para emergência local:**
- **Phrase match** como padrão — captura variações naturais
- **Exact match** para os 5–10 termos que mais gastam (controle total)
- **Broad match** apenas com Smart Bidding ativo e ≥ 100 conversões/mês — senão vira desperdício

**Segmentação geográfica:**
1. Comece pela cidade inteira
2. Após 90 dias: analise por bairro no relatório de localização
3. Crie ajustes de lance +20–40% para bairros com CPA melhor
4. Exclua bairros com CPA > 2x a meta após 30+ conversões nele

**Performance Max — NÃO para emergência local:**
- PMax mistura Display, YouTube, Discover, Gmail — canais onde o usuário em crise não está
- Você perde controle total sobre onde aparece
- Se o cliente insistir: configure sinais de audiência extremamente restritivos + exclua todos os canais menos Search
- Pedro Sobral recomenda: PMax só para e-commerce com catálogo de produtos, não para serviços

**DSA (Dynamic Search Ads) — cuidado:**
- Útil como campanha de suporte para capturar long tails não mapeados
- NUNCA como campanha principal
- Budget: máximo 10–15% do total de Search

## Orçamento: Como Distribuir

| Campanha | % do Budget | Justificativa |
|---|---|---|
| Emergência / Urgência | 60–70% | Maior intenção = maior CVR = melhor ROI |
| Serviços Específicos | 20–30% | Qualifica o lead antes da ligação |
| Marca | 5–10% | Defesa de marca, CPCs baixos |
| DSA | 0–10% | Descoberta de long tails |

## Erros de Estrutura Mais Comuns

1. **Um grupo de anúncios para tudo** — CTR baixo, QS baixo, CPC alto
2. **Misturar serviços na mesma campanha** — o algoritmo não consegue otimizar
3. **Broad match em conta nova** — budget vai para termos irrelevantes antes de ter negativos
4. **Sem separação urgência vs. informacional** — paga o mesmo CPC para quem quer contratar e quem só está pesquisando
5. **LP genérica para todos os grupos** — message match fraco = QS baixo mesmo com boa keyword
