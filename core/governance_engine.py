"""Governance Engine for OBLISK.

Provides policy enforcement, decision auditing, and governance mechanisms.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import logging
import json


class PolicyDecision(Enum):
    """Enumeration of policy decision outcomes."""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRES_REVIEW = "requires_review"


class GovernanceEngine:
    """Governance engine for policy enforcement and audit trail management.
    
    The GovernanceEngine provides centralized governance for agent actions,
    policy enforcement, and maintains an immutable audit trail of all decisions.
    
    Attributes:
        policies (Dict): Active governance policies
        audit_log (List): Chronological audit trail of all governance decisions
        
    Example:
        >>> governance = GovernanceEngine()
        >>> governance.add_policy("data_access", policy_definition)
        >>> decision = governance.evaluate_action(agent_id, action)
    """
    
    def __init__(self):
        """Initialize the Governance Engine."""
        self.policies: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self._logger = logging.getLogger("oblisk.governance")
        self._logger.info("GovernanceEngine initialized")
    
    def add_policy(self, policy_id: str, policy: Dict[str, Any]) -> bool:
        """Add or update a governance policy.
        
        Args:
            policy_id: Unique identifier for the policy
            policy: Policy definition including rules and constraints
            
        Returns:
            bool: True if policy was added successfully
        """
        self.policies[policy_id] = {
            "definition": policy,
            "created_at": datetime.now().isoformat(),
            "enabled": True
        }
        self._logger.info(f"Policy '{policy_id}' added")
        self._audit("policy_added", {"policy_id": policy_id})
        return True
    
    def remove_policy(self, policy_id: str) -> bool:
        """Remove a governance policy.
        
        Args:
            policy_id: Unique identifier for the policy
            
        Returns:
            bool: True if policy was removed, False if not found
        """
        if policy_id in self.policies:
            del self.policies[policy_id]
            self._logger.info(f"Policy '{policy_id}' removed")
            self._audit("policy_removed", {"policy_id": policy_id})
            return True
        return False
    
    def evaluate_action(
        self,
        agent_id: str,
        action: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> PolicyDecision:
        """Evaluate an agent action against governance policies.
        
        Args:
            agent_id: ID of the agent requesting the action
            action: Action details to evaluate
            context: Optional contextual information
            
        Returns:
            PolicyDecision: The governance decision (ALLOW, DENY, or REQUIRES_REVIEW)
        """
        decision_data = {
            "agent_id": agent_id,
            "action": action,
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Evaluate action against all active policies
        for policy_id, policy_data in self.policies.items():
            if not policy_data["enabled"]:
                continue
            
            policy = policy_data["definition"]
            
            # Check if policy applies to this action type
            if "action_types" in policy:
                action_type = action.get("type")
                if action_type and action_type not in policy["action_types"]:
                    continue
            
            # Evaluate rules
            if "rules" in policy:
                for rule in policy["rules"]:
                    if self._evaluate_rule(rule, agent_id, action, context):
                        decision = PolicyDecision(rule.get("decision", "deny"))
                        decision_data["policy_id"] = policy_id
                        decision_data["rule"] = rule.get("name", "unnamed")
                        decision_data["decision"] = decision.value
                        self._audit("action_evaluated", decision_data)
                        return decision
        
        # Default to ALLOW if no policy denies
        decision = PolicyDecision.ALLOW
        decision_data["decision"] = decision.value
        self._audit("action_evaluated", decision_data)
        return decision
    
    def _evaluate_rule(
        self,
        rule: Dict[str, Any],
        agent_id: str,
        action: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """Evaluate a single policy rule.
        
        Args:
            rule: The rule to evaluate
            agent_id: Agent ID
            action: Action being evaluated
            context: Contextual information
            
        Returns:
            bool: True if rule matches, False otherwise
        """
        # Simple rule evaluation logic (can be extended)
        conditions = rule.get("conditions", {})
        
        # Check agent condition
        if "agent_id" in conditions:
            if agent_id != conditions["agent_id"]:
                return False
        
        # Check action properties
        if "action_properties" in conditions:
            for key, value in conditions["action_properties"].items():
                if action.get(key) != value:
                    return False
        
        return True
    
    def get_audit_log(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve audit log entries.
        
        Args:
            agent_id: Optional filter by agent ID
            limit: Maximum number of entries to return
            
        Returns:
            List of audit log entries
        """
        logs = self.audit_log
        
        if agent_id:
            logs = [log for log in logs if log.get("data", {}).get("agent_id") == agent_id]
        
        return logs[-limit:]
    
    def _audit(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record an event in the audit log.
        
        Args:
            event_type: Type of event being audited
            data: Event data to record
        """
        audit_entry = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.audit_log.append(audit_entry)
        self._logger.debug(f"Audited: {event_type}")
    
    def export_audit_log(self, filepath: str) -> bool:
        """Export audit log to a file.
        
        Args:
            filepath: Path where to save the audit log
            
        Returns:
            bool: True if export successful
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.audit_log, f, indent=2)
            self._logger.info(f"Audit log exported to {filepath}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to export audit log: {e}")
            return False
    
    def get_policy_stats(self) -> Dict[str, Any]:
        """Get statistics about governance policies.
        
        Returns:
            Dict containing policy statistics
        """
        enabled_count = sum(1 for p in self.policies.values() if p["enabled"])
        return {
            "total_policies": len(self.policies),
            "enabled_policies": enabled_count,
            "disabled_policies": len(self.policies) - enabled_count,
            "audit_log_size": len(self.audit_log)
        }
    
    def __repr__(self) -> str:
        return f"GovernanceEngine(policies={len(self.policies)}, audit_entries={len(self.audit_log)})"
