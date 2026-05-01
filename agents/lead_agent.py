import anthropic
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import ANTHROPIC_API_KEY, DEFAULT_MODEL
from database.models import SessionLocal, Lead, Conversa, Cliente, StatusLead
from datetime import datetime

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT_BASE = """Você é um atendente virtual da empresa {nome_empresa}, especializada em {segmento} em {cidade}.

Sua personalidade: {personalidade}

Suas responsabilidades:
- Atender leads que chegam pelo Google Ads com simpatia e agilidade
- Entender o problema do cliente (o que precisa, onde, quando)
- Passar confiança e credibilidade
- Informar os diferenciais da empresa ({diferenciais})
- Coletar: nome, telefone, endereço e descrição do problema
- Propor agendamento ou visita técnica
- NUNCA inventar preços — diga que o técnico avalia no local
- Se o cliente perguntar algo que você não sabe, diga que vai verificar com a equipe

Responda sempre de forma natural, como um atendente humano. Seja breve e direto.
Use o nome do cliente quando souber. Finalize com uma chamada para ação clara."""


def carregar_perfil_cliente(cliente_id: int) -> dict:
    """Busca as configurações do cliente no banco de dados."""
    db = SessionLocal()
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    db.close()

    if not cliente:
        return None

    return {
        "nome_empresa": cliente.nome,
        "segmento": cliente.segmento,
        "cidade": cliente.cidade,
        "personalidade": cliente.prompt_personalizado or "simpático, profissional e ágil",
        "diferenciais": "atendimento rápido, orçamento grátis, equipe qualificada"
    }


def construir_system_prompt(perfil: dict) -> str:
    return SYSTEM_PROMPT_BASE.format(**perfil)


def atender_lead(cliente_id: int, lead_id: int, mensagem_usuario: str, historico: list = None) -> str:
    """
    Processa uma mensagem do lead e retorna a resposta do agente.
    historico: lista de dicts [{"role": "user"/"assistant", "content": "..."}]
    """
    perfil = carregar_perfil_cliente(cliente_id)
    if not perfil:
        return "Erro: cliente não encontrado no sistema."

    system_prompt = construir_system_prompt(perfil)

    mensagens = historico or []
    mensagens.append({"role": "user", "content": mensagem_usuario})

    resposta = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=500,
        system=system_prompt,
        messages=mensagens
    )

    texto_resposta = resposta.content[0].text

    # Salva a conversa no banco
    db = SessionLocal()
    db.add(Conversa(lead_id=lead_id, remetente="lead", mensagem=mensagem_usuario))
    db.add(Conversa(lead_id=lead_id, remetente="agente", mensagem=texto_resposta))
    db.commit()
    db.close()

    return texto_resposta


def simular_atendimento(cliente_id: int):
    """Modo de simulação via terminal para testar o agente."""
    db = SessionLocal()
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()

    if not cliente:
        print(f"Cliente ID {cliente_id} não encontrado.")
        db.close()
        return

    # Cria lead de teste
    lead = Lead(
        cliente_id=cliente_id,
        nome="Lead Teste",
        telefone="(11) 99999-9999",
        status=StatusLead.em_atendimento,
        origem="simulacao"
    )
    db.add(lead)
    db.commit()
    lead_id = lead.id
    db.close()

    print(f"\n{'='*50}")
    print(f"SIMULAÇÃO DE ATENDIMENTO — {cliente.nome}")
    print(f"{'='*50}")
    print("Digite suas mensagens como se fosse o lead.")
    print("Digite 'sair' para encerrar.\n")

    historico = []

    # Mensagem inicial do agente
    boas_vindas = atender_lead(
        cliente_id, lead_id,
        "Olá, vim pelo anúncio do Google e preciso de ajuda.",
        historico
    )
    print(f"[Agente]: {boas_vindas}\n")
    historico.append({"role": "user", "content": "Olá, vim pelo anúncio do Google e preciso de ajuda."})
    historico.append({"role": "assistant", "content": boas_vindas})

    while True:
        mensagem = input("[Lead]: ").strip()
        if mensagem.lower() == "sair":
            print("\nSimulação encerrada.")
            break

        resposta = atender_lead(cliente_id, lead_id, mensagem, historico)
        historico.append({"role": "user", "content": mensagem})
        historico.append({"role": "assistant", "content": resposta})
        print(f"[Agente]: {resposta}\n")


if __name__ == "__main__":
    print("Para usar este agente, execute main.py e cadastre um cliente primeiro.")
