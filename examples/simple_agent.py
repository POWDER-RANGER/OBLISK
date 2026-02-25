"""Simple agent demo — runs without any external dependencies beyond oblisk.

Demonstrates:
- Creating a Vault with a derived key
- Initialising an Agent wired to the vault
- Storing a secret in the vault from within agent context
- Executing a task and inspecting the result
"""

from __future__ import annotations

import logging
import sys

# Configure logging so demo output is visible
logging.basicConfig(level=logging.WARNING, stream=sys.stdout)

from vault import Vault, derive_key
from agents.agent import Agent


def main() -> None:
    # 1. Derive a 256-bit vault key from a passphrase
    key, _salt = derive_key("demo-passphrase-change-in-production")
    vault = Vault(key=key, name="demo-vault")

    # 2. Store a secret in the encrypted vault
    vault.store("openai_api_key", "sk-demo-key-replace-with-real")
    print(f"[vault] Stored 1 secret. Keys: {vault.list_keys()}")

    # 3. Create an agent wired to the vault
    agent = Agent(
        name="research_assistant",
        capabilities=["research", "analysis"],
        vault=vault,
    )
    print(f"[agent] Created: {agent}")

    # 4. Start the agent
    started = agent.start()
    print(f"[agent] Started: {started}, Status: {agent.status.value}")

    # 5. Execute a task (returns a result dict)
    task = {
        "id": "task-001",
        "name": "analyse_dataset",
        "payload": {"source": "data.csv", "rows": 1000},
    }
    result = agent.execute_task(task)
    print(f"[agent] Task result: {result}")
    assert result["status"] == "completed", f"Expected completed, got {result['status']}"

    # 6. Inspect agent status
    status = agent.get_status()
    print(f"[agent] Status dict: tasks_completed={status['tasks_completed']}, has_vault={status['has_vault']}")

    # 7. Retrieve the vault secret to confirm round-trip
    api_key = vault.retrieve("openai_api_key")
    assert api_key == "sk-demo-key-replace-with-real", "Vault round-trip failed!"
    print(f"[vault] Retrieved secret: {api_key[:8]}... (AES-256-GCM decrypted OK)")

    # 8. Stop agent
    agent.stop()
    print(f"[agent] Final status: {agent.status.value}")
    print("\n✅ simple_agent.py completed successfully.")


if __name__ == "__main__":
    main()
