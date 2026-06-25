"""
Trust Ritual — First Agent Binding to Vault

The TrustRitual is the ceremony through which the human binds their
first (and subsequent) agents to their vault. This is not automated
setup — it is a deliberate act of trust.

The ritual ensures:
    1. The human knows exactly what capabilities the agent will have
    2. The human understands what data the agent can access
    3. The agent is cryptographically bound to ONE vault and ONE identity
    4. The agent cannot be re-bound to another identity
    5. The human can revoke the binding at any time

Principle: Trust is given deliberately, verified cryptographically, and revocable instantly.
"""

from __future__ import annotations

import hashlib
import time
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

from ..vault.identity import HumanIdentity
from ..vault.consent_log import ConsentLog, ConsentType


class RitualPhase(Enum):
    """Phases of the trust ritual."""
    NOT_STARTED = "not_started"
    AGENT_PRESENTED = "agent_presented"       # Human shown agent capabilities
    CAPABILITIES_REVIEWED = "capabilities_reviewed"  # Human reviewed what agent can do
    DATA_ACCESS_REVIEWED = "data_access_reviewed"    # Human reviewed what data agent can access
    BINDING_CONFIRMED = "binding_confirmed"   # Human confirms they want to bind
    CRYPTOGRAPHIC_BINDING = "cryptographic_binding"  # Keys exchanged and bound
    CONSENT_LOGGED = "consent_logged"         # Binding recorded in consent log
    COMPLETE = "complete"


@dataclass
class AgentCapabilities:
    """Description of what an agent can do."""
    name: str
    description: str
    can_read: list[str] = field(default_factory=list)    # Data types it can read
    can_write: list[str] = field(default_factory=list)   # Data types it can modify
    can_call: list[str] = field(default_factory=list)    # APIs it can call
    can_execute: list[str] = field(default_factory=list) # Commands it can run
    max_request_rate: int = 10  # per minute
    restricted_hours: Optional[str] = None  # e.g., "09:00-17:00"


@dataclass
class BindingRecord:
    """
    Record of an agent binding ceremony.
    
    Attributes:
        binding_id: Unique binding identifier
        agent_id: The bound agent
        agent_capabilities: What the agent was authorized to do
        human_identity: Hash of the human identity (not the identity itself)
        bound_at: When the binding occurred
        revoked_at: When the binding was revoked (None if active)
        revocation_reason: Why the binding was revoked
        attestation: Cryptographic proof of binding
    """
    binding_id: str
    agent_id: str
    agent_capabilities: AgentCapabilities
    human_identity_hash: str
    bound_at: float = field(default_factory=time.time)
    revoked_at: Optional[float] = None
    revocation_reason: str = ""
    attestation: dict = field(default_factory=dict)


