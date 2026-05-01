"""
Memória persistente por agente — UnboundSales
Armazena contexto relevante entre sessões: clientes atendidos, padrões aprendidos,
preferências por segmento. Carregada no início de cada chamada de agente.
"""
import os
from datetime import datetime

_MEMORY_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "memory", "agents",
)


def _arquivo_geral(agent_key: str) -> str:
    return os.path.join(_MEMORY_DIR, f"{agent_key}.md")


def _arquivo_cliente(agent_key: str, cliente_id: int) -> str:
    return os.path.join(_MEMORY_DIR, f"{agent_key}_cliente_{cliente_id}.md")


def carregar(agent_key: str, cliente_id: int = None) -> str:
    """
    Retorna bloco de memória para injetar no prompt do agente.
    Combina memória geral (padrões aprendidos) + memória do cliente específico.
    Retorna string vazia se não houver memória.
    """
    os.makedirs(_MEMORY_DIR, exist_ok=True)
    partes = []

    # Memória geral do agente (aprendizados cross-cliente)
    arq = _arquivo_geral(agent_key)
    if os.path.exists(arq):
        conteudo = open(arq).read().strip()
        if conteudo:
            partes.append(f"[MEMÓRIA DO ESPECIALISTA — aprendizados anteriores]\n{conteudo}")

    # Memória específica do cliente
    if cliente_id:
        arq = _arquivo_cliente(agent_key, cliente_id)
        if os.path.exists(arq):
            conteudo = open(arq).read().strip()
            if conteudo:
                partes.append(f"[MEMÓRIA DESTE CLIENTE]\n{conteudo}")

    return "\n\n".join(partes)


def salvar_cliente(agent_key: str, cliente_id: int, conteudo: str):
    """Salva/sobrescreve memória do agente para um cliente específico."""
    os.makedirs(_MEMORY_DIR, exist_ok=True)
    arq = _arquivo_cliente(agent_key, cliente_id)
    _escrever(arq, agent_key, conteudo)


def salvar_geral(agent_key: str, conteudo: str):
    """Salva/sobrescreve memória geral do agente (aprendizados cross-cliente)."""
    os.makedirs(_MEMORY_DIR, exist_ok=True)
    arq = _arquivo_geral(agent_key)
    _escrever(arq, agent_key, conteudo)


def listar(agent_key: str) -> dict:
    """Retorna dict com caminhos e existência de memórias do agente."""
    os.makedirs(_MEMORY_DIR, exist_ok=True)
    resultado = {"geral": None, "clientes": []}

    arq_geral = _arquivo_geral(agent_key)
    if os.path.exists(arq_geral):
        resultado["geral"] = arq_geral

    prefixo = f"{agent_key}_cliente_"
    for nome in os.listdir(_MEMORY_DIR):
        if nome.startswith(prefixo) and nome.endswith(".md"):
            resultado["clientes"].append(os.path.join(_MEMORY_DIR, nome))

    return resultado


def _escrever(caminho: str, agent_key: str, conteudo: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(caminho, "w") as f:
        f.write(f"# Memória — {agent_key}\nAtualizado: {ts}\n\n{conteudo}")
