"""Agent Manager module for OBLISK.

Provides centralized management and coordination of multiple agents.
"""

from typing import Dict, List, Optional, Any
import logging
from .agent import Agent, AgentStatus


class AgentManager:
    """Manages multiple agents and coordinates their activities.
    
    The AgentManager class provides centralized control over agent lifecycle,
    task distribution, and inter-agent communication within the OBLISK system.
    
    Attributes:
        agents (Dict[str, Agent]): Dictionary of managed agents keyed by agent_id
        max_agents (int): Maximum number of concurrent agents allowed
        
    Example:
        >>> manager = AgentManager(max_agents=10)
        >>> agent = manager.create_agent(name="worker_1", capabilities=["task"])
        >>> manager.start_agent(agent.agent_id)
        >>> status = manager.get_all_status()
    """
    
    def __init__(self, max_agents: int = 100):
        """Initialize the AgentManager.
        
        Args:
            max_agents: Maximum number of concurrent agents (default: 100)
        """
        self.agents: Dict[str, Agent] = {}
        self.max_agents = max_agents
        self._logger = logging.getLogger("oblisk.agent_manager")
        self._logger.info(f"AgentManager initialized with max_agents={max_agents}")
    
    def create_agent(
        self,
        name: str,
        capabilities: Optional[List[str]] = None,
        vault: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Agent:
        """Create and register a new agent.
        
        Args:
            name: Human-readable name for the agent
            capabilities: List of agent capabilities
            vault: Optional Vault instance
            config: Optional configuration dictionary
            
        Returns:
            Agent: The newly created agent instance
            
        Raises:
            RuntimeError: If maximum agent limit is reached
        """
        if len(self.agents) >= self.max_agents:
            raise RuntimeError(
                f"Cannot create agent: maximum limit of {self.max_agents} reached"
            )
        
        agent = Agent(name=name, capabilities=capabilities, vault=vault, config=config)
        self.agents[agent.agent_id] = agent
        self._logger.info(f"Created agent '{name}' with ID {agent.agent_id}")
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Retrieve an agent by its ID.
        
        Args:
            agent_id: The unique agent identifier
            
        Returns:
            Optional[Agent]: The agent if found, None otherwise
        """
        return self.agents.get(agent_id)
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from management.
        
        Args:
            agent_id: The unique agent identifier
            
        Returns:
            bool: True if agent was removed, False if not found
        """
        agent = self.agents.get(agent_id)
        if agent:
            if agent.status == AgentStatus.RUNNING:
                agent.stop()
            del self.agents[agent_id]
            self._logger.info(f"Removed agent {agent_id}")
            return True
        return False
    
    def start_agent(self, agent_id: str) -> bool:
        """Start a specific agent.
        
        Args:
            agent_id: The unique agent identifier
            
        Returns:
            bool: True if agent started successfully, False otherwise
        """
        agent = self.get_agent(agent_id)
        if agent:
            return agent.start()
        self._logger.warning(f"Agent {agent_id} not found")
        return False
    
    def stop_agent(self, agent_id: str) -> bool:
        """Stop a specific agent.
        
        Args:
            agent_id: The unique agent identifier
            
        Returns:
            bool: True if agent stopped successfully, False otherwise
        """
        agent = self.get_agent(agent_id)
        if agent:
            return agent.stop()
        self._logger.warning(f"Agent {agent_id} not found")
        return False
    
    def start_all(self) -> int:
        """Start all registered agents.
        
        Returns:
            int: Number of agents successfully started
        """
        count = 0
        for agent in self.agents.values():
            if agent.start():
                count += 1
        self._logger.info(f"Started {count}/{len(self.agents)} agents")
        return count
    
    def stop_all(self) -> int:
        """Stop all running agents.
        
        Returns:
            int: Number of agents successfully stopped
        """
        count = 0
        for agent in self.agents.values():
            if agent.status == AgentStatus.RUNNING:
                if agent.stop():
                    count += 1
        self._logger.info(f"Stopped {count} agents")
        return count
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all agents.
        
        Returns:
            Dict: Dictionary mapping agent_id to status information
        """
        return {agent_id: agent.get_status() for agent_id, agent in self.agents.items()}
    
    def get_agents_by_status(self, status: AgentStatus) -> List[Agent]:
        """Get all agents with a specific status.
        
        Args:
            status: The agent status to filter by
            
        Returns:
            List[Agent]: List of agents matching the status
        """
        return [agent for agent in self.agents.values() if agent.status == status]
    
    def get_agents_by_capability(self, capability: str) -> List[Agent]:
        """Get all agents with a specific capability.
        
        Args:
            capability: The capability to filter by
            
        Returns:
            List[Agent]: List of agents with the specified capability
        """
        return [
            agent
            for agent in self.agents.values()
            if capability in agent.capabilities
        ]
    
    def distribute_task(self, task: Dict[str, Any], capability: Optional[str] = None) -> Optional[str]:
        """Distribute a task to an available agent.
        
        Args:
            task: The task to distribute
            capability: Optional required capability for the task
            
        Returns:
            Optional[str]: Agent ID of the agent assigned the task, or None if no agent available
        """
        # Get eligible agents
        if capability:
            eligible_agents = self.get_agents_by_capability(capability)
        else:
            eligible_agents = list(self.agents.values())
        
        # Find an available (IDLE or RUNNING) agent
        for agent in eligible_agents:
            if agent.status in [AgentStatus.IDLE, AgentStatus.RUNNING]:
                agent.execute_task(task)
                self._logger.info(f"Assigned task to agent {agent.agent_id}")
                return agent.agent_id
        
        self._logger.warning("No available agent found for task")
        return None
    
    def __repr__(self) -> str:
        return f"AgentManager(agents={len(self.agents)}, max={self.max_agents})"
