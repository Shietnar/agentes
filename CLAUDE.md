# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos essenciais

```bash
# Instalar dependências (usar venv já existente)
source venv/bin/activate
pip install -r requirements.txt

# Rodar o sistema principal (terminal interativo)
python main.py

# Rodar um agente individualmente para testes rápidos
python agents/strategy_agent.py
python agents/copywriter_agent.py
python agents/analyst_agent.py

# Criar as tabelas do banco (executado automaticamente no main.py)
python database/models.py

# Gerar refresh token do Google Ads (uma vez só, antes de usar a integração)
python gerar_token.py
```

## Configuração de ambiente

Copiar `.env.example` para `.env` e preencher:
- `ANTHROPIC_API_KEY` — obrigatório para todos os agentes
- `GOOGLE_ADS_*` — necessário apenas para integração com Google Ads
- `GEMINI_API_KEY` / `OPENAI_API_KEY` — reservados para uso futuro

O modelo padrão está em `config/settings.py` (`DEFAULT_MODEL = "claude-sonnet-4-6"`).

## Arquitetura

Sistema multi-agente para agências de marketing digital. Foco em serviços locais de emergência (desentupidoras, gasistas, chaveiros etc.) no mercado brasileiro.

### Fluxo principal (`main.py`)

Terminal interativo com menu. Gerencia clientes e dispara os fluxos de agentes via `agents/orchestrator.py`.

### Agentes (`agents/`)

| Arquivo | Papel |
|---|---|
| `orchestrator.py` | Coordena os agentes: `fluxo_novo_cliente` (estratégia + anúncios) e `fluxo_relatorio_mensal` (análise + relatório) |
| `strategy_agent.py` | Cria estratégia completa de Google Ads a partir de briefing |
| `copywriter_agent.py` | Cria textos de anúncios RSA (títulos + descrições + sitelinks) |
| `analyst_agent.py` | Analisa métricas da campanha e gera relatório para o cliente |
| `lead_agent.py` | Atendente virtual que conversa com leads via API Anthropic, com histórico salvo no banco |

Cada agente usa diretamente `anthropic.Anthropic` com `client.messages.create`. **Não usam LangChain** — apenas `strategy_agent`, `copywriter_agent` e `analyst_agent` importam do SDK direto.

### Banco de dados (`database/models.py`)

SQLite via SQLAlchemy. Modelos principais:
- `Cliente` — empresa cliente da agência (tem `prompt_personalizado` para personalidade do atendente virtual)
- `Campanha` — campanha Google Ads vinculada ao cliente
- `Lead` — lead recebido, com status (`novo → em_atendimento → convertido/perdido`)
- `Conversa` — histórico de mensagens entre lead e agente

`criar_tabelas()` cria o schema; é chamado na inicialização do `main.py`.

### Config (`config/`)

- `settings.py` — carrega todas as variáveis do `.env` e define `DEFAULT_MODEL`
- `google-ads.yaml` — configuração da lib `google-ads` (lida pela API do Google Ads)
- `client_secret.json` — OAuth credentials do Google Cloud (necessário para `gerar_token.py`)

### Integração Google Ads

Ainda não implementada nos agentes (pasta `tools/` está vazia). O `google-ads.yaml` e as credenciais OAuth já estão configurados. A integração será adicionada em `tools/` e chamada pelos agentes conforme necessário.
