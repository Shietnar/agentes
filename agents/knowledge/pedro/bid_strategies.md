# Estratégias de Lance — Metodologia Pedro Sobral

## A Escada de Automação

Pedro Sobral ensina uma progressão obrigatória. Pular etapas destrói o histórico de aprendizado do Google.

### Etapa 1 — CPC Manual
**Quando usar:** conta nova, estrutura nova, menos de 30 conversões/mês, depois de mudança estrutural grande.
**Por quê:** o algoritmo não tem dados suficientes para tomar decisões. Você guia manualmente.
**Como definir o CPC:**
- Fórmula: CPC máximo = CPA desejado × CVR estimada
- Exemplo: CPA desejado R$ 60, CVR estimada 15% → CPC máximo R$ 9,00
- Comece com 70% desse valor e suba conforme os dados chegam
**Duração mínima:** 30 dias ou 50 cliques por grupo de anúncios antes de qualquer ajuste significativo.
**Sinal para avançar:** ≥ 30 conversões no período, CPA estabilizando.

### Etapa 2 — Maximizar Conversões (sem meta de CPA)
**Quando usar:** ≥ 30 conversões/mês, histórico de 60+ dias com CPC Manual.
**Por quê:** o Google começa a aprender padrões reais de conversão sem a restrição de uma meta que ainda não faz sentido.
**Cuidado:** nos primeiros 7 dias pode gastar acima do orçamento planejado — monitore diariamente.
**Sinal de alerta:** CPA sobe mais de 40% vs. média do CPC Manual → volte uma etapa.
**Duração:** 30–60 dias para estabilização completa.
**Sinal para avançar:** CPA estável por 2 semanas, ≥ 50 conversões/mês.

### Etapa 3 — tCPA (Custo por Aquisição Desejado)
**Quando usar:** ≥ 50 conversões/mês consistentes, variação de CPA < 30%.
**Meta inicial:** defina 20–30% ACIMA do CPA real atual.
- Exemplo: CPA real R$ 45 → comece com tCPA R$ 57–60
- Nunca coloque uma meta abaixo do CPA atual — o algoritmo vai cortar impressões para "cumprir" a meta impossível
**Redução gradual:** máximo 10–15% a cada 14 dias se a performance estiver estável.
**Erro fatal:** reduzir a meta de R$ 80 para R$ 40 de uma vez. O algoritmo entra em colapso.

### Etapa 4 — tROAS (evitar para serviços de emergência locais)
**Regra do Pedro Sobral:** NÃO use tROAS para serviços locais com ticket variável.
- Desentupidora: R$ 150 (esgoto simples) a R$ 1.500 (coluna predial)
- Chaveiro: R$ 100 a R$ 600
- O ROAS médio calculado não representa nenhum trabalho real — é uma ficção matemática
- Use tCPA + acompanhe conversões em quantidade, não em valor

## Regras de Ouro das Estratégias de Lance

1. **Nunca troque de estratégia sem motivo** — cada troca reseta o período de aprendizado (7–14 dias)
2. **O período de aprendizado é sagrado** — não mexa em estrutura, orçamento ±20%, ou lances durante os primeiros 7 dias após mudança de estratégia
3. **Orçamento mínimo para automação funcionar:** 3–5x o CPA desejado por dia
   - CPA desejado R$ 60 → orçamento diário mínimo R$ 180–300
4. **Sazonalidade:** pause a automação (volte para CPC Manual) durante eventos atípicos com duração < 7 dias. Para eventos longos, ajuste o tCPA

## Diagnóstico de Problemas de Lance

| Sintoma | Causa Provável | Solução |
|---|---|---|
| CPA subindo gradualmente | Meta de tCPA muito baixa | Suba a meta 20%, espere 2 semanas |
| Volume de conversões caindo | Meta inalcançável ou orçamento limitando | Aumente orçamento ou meta |
| CPA instável (varia 50%+) | Poucos dados, avance para tCPA só quando > 50 conv/mês | Aguarde mais dados |
| Muitos cliques, zero conversão | Problema de LP ou tracking quebrado | Verifique tag de conversão antes de qualquer ajuste de lance |