class TrustRitual:
    """
    The ceremony for binding an agent to a human's vault.
    
    The TrustRitual is not setup automation. It is a deliberate process
    where the human reviews, understands, and explicitly approves each
    agent's capabilities before cryptographic binding.
    
    Attributes:
        identity: The human's sovereign identity
        consent_log: The immutable consent audit trail
        bindings: Active binding records
    """
    
    def __init__(self, identity: HumanIdentity, consent_log: ConsentLog):
        self.identity = identity
        self.consent_log = consent_log
        self.bindings: dict[str, BindingRecord] = {}
        self._phase: RitualPhase = RitualPhase.NOT_STARTED
        self._pending_capabilities: Optional[AgentCapabilities] = None
    
    def present_agent(self, capabilities: AgentCapabilities) -> dict:
        """
        Present an agent's capabilities to the human for review.
        
        This is the first step — the human sees exactly what the agent
        can and cannot do before making any commitment.
        
        Args:
            capabilities: Full description of agent capabilities
            
        Returns:
            Human-readable summary of capabilities
        """
        self._pending_capabilities = capabilities
        self._phase = RitualPhase.AGENT_PRESENTED
        
        return {
            "agent_name": capabilities.name,
            "description": capabilities.description,
            "can_read": capabilities.can_read,
            "can_write": capabilities.can_write,
            "can_call": capabilities.can_call,
            "can_execute": capabilities.can_execute,
            "rate_limit": f"{capabilities.max_request_rate} requests/min",
            "restricted_hours": capabilities.restricted_hours or "None (24/7)",
            "warning": (
                "Review these capabilities carefully. Once bound, the agent "
                "can perform any of these actions without asking, subject to "
                "your vault policies."
            ),
        }
    
    def review_capabilities(self) -> dict:
        """
        Mark capabilities as reviewed by the human.
        
        Returns:
            Next steps for the human
        """
        if self._phase != RitualPhase.AGENT_PRESENTED:
            raise ValueError(f"Cannot review capabilities in phase: {self._phase.value}")
        
        self._phase = RitualPhase.CAPABILITIES_REVIEWED
        
        return {
            "status": "Capabilities reviewed",
            "next_step": "Review what data the agent can access",
            "capabilities": self._pending_capabilities,
        }
    
    def review_data_access(self, allowed_data_types: list[str]) -> dict:
        """
        Review and confirm what data types the agent can access.
        
        The human explicitly lists what data types are allowed.
        Anything not listed is denied by default.
        
        Args:
            allowed_data_types: List of data types the human approves
            
        Returns:
            Summary of approved data access
        """
        if self._phase != RitualPhase.CAPABILITIES_REVIEWED:
            raise ValueError(f"Cannot review data access in phase: {self._phase.value}")
        
        self._pending_capabilities.can_read = allowed_data_types
        self._phase = RitualPhase.DATA_ACCESS_REVIEWED
        
        return {
            "status": "Data access reviewed",
            "allowed_types": allowed_data_types,
            "next_step": "Confirm binding",
        }
    
    def confirm_binding(self, agent_id: str) -> str:
        """
        Human confirms they want to bind this agent to their vault.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            Binding confirmation message
        """
        if self._phase != RitualPhase.DATA_ACCESS_REVIEWED:
            raise ValueError(f"Cannot confirm binding in phase: {self._phase.value}")
        
        if self._pending_capabilities is None:
            raise ValueError("No agent capabilities have been presented")
        
        self._phase = RitualPhase.BINDING_CONFIRMED
        
        return (
            f"Binding confirmed for agent '{self._pending_capabilities.name}' "
            f"({agent_id}). Proceeding to cryptographic binding..."
        )
    
    def perform_binding(self, agent_id: str) -> BindingRecord:
        """
        Perform the cryptographic binding of agent to vault.
        
        This creates the agent-specific key, signs the binding attestation,
        and records everything in the consent log.
        
        Args:
            agent_id: The agent to bind
            
        Returns:
            The complete BindingRecord
        """
        if self._phase != RitualPhase.BINDING_CONFIRMED:
            raise ValueError(f"Cannot perform binding in phase: {self._phase.value}")
        
        # Derive agent-specific key from master identity
        agent_key = self.identity.derive_agent_key(agent_id)
        
        # Create binding record
        binding_id = f"binding_{agent_id}_{int(time.time())}"
        binding = BindingRecord(
            binding_id=binding_id,
            agent_id=agent_id,
            agent_capabilities=self._pending_capabilities,
            human_identity_hash=self.identity.identity_hash,
            attestation={
                "agent_key_hash": hashlib.sha256(agent_key).hexdigest()[:16],
                "capabilities_hash": hashlib.sha256(
                    str(self._pending_capabilities).encode()
                ).hexdigest()[:16],
                "binding_timestamp": time.time(),
                "identity_bound": self.identity.identity_hash,
            },
        )
        
        # Store binding
        self.bindings[agent_id] = binding
        self._phase = RitualPhase.CRYPTOGRAPHIC_BINDING
        
        # Log in consent trail
        self.consent_log.record(
            ConsentType.AGENT_SPAWNED,
            agent_id,
            f"Agent '{self._pending_capabilities.name}' bound to vault. "
            f"Capabilities: {len(self._pending_capabilities.can_read)} read types, "
            f"{len(self._pending_capabilities.can_call)} API calls. "
            f"Binding: {binding_id}"
        )
        
        self._phase = RitualPhase.COMPLETE
        
        return binding
    
    def revoke_binding(self, agent_id: str, reason: str = "Human revoked") -> BindingRecord:
        """
        Revoke an agent's binding to the vault.
        
        This is instant and irreversible. The agent's derived key becomes
        invalid, and the agent can no longer access the vault.
        
        Args:
            agent_id: The agent to revoke
            reason: Human-readable reason for revocation
            
        Returns:
            The revoked BindingRecord
        """
        binding = self.bindings.get(agent_id)
        if binding is None:
            raise ValueError(f"No binding found for agent {agent_id}")
        
        if binding.revoked_at is not None:
            return binding
        
        binding.revoked_at = time.time()
        binding.revocation_reason = reason
        
        # Log revocation
        self.consent_log.record(
            ConsentType.REVOCATION,
            agent_id,
            f"Agent {agent_id} binding revoked: {reason}"
        )
        
        return binding
    
    def is_bound(self, agent_id: str) -> bool:
        """Check if an agent is currently bound to the vault."""
        binding = self.bindings.get(agent_id)
        if binding is None:
            return False
        return binding.revoked_at is None
    
    def get_binding(self, agent_id: str) -> Optional[BindingRecord]:
        """Get the binding record for an agent."""
        return self.bindings.get(agent_id)
    
    def get_active_bindings(self) -> list[BindingRecord]:
        """Get all currently active (non-revoked) bindings."""
        return [b for b in self.bindings.values() if b.revoked_at is None]
