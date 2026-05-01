"""
Sistema de Reunião de Time — UnboundSales
Migrado para Anthropic Managed Agents API.

Cada especialista é um agente persistente criado via setup_agents.py.
A cada reunião, sessões efêmeras são criadas por chamada de especialista,
com o histórico de debate passado como contexto na mensagem do usuário.

Pré-requisito: execute python agents/setup_agents.py e adicione os IDs ao .env.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from config.settings import (
    ANTHROPIC_API_KEY,
    AGENT_LUCAS_ID,
    AGENT_PEDRO_ID,
    AGENT_RODRIGO_ID,
    AGENT_ANA_ID,
    AGENT_MODERADOR_ID,
    MANAGED_AGENTS_ENVIRONMENT_ID,
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ─── MAPEAMENTO DE PERSONAS ────────────────────────────────────────────────────
# Mantém metadados visuais (ícone, cor) para compatibilidade com o dashboard.
# Os system prompts vivem nos agentes da plataforma Anthropic (setup_agents.py).

_PERSONAS = {
    "🎯 Lucas — Estratégia de Negócio": {
        "icone": "🎯",
        "cor": "#1565C0",
        "agent_key": "lucas",
    },
    "🔬 Pedro — Google Ads": {
        "icone": "🔬",
        "cor": "#C62828",
        "agent_key": "pedro",
    },
    "✍️ Rodrigo — Copywriter RSA": {
        "icone": "✍️",
        "cor": "#2E7D32",
        "agent_key": "rodrigo",
    },
    "🌐 Ana — Landing Pages & Web": {
        "icone": "🌐",
        "cor": "#6A1B9A",
        "agent_key": "ana",
    },
}

_AGENT_IDS = {
    "lucas":     AGENT_LUCAS_ID,
    "pedro":     AGENT_PEDRO_ID,
    "rodrigo":   AGENT_RODRIGO_ID,
    "ana":       AGENT_ANA_ID,
    "moderador": AGENT_MODERADOR_ID,
}

# ─── TIPOS DE REUNIÃO ──────────────────────────────────────────────────────────

TIPOS_REUNIAO = {
    "novo_cliente": {
        "label": "🆕 Onboarding de Novo Cliente",
        "descricao": "Análise completa e estratégia integrada para um novo cliente.",
        "instrucao_r1": (
            "É a primeira reunião sobre este cliente. Analise o briefing e dê seu diagnóstico "
            "inicial na sua área de especialidade. O que você vê de potencial, riscos e oportunidades? "
            "O que precisa ser feito PRIMEIRO na sua área?"
        ),
        "instrucao_r2": (
            "Você já ouviu seus colegas. Agora responda diretamente ao que foi dito: "
            "Concorda? Discorda de algum ponto? O que a análise dos colegas muda ou complementa "
            "na sua visão? Há dependências entre as áreas que precisam ser resolvidas juntas?"
        ),
    },
    "revisao_campanha": {
        "label": "🔬 Revisão de Campanha Ativa",
        "descricao": "Time analisa o desempenho atual e define melhorias integradas.",
        "instrucao_r1": (
            "O cliente tem uma campanha ativa. Analise os dados disponíveis e dê seu diagnóstico "
            "na sua área: o que está bom, o que está ruim, o que é urgente?"
        ),
        "instrucao_r2": (
            "Depois de ouvir seus colegas, identifique as dependências entre as áreas: "
            "O problema de Google Ads impacta a LP? A copy fraca explica o QS baixo? "
            "Proponha uma solução integrada que conecte as áreas."
        ),
    },
    "estrategia_mensal": {
        "label": "📅 Planejamento Mensal",
        "descricao": "Time define o foco e prioridades para o próximo mês.",
        "instrucao_r1": (
            "É início do mês. Com base no contexto do cliente e histórico, defina as 3 prioridades "
            "da sua área para os próximos 30 dias. Seja específico: o que será feito, quando e por quê."
        ),
        "instrucao_r2": (
            "Depois de ouvir os colegas, alinhe o plano da sua área com o deles. "
            "Há conflitos de prioridade? Ações de uma área que dependem de outra? Ajuste seu plano."
        ),
    },
    "crescimento": {
        "label": "🚀 Estratégia de Crescimento",
        "descricao": "Time debate como escalar resultados do cliente.",
        "instrucao_r1": (
            "O cliente quer crescer. Na sua área de especialidade, qual é o maior alavancador "
            "de crescimento? O que, se bem feito, multiplica os resultados mais rápido?"
        ),
        "instrucao_r2": (
            "Seus colegas deram suas visões de crescimento. Construa em cima delas: "
            "Como as iniciativas das áreas se complementam? Qual é a sequência correta? "
            "O que trava o crescimento que depende de mais de uma área para resolver?"
        ),
    },
}


# ─── MOTOR DA REUNIÃO ──────────────────────────────────────────────────────────

class TeamSession:
    """
    Orquestra a reunião de time usando Anthropic Managed Agents.
    Cada especialista é um agente persistente; cada chamada cria uma sessão efêmera.
    O histórico de debate é compartilhado via contexto na mensagem enviada a cada agente.
    """

    def __init__(
        self,
        nome_cliente: str,
        segmento: str,
        cidade: str,
        tipo: str,
        briefing: str,
    ):
        self.nome_cliente = nome_cliente
        self.segmento = segmento
        self.cidade = cidade
        self.tipo = tipo
        self.briefing = briefing
        self.historico = []
        self.config = TIPOS_REUNIAO.get(tipo, TIPOS_REUNIAO["novo_cliente"])

    def _contexto_reuniao(self) -> str:
        return (
            f"CLIENTE: {self.nome_cliente}\n"
            f"SEGMENTO: {self.segmento}\n"
            f"CIDADE/REGIÃO: {self.cidade}\n\n"
            f"BRIEFING / CONTEXTO:\n{self.briefing}"
        )

    def _historico_formatado(self) -> str:
        if not self.historico:
            return ""
        linhas = ["─── O QUE O TIME JÁ DISCUTIU ───"]
        for h in self.historico:
            linhas.append(f"\n**{h['agente']}:**\n{h['contribuicao']}")
        return "\n".join(linhas)

    def _executar_sessao(self, agent_id: str, mensagem: str) -> str:
        """
        Cria uma sessão Managed Agent, envia a mensagem via streaming e
        retorna o texto completo gerado pelo agente.
        """
        if not agent_id:
            raise ValueError(
                "Agent ID não configurado. "
                "Execute 'python agents/setup_agents.py' e adicione os IDs ao .env."
            )
        if not MANAGED_AGENTS_ENVIRONMENT_ID:
            raise ValueError(
                "MANAGED_AGENTS_ENVIRONMENT_ID não configurado. "
                "Execute 'python agents/setup_agents.py' e adicione ao .env."
            )

        session = client.beta.sessions.create(
            agent=agent_id,
            environment_id=MANAGED_AGENTS_ENVIRONMENT_ID,
        )

        texto = ""
        # Abre o stream antes de enviar a mensagem (stream-first pattern).
        with client.beta.sessions.events.stream(session_id=session.id) as stream:
            client.beta.sessions.events.send(
                session_id=session.id,
                events=[{
                    "type": "user.message",
                    "content": [{"type": "text", "text": mensagem}],
                }],
            )
            for event in stream:
                if event.type == "agent.message":
                    for block in event.content:
                        if block.type == "text":
                            texto += block.text
                elif event.type == "session.status_terminated":
                    break
                elif event.type == "session.status_idle":
                    stop_reason = getattr(event, "stop_reason", None)
                    stop_type = getattr(stop_reason, "type", None)
                    if stop_type == "requires_action":
                        continue
                    break

        return texto

    def _chamar_especialista(self, nome: str, instrucao_rodada: str) -> str:
        agent_key = _PERSONAS[nome]["agent_key"]
        agent_id = _AGENT_IDS[agent_key]

        conteudo = (
            f"{self._contexto_reuniao()}\n\n"
            f"TIPO DE REUNIÃO: {self.config['label']}\n\n"
        )
        historico_str = self._historico_formatado()
        if historico_str:
            conteudo += f"{historico_str}\n\n─── SUA VEZ ───\n"
        conteudo += instrucao_rodada

        texto = self._executar_sessao(agent_id, conteudo)
        self.historico.append({"agente": nome, "contribuicao": texto})
        return texto

    def _sintetizar(self) -> str:
        historico_str = self._historico_formatado()
        prompt = (
            f"Reunião do time sobre o cliente **{self.nome_cliente}** "
            f"({self.segmento} — {self.cidade}).\n\n"
            f"Tipo: {self.config['label']}\n\n"
            f"BRIEFING:\n{self.briefing}\n\n"
            f"{historico_str}\n\n"
            "Agora produza o PLANO DE AÇÃO INTEGRADO e FINAL do time. "
            "Consolide o que foi debatido em um documento claro, priorizado e acionável."
        )
        return self._executar_sessao(_AGENT_IDS["moderador"], prompt)

    def rodar(self, callback=None):
        """
        Executa a reunião completa via Managed Agents.
        Interface idêntica à versão anterior — totalmente compatível com o dashboard.

        callback(etapa, agente, texto) é chamado após cada contribuição completa.
        Etapas: "rodada_1", "rodada_2", "sintese"

        Retorna dict com: historico, sintese_final
        """
        nomes = list(_PERSONAS.keys())

        # ── Rodada 1: Análise inicial ──────────────────────────────────────────
        for nome in nomes:
            texto = self._chamar_especialista(nome, self.config["instrucao_r1"])
            if callback:
                callback("rodada_1", nome, texto)

        # ── Rodada 2: Debate e complementos ───────────────────────────────────
        for nome in nomes:
            texto = self._chamar_especialista(nome, self.config["instrucao_r2"])
            if callback:
                callback("rodada_2", nome, texto)

        # ── Síntese final pelo moderador ───────────────────────────────────────
        sintese = self._sintetizar()
        if callback:
            callback("sintese", "📋 Moderador — Plano Final", sintese)

        return {
            "historico": self.historico,
            "sintese_final": sintese,
        }


# ─── EXECUÇÃO DIRETA ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    session = TeamSession(
        nome_cliente="Desentupidora Rápida SP",
        segmento="Desentupidora",
        cidade="São Paulo - Zona Sul",
        tipo="novo_cliente",
        briefing=(
            "Empresa com 8 anos, 4 técnicos. Atende zona sul e centro. "
            "Diferencial: chegada em 45 min, orçamento grátis, nota fiscal. "
            "Budget Google Ads: R$ 80/dia. Ticket médio: R$ 350. "
            "Site atual: WordPress básico sem LP dedicada. "
            "QS médio das keywords: 5. CTR: 3.2%. CPA atual: R$ 85."
        ),
    )

    def imprimir(etapa, agente, texto):
        print(f"\n{'═' * 60}")
        print(f"  [{etapa.upper()}] {agente}")
        print(f"{'═' * 60}")
        print(texto)

    resultado = session.rodar(callback=imprimir)
    print(f"\n{'═' * 60}")
    print("  REUNIÃO CONCLUÍDA")
    print(f"  {len(resultado['historico'])} contribuições registradas")
