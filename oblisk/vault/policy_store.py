"""
Policy Store — User-Authored Governance Rules

The PolicyStore manages hard logical constraints that govern agent behavior.
Policies are written in Prolog/Datalog syntax and stored encrypted in the vault.

Principle: The human writes the law. The constraint engine enforces it.
"""

from __future__ import annotations

import re
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class ConstraintType(Enum):
    """Types of hard constraints a human can set."""
    NEVER_LEAVE_DEVICE = "never_leaves_device"      # Data locality
    NEVER_SHARE = "never_share"                       # No external sharing
    REQUIRES_EXPLICIT_APPROVAL = "requires_approval"  # Human must approve each action
    RATE_LIMITED = "rate_limited"                     # Max actions per time window
    TIME_BOUND = "time_bound"                         # Only active during certain hours
    DOMAIN_RESTRICTED = "domain_restricted"           # Only specific domains/apis
    CUSTOM = "custom"                                 # Arbitrary Prolog/Datalog rule


@dataclass
class Policy:
    """
    A single governance rule authored by the human.
    
    Policies are the user's law. They constrain what agents can do,
    what data can leave the device, and what requires explicit approval.
    
    Attributes:
        id: Unique policy identifier (human-readable)
        constraint_type: Category of constraint
        rule: Prolog/Datalog syntax rule string
        description: Human-readable explanation
        active: Whether this policy is currently enforced
        priority: Resolution priority (higher = more important)
        metadata: Additional policy parameters
    """
    id: str
    constraint_type: ConstraintType
    rule: str
    description: str
    active: bool = True
    priority: int = 100
    metadata: dict = field(default_factory=dict)
    
    def to_datalog(self) -> str:
        """
        Convert policy to standard Datalog format.
        
        Example:
            location_data(X) :- never_leaves_device(X).
            outbound_transfer(X) :- requires_approval(X), user_consented(X).
        """
        if self.constraint_type == ConstraintType.CUSTOM:
            return self.rule
        
        # Auto-generate Datalog from structured policy
        predicate = self._get_predicate()
        return f"{predicate}(X) :- {self.constraint_type.value}(X)."
    
    def _get_predicate(self) -> str:
        """Map constraint type to Datalog predicate."""
        mapping = {
            ConstraintType.NEVER_LEAVE_DEVICE: "location_data",
            ConstraintType.NEVER_SHARE: "sensitive_data",
            ConstraintType.REQUIRES_EXPLICIT_APPROVAL: "outbound_transfer",
            ConstraintType.RATE_LIMITED: "agent_action",
            ConstraintType.TIME_BOUND: "agent_action",
            ConstraintType.DOMAIN_RESTRICTED: "api_call",
            ConstraintType.CUSTOM: "custom_constraint",
        }
        return mapping.get(self.constraint_type, "constraint")
    
    def validate_rule(self) -> tuple[bool, Optional[str]]:
        """
        Validate the Datalog rule syntax.
        
        Returns:
            (is_valid, error_message)
        """
        # Basic syntax validation for Datalog
        if not self.rule or not self.rule.strip():
            return False, "Rule cannot be empty"
        
        # Check for balanced parentheses
        parens = 0
        for char in self.rule:
            if char == '(':
                parens += 1
            elif char == ')':
                parens -= 1
            if parens < 0:
                return False, "Unbalanced parentheses in rule"
        
        if parens != 0:
            return False, "Unbalanced parentheses in rule"
        
        # Check for unsafe constructs
        unsafe = ['eval', 'exec', 'import', '__', 'os.', 'subprocess']
        for token in unsafe:
            if token in self.rule.lower():
                return False, f"Unsafe construct '{token}' detected in rule"
        
        return True, None


