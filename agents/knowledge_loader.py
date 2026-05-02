"""
Knowledge Loader — UnboundSales
Carrega os arquivos .md de conhecimento de cada agente e injeta no system prompt.

Separação clara:
  agents/setup_agents.py   → personalidade, voz, como pensa, como se comunica
  agents/knowledge/{key}/  → técnicas, frameworks, benchmarks, dados de mercado

Isso permite:
  - Atualizar conhecimento via ETL sem tocar na personalidade
  - Criar novos agentes adicionando pasta + personalidade
  - Cada agente ter knowledge base independente e expansível
"""
from pathlib import Path

_KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"


def carregar_conhecimento(agent_key: str, max_chars: int = 80_000) -> str:
    """
    Carrega todos os arquivos .md da pasta agents/knowledge/{agent_key}/.
    Retorna string formatada para injeção no system prompt.
    Arquivos prefixados com '_' são ignorados (usados para índices/notas internas).
    """
    agent_dir = _KNOWLEDGE_DIR / agent_key
    if not agent_dir.exists():
        return ""

    partes = []
    for md_file in sorted(agent_dir.glob("*.md")):
        if md_file.name.startswith("_"):
            continue
        conteudo = md_file.read_text(encoding="utf-8").strip()
        if conteudo:
            partes.append(conteudo)

    if not partes:
        return ""

    separador = "\n\n" + "─" * 60 + "\n\n"
    conhecimento = separador.join(partes)

    if len(conhecimento) > max_chars:
        conhecimento = conhecimento[:max_chars] + "\n\n[... knowledge truncated ...]"

    return conhecimento


def montar_system_prompt(personalidade: str, agent_key: str) -> str:
    """
    Combina personalidade + conhecimento em um único system prompt.
    A personalidade define QUEM o agente é.
    O conhecimento define O QUE ele sabe.
    """
    conhecimento = carregar_conhecimento(agent_key)
    if not conhecimento:
        return personalidade

    return (
        f"{personalidade}\n\n"
        f"{'━' * 60}\n\n"
        f"━━━ BASE DE CONHECIMENTO ESPECIALIZADO ━━━\n\n"
        f"O conteúdo abaixo é sua base técnica de referência. "
        f"Use-o como fundamento para suas análises e recomendações.\n\n"
        f"{conhecimento}"
    )


def listar_fontes(agent_key: str) -> list[dict]:
    """Lista os arquivos de conhecimento disponíveis para um agente."""
    agent_dir = _KNOWLEDGE_DIR / agent_key
    if not agent_dir.exists():
        return []

    fontes = []
    for md_file in sorted(agent_dir.glob("*.md")):
        if md_file.name.startswith("_"):
            continue
        chars = len(md_file.read_text(encoding="utf-8"))
        fontes.append({
            "arquivo": md_file.name,
            "topico": md_file.stem.replace("_", " ").title(),
            "chars": chars,
        })
    return fontes


def stats_conhecimento() -> dict:
    """Retorna estatísticas da base de conhecimento de todos os agentes."""
    stats = {}
    for agent_dir in sorted(_KNOWLEDGE_DIR.iterdir()):
        if not agent_dir.is_dir():
            continue
        fontes = listar_fontes(agent_dir.name)
        total_chars = sum(f["chars"] for f in fontes)
        stats[agent_dir.name] = {
            "arquivos": len(fontes),
            "total_chars": total_chars,
            "total_tokens_aprox": total_chars // 4,
            "fontes": fontes,
        }
    return stats


if __name__ == "__main__":
    # Diagnóstico rápido
    import json
    stats = stats_conhecimento()
    for agent, info in stats.items():
        print(f"\n{agent.upper()}: {info['arquivos']} arquivos | "
              f"{info['total_chars']:,} chars | ~{info['total_tokens_aprox']:,} tokens")
        for f in info["fontes"]:
            print(f"  ├─ {f['arquivo']} ({f['chars']:,} chars)")
