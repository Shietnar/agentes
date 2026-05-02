# CRO — Técnicas de Alta Conversão (CXL Institute + Unbounce Research)

## Os 7 Elementos Obrigatórios Acima da Dobra (Mobile)

Pesquisa CXL: 86% das decisões de sair ou ficar acontecem nos primeiros 3 segundos.
Para emergência local em mobile (70%+ do tráfego), acima da dobra é TUDO.

1. **Número de telefone clicável** — `href="tel:+55..."` — fonte > 24px, cor contrastante
2. **H1 com keyword principal** — deve espelhar o anúncio (message match)
3. **Sub-headline com diferenciador** — "Chegamos em 45 minutos • 24 horas • Orçamento grátis"
4. **CTA primário** — botão grande (min 56px altura), cor que contraste 4.5:1 com o fundo
5. **CTA secundário** — WhatsApp (segundo CTA mais importante no Brasil)
6. **Badge de credibilidade rápida** — "4.9★ Google | 15 anos | +5.000 atendimentos"
7. **Sem menu complexo** — máximo: logo + telefone no header. Menu de 20 itens = abandono

## Message Match — O Elo entre Anúncio e LP

**Conceito (Unbounce):** o texto do anúncio deve se "continuar" na LP. Se o anúncio diz "Desentupidora em SP — Atende em 1 Hora", o H1 da LP deve repetir essa promessa.

**Impacto no QS:** message match fraco = QS baixo = CPC alto = menos cliques pelo mesmo dinheiro.

| Anúncio | LP H1 Fraco | LP H1 Forte |
|---|---|---|
| "Desentupidora SP — 1 Hora" | "Bem-vindo à Empresa X" | "Desentupidora em SP — Chegamos em 1 Hora" |
| "Gasista 24h Rio" | "Serviços de Gás" | "Gasista no Rio 24 Horas — Atendimento Imediato" |

## Velocidade — Impacto Quantificado

Google/Deloitte study: cada 0.1s de melhoria na velocidade = +8% de conversão no mobile.

**Alvos:**
- LCP (Largest Contentful Paint): < 2.5s
- FID (First Input Delay): < 100ms
- CLS (Cumulative Layout Shift): < 0.1
- TTFB (Time to First Byte): < 600ms

**Principais causas de lentidão em sites de serviços locais:**
1. Imagens sem compressão (foto de equipe de 3MB sem otimização)
2. Google Fonts carregadas externamente
3. Scripts de chat/pop-up de terceiros (ex: Tawk, Zendesk) bloqueantes
4. Servidor compartilhado lento (problema de hosting)
5. WordPress sem cache plugin (WP Rocket, W3 Total Cache)

**Solução rápida:** WebP para imagens + lazy loading + cache plugin + CDN (CloudFlare gratuito)

## Formulários — A Regra dos Campos Mínimos

**Pesquisa Unbounce:** cada campo adicional reduz conversão em ~20%.

| Campos | Conversão Relativa |
|---|---|
| Nome + Telefone | 100% (baseline) |
| + Email | ~80% |
| + CEP | ~64% |
| + Tipo de serviço | ~51% |
| + Mensagem | ~41% |

**Para emergência:** nome + telefone APENAS. O cliente quer ligar, não preencher formulário.
**Alternativa ao formulário:** botão WhatsApp com mensagem pré-preenchida ("Olá, preciso de um [serviço] em [cidade]")

## Hierarquia de Trust Signals (CXL Research)

Ordem de impacto em conversão para serviços locais:

1. **Google Reviews widget real** (não screenshots) — verificável, atual, com fotos
2. **Número de atendimentos** — "mais de 8.000 serviços realizados" com contador
3. **Garantia explícita escrita** — "30 dias de garantia ou voltamos sem custo"
4. **CNPJ visível** — resolve objeção de "empresa real ou golpe?"
5. **Fotos reais dos técnicos** — foto genérica de banco de imagens destrói confiança
6. **Certificações** — CREA, CRBIO, etc. onde aplicável
7. **Meios de pagamento** — PIX, cartão, dinheiro — resolve "e se for caro?"
8. **Área de atendimento explícita** — lista de bairros ou mapa

## Pop-ups — Regra Absoluta

**Para tráfego pago de emergência: ZERO pop-ups.**
- Pop-up de saída em mobile não funciona (gesture != mouse hover)
- Pop-up de entrada em campanha de emergência = usuário em crise que fecha e vai para o concorrente
- Se usar pop-up em algum contexto: nunca em mobile, nunca em primeiro acesso, nunca em tráfego de emergência

## WhatsApp — O CTA Mais Importante do Brasil

**Dado:** 70%+ dos brasileiros preferem WhatsApp a qualquer outro canal de contato.

**Implementação correta:**
```html
<!-- Botão flutuante sempre visível -->
<a href="https://wa.me/5511999990000?text=Ol%C3%A1%2C%20preciso%20de%20ajuda%20urgente"
   style="position:fixed;bottom:20px;right:20px;z-index:9999">
  💬 WhatsApp
</a>
```

**Mensagem pré-preenchida ideal:** "Olá, preciso de [serviço] em [cidade]. Pode me ajudar?"
Remove a fricção de escrever a primeira mensagem.

**Botão dentro da LP:** coloque acima da dobra, depois do CTA de telefone (segundo CTA mais importante).

## Testes A/B para Emergência — Prioridades

**Alto impacto, fácil de testar:**
1. Cor do botão de CTA (vermelho vs. verde vs. laranja)
2. Texto do CTA ("Ligue Agora" vs. "Falar com Técnico" vs. "Solicitar Orçamento Grátis")
3. Texto do H1 (com/sem prazo de chegada)
4. Posição do WhatsApp (flutuante vs. no hero)
5. Foto da equipe real vs. ícone/ilustração

**O que não testar antes de corrigir erros básicos:**
- Cor de fundo
- Fonte
- Ordem das seções

Se o site não tem número clicável, não tem WhatsApp, e é lento — não teste A/B. Corrija primeiro.