class PolicyStore:
    """
    Manages the collection of user-authored governance rules.
    
    The PolicyStore is the user's law book. All policies are encrypted
    at rest in the vault and only decrypted when the constraint engine
    needs to verify a proof tree.
    
    Attributes:
        vault: Reference to the encrypted vault
        _policies: In-memory cache of active policies
    """
    
    def __init__(self, vault):
        self.vault = vault
        self._policies: dict[str, Policy] = {}
        self._load_policies()
    
    def _load_policies(self) -> None:
        """Load policies from vault into memory."""
        raw_policies = self.vault.get("_policies", [])
        for raw in raw_policies:
            try:
                policy = Policy(
                    id=raw["id"],
                    constraint_type=ConstraintType(raw.get("constraint_type", "custom")),
                    rule=raw["rule"],
                    description=raw.get("description", ""),
                    active=raw.get("active", True),
                    priority=raw.get("priority", 100),
                    metadata=raw.get("metadata", {}),
                )
                self._policies[policy.id] = policy
            except (KeyError, ValueError) as e:
                # Log but don't crash on corrupted policy
                print(f"Warning: Skipping corrupted policy: {e}")
    
    def set_hard_constraint(self, rule: str, policy_id: Optional[str] = None) -> Policy:
        """
        Set a hard constraint rule.
        
        The rule is Prolog/Datalog syntax that defines what agents
        cannot do without explicit human approval.
        
        Args:
            rule: Prolog/Datalog syntax rule, e.g.
                  "location_data(X) :- never_leaves_device(X)."
            policy_id: Optional human-readable identifier
            
        Returns:
            The created Policy object
            
        Example:
            >>> policy_store.set_hard_constraint(
            ...     "location_data(X) :- never_leaves_device(X).",
            ...     policy_id="no_location_sharing"
            ... )
        """
        policy_id = policy_id or f"policy_{len(self._policies)}"
        
        policy = Policy(
            id=policy_id,
            constraint_type=ConstraintType.CUSTOM,
            rule=rule,
            description=f"Hard constraint: {rule}",
        )
        
        # Validate before storing
        is_valid, error = policy.validate_rule()
        if not is_valid:
            raise ValueError(f"Invalid rule: {error}")
        
        self._policies[policy_id] = policy
        self._persist()
        
        return policy
    
    def add_policy(self, policy: Policy) -> None:
        """Add a fully-constructed Policy object."""
        is_valid, error = policy.validate_rule()
        if not is_valid:
            raise ValueError(f"Invalid policy: {error}")
        
        self._policies[policy.id] = policy
        self._persist()
    
    def remove_policy(self, policy_id: str) -> bool:
        """Remove a policy by ID. Returns True if found and removed."""
        if policy_id in self._policies:
            del self._policies[policy_id]
            self._persist()
            return True
        return False
    
    def get_active_policies(self) -> list[Policy]:
        """Get all currently active policies, sorted by priority."""
        active = [p for p in self._policies.values() if p.active]
        return sorted(active, key=lambda p: -p.priority)
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get a specific policy by ID."""
        return self._policies.get(policy_id)
    
    def to_datalog_program(self) -> str:
        """
        Export all active policies as a Datalog program.
        
        This is used by the ConstraintEngine to verify proof trees.
        
        Returns:
            Complete Datalog program as a string
        """
        lines = [
            "% OBLISK Policy Store — Auto-generated Datalog",
            f"% {len(self.get_active_policies())} active policies",
            "",
        ]
        
        for policy in self.get_active_policies():
            lines.append(f"% {policy.id}: {policy.description}")
            lines.append(policy.to_datalog())
            lines.append("")
        
        return "\n".join(lines)
    
    def _persist(self) -> None:
        """Save policies back to the vault."""
        raw_policies = []
        for policy in self._policies.values():
            raw_policies.append({
                "id": policy.id,
                "constraint_type": policy.constraint_type.value,
                "rule": policy.rule,
                "description": policy.description,
                "active": policy.active,
                "priority": policy.priority,
                "metadata": policy.metadata,
            })
        self.vault.set("_policies", raw_policies)
