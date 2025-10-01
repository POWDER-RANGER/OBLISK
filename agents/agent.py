"""Agent module for OBLISK.

Provides the core Agent class for creating and managing AI agents within the OBLISK system.
"""

from typing import List, Dict, Optional, Any
from enum import Enum
import logging
from datetime import datetime


class AgentStatus(Enum):
    """Enumeration of possible agent states."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class Agent:
    """Base Agent class for OBLISK system.
    
    The Agent class represents an autonomous AI agent that can perform tasks,
    interact with vaults, and operate under governance policies.
    
    Attributes:
        agent_id (str): Unique identifier for the agent
        name (str): Human-readable name for the agent
        capabilities (List[str]): List of capabilities the agent possesses
        status (AgentStatus): Current status of the agent
        vault: Associated encrypted vault for secure data storage
        config (Dict): Agent configuration parameters
        
    Example:
        >>> agent = Agent(
        ...     name="research_assistant",
        ...     capabilities=["research", "analysis"],
        ...     vault=vault_instance
        ... )
        >>> agent.start()
    """
    
    def __init__(
        self,
        name: str,
        capabilities: Optional[List[str]] = None,
        vault: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize a new Agent instance.
        
        Args:
            name: Human-readable name for the agent
            capabilities: List of capabilities (e.g., ["research", "analysis"])
            vault: Optional Vault instance for secure storage
            config: Optional configuration dictionary
        """
        self.agent_id = self._generate_agent_id()
        self.name = name
        self.capabilities = capabilities or []
        self.vault = vault
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self._logger = logging.getLogger(f"oblisk.agent.{self.name}")
        self._task_history: List[Dict] = []
        
        self._logger.info(f"Agent '{self.name}' initialized with ID {self.agent_id}")
    
    def start(self) -> bool:
        """Start the agent and begin processing tasks.
        
        Returns:
            bool: True if agent started successfully, False otherwise
        """
        if self.status == AgentStatus.RUNNING:
            self._logger.warning(f"Agent '{self.name}' is already running")
            return False
        
        self.status = AgentStatus.RUNNING
        self._logger.info(f"Agent '{self.name}' started")
        return True
    
    def stop(self) -> bool:
        """Stop the agent gracefully.
        
        Returns:
            bool: True if agent stopped successfully, False otherwise
        """
        if self.status == AgentStatus.STOPPED:
            self._logger.warning(f"Agent '{self.name}' is already stopped")
            return False
        
        self.status = AgentStatus.STOPPED
        self._logger.info(f"Agent '{self.name}' stopped")
        return True
    
    def pause(self) -> bool:
        """Pause the agent temporarily.
        
        Returns:
            bool: True if agent paused successfully, False otherwise
        """
        if self.status != AgentStatus.RUNNING:
            self._logger.warning(f"Agent '{self.name}' is not running")
            return False
        
        self.status = AgentStatus.PAUSED
        self._logger.info(f"Agent '{self.name}' paused")
        return True
    
    def resume(self) -> bool:
        """Resume a paused agent.
        
        Returns:
            bool: True if agent resumed successfully, False otherwise
        """
        if self.status != AgentStatus.PAUSED:
            self._logger.warning(f"Agent '{self.name}' is not paused")
            return False
        
        self.status = AgentStatus.RUNNING
        self._logger.info(f"Agent '{self.name}' resumed")
        return True
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task.
        
        Args:
            task: Dictionary containing task details
            
        Returns:
            Dict containing task execution results
        """
        self._logger.info(f"Executing task: {task.get('name', 'unnamed')}")
        
        # Task execution logic would go here
        result = {
            "task_id": task.get("id"),
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id
        }
        
        self._task_history.append(result)
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status and statistics.
        
        Returns:
            Dict containing agent status information
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "tasks_completed": len(self._task_history),
            "has_vault": self.vault is not None
        }
    
    def _generate_agent_id(self) -> str:
        """Generate a unique agent ID.
        
        Returns:
            str: Unique agent identifier
        """
        import uuid
        return f"agent-{uuid.uuid4().hex[:12]}"
    
    def __repr__(self) -> str:
        return f"Agent(id={self.agent_id}, name='{self.name}', status={self.status.value})"
