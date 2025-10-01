"""Simple Agent Example

This example demonstrates how to create and start a basic agent in OBLISK.
"""

from oblisk.agents import Agent
from oblisk.vault import Vault


def main():
    """Create and run a simple research assistant agent."""
    
    # Create an encrypted vault for the agent
    vault = Vault.create(
        name="research_vault",
        encrypted=True
    )
    
    # Create the agent with specific capabilities
    agent = Agent(
        name="research_assistant",
        capabilities=["research", "analysis", "reporting"],
        vault=vault,
        config={
            "max_concurrent_tasks": 5,
            "timeout": 300,
        }
    )
    
    print(f"Created agent: {agent.name}")
    print(f"Capabilities: {', '.join(agent.capabilities)}")
    
    # Start the agent
    agent.start()
    print(f"Agent status: {agent.state}")
    
    # Assign a task to the agent
    task = agent.assign_task(
        task_type="research",
        description="Research the latest advances in multi-agent systems",
        priority="high"
    )
    
    print(f"Task assigned: {task.id}")
    
    # Wait for task completion
    result = agent.wait_for_task(task.id, timeout=60)
    
    if result.success:
        print(f"Task completed successfully!")
        print(f"Result: {result.data}")
    else:
        print(f"Task failed: {result.error}")
    
    # Stop the agent gracefully
    agent.stop()
    print("Agent stopped")


if __name__ == "__main__":
    main()
