"""Symbolic Planner for OBLISK.

Provides symbolic reasoning and planning capabilities for agents.
"""

from typing import Dict, List, Optional, Any, Set
from enum import Enum
import logging
from dataclasses import dataclass


class PlanStatus(Enum):
    """Status of a plan."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Action:
    """Represents a symbolic action in a plan."""
    name: str
    parameters: Dict[str, Any]
    preconditions: List[str]
    effects: List[str]
    cost: float = 1.0


@dataclass
class Goal:
    """Represents a goal to be achieved."""
    description: str
    conditions: List[str]
    priority: int = 1


class SymbolicPlanner:
    """Symbolic planner for agent task planning and reasoning.
    
    The SymbolicPlanner provides symbolic AI capabilities including goal
    decomposition, action planning, and logical reasoning for agents.
    
    Attributes:
        actions (Dict): Available actions the planner can use
        plans (Dict): Active and historical plans
        
    Example:
        >>> planner = SymbolicPlanner()
        >>> planner.register_action("move", move_action)
        >>> plan = planner.create_plan(goal, initial_state)
    """
    
    def __init__(self):
        """Initialize the Symbolic Planner."""
        self.actions: Dict[str, Action] = {}
        self.plans: Dict[str, Dict[str, Any]] = {}
        self._logger = logging.getLogger("oblisk.planner")
        self._logger.info("SymbolicPlanner initialized")
    
    def register_action(self, action_id: str, action: Action) -> bool:
        """Register an action that the planner can use.
        
        Args:
            action_id: Unique identifier for the action
            action: Action definition
            
        Returns:
            bool: True if action was registered successfully
        """
        self.actions[action_id] = action
        self._logger.info(f"Action '{action_id}' registered")
        return True
    
    def create_plan(
        self,
        goal: Goal,
        initial_state: Set[str],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Create a plan to achieve a goal from an initial state.
        
        Args:
            goal: The goal to achieve
            initial_state: Set of facts representing initial state
            constraints: Optional planning constraints
            
        Returns:
            Optional[str]: Plan ID if plan was created, None otherwise
        """
        import uuid
        plan_id = f"plan-{uuid.uuid4().hex[:12]}"
        
        # Simple forward search planning (can be extended with more sophisticated algorithms)
        action_sequence = self._forward_search(goal, initial_state, constraints or {})
        
        if action_sequence is None:
            self._logger.warning(f"Failed to create plan for goal: {goal.description}")
            return None
        
        plan = {
            "plan_id": plan_id,
            "goal": goal,
            "initial_state": initial_state,
            "actions": action_sequence,
            "status": PlanStatus.PENDING,
            "current_step": 0
        }
        
        self.plans[plan_id] = plan
        self._logger.info(f"Plan '{plan_id}' created with {len(action_sequence)} actions")
        return plan_id
    
    def _forward_search(
        self,
        goal: Goal,
        state: Set[str],
        constraints: Dict[str, Any]
    ) -> Optional[List[Action]]:
        """Perform forward search to find action sequence.
        
        Args:
            goal: Goal to achieve
            state: Current state
            constraints: Planning constraints
            
        Returns:
            Optional list of actions, or None if no plan found
        """
        # Simple greedy search (can be replaced with A*, etc.)
        plan: List[Action] = []
        current_state = state.copy()
        max_depth = constraints.get("max_depth", 10)
        
        for _ in range(max_depth):
            # Check if goal is satisfied
            if self._check_goal(goal, current_state):
                return plan
            
            # Find applicable actions
            applicable = self._get_applicable_actions(current_state)
            
            if not applicable:
                break
            
            # Select best action (simple heuristic: choose first applicable)
            action = applicable[0]
            plan.append(action)
            
            # Apply effects
            current_state = self._apply_action(action, current_state)
        
        # Check if goal achieved
        if self._check_goal(goal, current_state):
            return plan
        
        return None
    
    def _get_applicable_actions(self, state: Set[str]) -> List[Action]:
        """Get actions whose preconditions are satisfied in current state.
        
        Args:
            state: Current state
            
        Returns:
            List of applicable actions
        """
        applicable = []
        for action in self.actions.values():
            if all(precond in state for precond in action.preconditions):
                applicable.append(action)
        return applicable
    
    def _apply_action(self, action: Action, state: Set[str]) -> Set[str]:
        """Apply an action's effects to a state.
        
        Args:
            action: Action to apply
            state: Current state
            
        Returns:
            New state after applying action
        """
        new_state = state.copy()
        for effect in action.effects:
            if effect.startswith("NOT_"):
                # Negative effect (remove fact)
                fact = effect[4:]
                new_state.discard(fact)
            else:
                # Positive effect (add fact)
                new_state.add(effect)
        return new_state
    
    def _check_goal(self, goal: Goal, state: Set[str]) -> bool:
        """Check if goal conditions are satisfied in state.
        
        Args:
            goal: Goal to check
            state: Current state
            
        Returns:
            bool: True if goal is satisfied
        """
        return all(condition in state for condition in goal.conditions)
    
    def execute_plan(self, plan_id: str) -> bool:
        """Mark a plan as being executed.
        
        Args:
            plan_id: ID of the plan to execute
            
        Returns:
            bool: True if plan execution started
        """
        if plan_id not in self.plans:
            return False
        
        plan = self.plans[plan_id]
        plan["status"] = PlanStatus.IN_PROGRESS
        self._logger.info(f"Plan '{plan_id}' execution started")
        return True
    
    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a plan by ID.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Optional plan data
        """
        return self.plans.get(plan_id)
    
    def get_plan_status(self, plan_id: str) -> Optional[PlanStatus]:
        """Get the status of a plan.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Optional plan status
        """
        plan = self.plans.get(plan_id)
        return plan["status"] if plan else None
    
    def __repr__(self) -> str:
        return f"SymbolicPlanner(actions={len(self.actions)}, plans={len(self.plans)})"
