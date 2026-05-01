"""
Atualiza os system prompts dos agentes managed com as versões mais recentes do setup_agents.py.
Execute sempre que alterar os prompts:
    python agents/push_prompts.py
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
)
from agents.setup_agents import AGENTES

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

ID_MAP = {
    "LUCAS":    AGENT_LUCAS_ID,
    "PEDRO":    AGENT_PEDRO_ID,
    "RODRIGO":  AGENT_RODRIGO_ID,
    "ANA":      AGENT_ANA_ID,
    "MODERADOR": AGENT_MODERADOR_ID,
}


def push():
    print("\n=== UNBOUND SALES — PUSH DE SYSTEM PROMPTS ===\n")
    ok = 0
    for cfg in AGENTES:
        agent_id = ID_MAP.get(cfg["key"])
        if not agent_id:
            print(f"  ⚠️  {cfg['key']}: ID não configurado no .env — pulando")
            continue
        try:
            ag = client.beta.agents.retrieve(agent_id)
            kwargs = {
                "version": ag.version,
                "system": cfg["system"],
            }
            if cfg.get("tools"):
                kwargs["tools"] = cfg["tools"]
            client.beta.agents.update(agent_id, **kwargs)
            chars = len(cfg["system"])
            print(f"  ✅ {cfg['key']} ({cfg['name']}): {chars} chars de system prompt")
            ok += 1
        except Exception as e:
            print(f"  ❌ {cfg['key']}: {e}")

    print(f"\n  {ok}/{len(AGENTES)} agentes atualizados.\n")


if __name__ == "__main__":
    push()
