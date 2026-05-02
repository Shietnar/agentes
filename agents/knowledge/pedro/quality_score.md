# Quality Score — Diagnóstico e Melhoria

## O Que É e Por Que Importa

Quality Score (1–10) afeta diretamente o **Ad Rank** = Bid × QS × Formatos esperados.
- QS 8 com CPC R$ 3,00 pode superar QS 4 com CPC R$ 6,00
- QS baixo = você paga mais para aparecer menos
- QS alto = você paga menos e aparece mais

## Os 3 Componentes do QS

### 1. CTR Esperado (peso maior)
- Google compara seu CTR histórico vs. a média de anunciantes para aquela keyword
- Avaliação: "Acima da média", "Dentro da média", "Abaixo da média"
- **Como melhorar:** headlines que incluem a keyword, CTAs diretos ("Ligue Agora", "Atendimento 24h"), extensões preenchidas

### 2. Relevância do Anúncio
- Quanto o anúncio corresponde à intenção de busca
- **Como melhorar:** incluir a keyword no headline 1 ou 2, agrupar keywords semanticamente similares, 1 grupo = 1 tema

### 3. Experiência na Página de Destino
- Google avalia: velocidade, relevância do conteúdo, transparência (CNPJ, contato), mobile-friendliness
- **Como melhorar:** keyword na H1 da LP, conteúdo coerente com o anúncio, velocidade < 3s, HTTPS

## Protocolo de Diagnóstico de QS (Pedro Sobral)

### Passo 1: Identifique as keywords com QS ≤ 5 que gastam dinheiro
```sql
-- No Google Ads: Palavras-chave → Colunas → Quality Score
-- Filtre: Custo > R$ 50 AND Quality Score <= 5
```

### Passo 2: Analise cada componente
Para cada keyword com QS ruim:
- CTR Esperado abaixo da média → problema no anúncio (headline, relevância)
- Relevância do anúncio abaixo → keyword não está nos headlines
- Exp. na página abaixo → LP não corresponde ao anúncio ou é lenta

### Passo 3: Ações por problema

**CTR Esperado baixo:**
- Adicione a keyword exact no headline 1 ou 2
- Teste variações de CTA com urgência: "Ligue Agora 24h", "Atendimento Imediato"
- Use Dynamic Keyword Insertion com cuidado (pode sair estranho)
- Verifique extensões: callout, sitelinks, chamada — todas preenchidas

**Relevância baixa:**
- Reavalie se a keyword faz parte do grupo certo
- Crie um novo grupo específico para essa keyword (SKAG se crítica)
- Escreva um anúncio exclusivo para ela

**Experiência na LP baixa:**
- Keyword no título H1 da página
- Número de telefone clicável (tel:) visível sem scroll
- Verifi PageSpeed Insights: alvo LCP < 2,5s
- Cheque se a LP está indexada e acessível pelo Googlebot

## Benchmarks de QS por Setor

| QS | Interpretação | Ação |
|---|---|---|
| 8–10 | Excelente — mantenha | Não mexa sem motivo |
| 6–7 | Bom — pode melhorar | Otimize se gastar > R$ 100/mês |
| 4–5 | Atenção — impacto no CPC | Intervenção em 30 dias |
| 1–3 | Crítico — pagando premium desnecessário | Intervenção imediata ou pausa |

## QS de Keywords Novas

Toda keyword nova começa com QS 6 (default). O Google precisa de:
- Mínimo 1.000 impressões para calcular CTR Esperado real
- Relevância calculada desde o início

**Dica Pedro Sobral:** não pause keywords novas por QS baixo se tiverem < 500 impressões. Espere os dados chegarem.

## Erro Clássico

"Meu QS é 3, então a keyword é ruim e preciso pausar."

Errado. QS 3 pode significar que seu ANÚNCIO é ruim, não a keyword. A keyword pode ser ouro — você só está desperdiçando seu potencial com um anúncio fraco.
