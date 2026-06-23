"""
Intent Store — Cryptographically Signed Human Intents

The IntentStore manages human intents that have been cryptographically signed
by the vault identity. These signed intents are the only authorization tokens
that allow agents to act on behalf of the human.

Principle: If it's not signed by the vault, the agent doesn't act.
"""

from __future__ import annotations

import json
import hashlib
import time
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum


class IntentStatus(Enum):
    """Lifecycle states of a human intent."""
    PENDING = "pending"         # Created, awaiting human confirmation
    SIGNED = "signed"           # Signed by human identity, ready for planning
    PLANNING = "planning"       # SymbolicPlanner is decomposing
    APPROVED = "approved"       # Plan + proof tree approved by FlowController
    EXECUTING = "executing"     # Agents are carrying out the plan
    COMPLETED = "completed"     # All steps executed successfully
    REVOKED = "revoked"         # Human revoked intent before/during execution
    EXPIRED = "expired"         # Intent exceeded time-to-live


@dataclass
class Intent:
    """
    A human intent that has been cryptographically signed by the vault identity.
    
    This is the authorization token that flows through the entire OBLISK pipeline.
    Every agent action traces back to a vault-signed Intent.
    
    Attributes:
        id: Unique intent identifier (hash of content + timestamp)
        goal: Natural language description of what the human wants
        constraints: Additional runtime constraints beyond vault policies
        status: Current lifecycle state
        signature: Ed25519 signature from HumanIdentity
        created_at: Unix timestamp of creation
        expires_at: Optional expiration timestamp
        proof_tree: Generated proof tree from SymbolicPlanner (filled during planning)
        audit_log: Chronological record of all state transitions
    """
    id: str
    goal: str
    constraints: list[str] = field(default_factory=list)
    status: IntentStatus = IntentStatus.PENDING
    signature: Optional[bytes] = None
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    proof_tree: Optional[dict] = None
    audit_log: list[dict] = field(default_factory=list)
    
    def is_expired(self) -> bool:
        """Check if intent has exceeded its time-to-live."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def is_active(self) -> bool:
        """Check if intent is currently active (signed, not expired, not revoked)."""
        return (
            self.status in (IntentStatus.SIGNED, IntentStatus.PLANNING, IntentStatus.APPROVED, IntentStatus.EXECUTING)
            and not self.is_expired()
        )
    
    def to_signing_payload(self) -> str:
        """Generate the canonical payload that gets signed."""
        payload = {
            "id": self.id,
            "goal": self.goal,
            "constraints": self.constraints,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }
        return json.dumps(payload, sort_keys=True, separators=(',', ':'))
    
    def record_transition(self, from_status: IntentStatus, to_status: IntentStatus, reason: str = "") -> None:
        """Record a state transition in the audit log."""
        self.audit_log.append({
            "from": from_status.value,
            "to": to_status.value,
            "timestamp": time.time(),
            "reason": reason,
        })
        self.status = to_status


class IntentStore:
    """
    Manages the lifecycle of cryptographically signed human intents.
    
    The IntentStore is where human will enters the OBLISK system. Every intent
    is signed by the vault identity before any agent can act on it.
    
    Attributes:
        vault: Reference to the encrypted vault
        identity: The HumanIdentity used for signing
        _intents: In-memory cache of intents
    """
    
    def __init__(self, vault, identity):
        self.vault = vault
        self.identity = identity
        self._intents: dict[str, Intent] = {}
        self._load_intents()
    
    def _load_intents(self) -> None:
        """Load intents from vault into memory."""
        raw_intents = self.vault.get("_intents", {})
        for intent_id, raw in raw_intents.items():
            try:
                intent = Intent(
                    id=raw["id"],
                    goal=raw["goal"],
                    constraints=raw.get("constraints", []),
                    status=IntentStatus(raw.get("status", "pending")),
                    signature=raw.get("signature"),
                    created_at=raw.get("created_at", 0),
                    expires_at=raw.get("expires_at"),
                    proof_tree=raw.get("proof_tree"),
                    audit_log=raw.get("audit_log", []),
                )
                self._intents[intent_id] = intent
            except (KeyError, ValueError) as e:
                print(f"Warning: Skipping corrupted intent {intent_id}: {e}")
    
    def create_intent(self, goal: str, constraints: Optional[list[str]] = None, ttl_seconds: Optional[float] = None) -> Intent:
        """
        Create a new human intent (unsigned, pending confirmation).
        
        Args:
            goal: Natural language description of what the human wants
            constraints: Additional runtime constraints
            ttl_seconds: Time-to-live in seconds (None = no expiration)
            
        Returns:
            Unsigned Intent awaiting human signature
        """
        # Generate deterministic ID from goal + current time
        content = f"{goal}:{time.time()}"
        intent_id = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        expires_at = None
        if ttl_seconds:
            expires_at = time.time() + ttl_seconds
        
        intent = Intent(
            id=intent_id,
            goal=goal,
            constraints=constraints or [],
            status=IntentStatus.PENDING,
            expires_at=expires_at,
        )
        
        # Log creation
        intent.record_transition(IntentStatus.PENDING, IntentStatus.PENDING, "Intent created")
        
        self._intents[intent_id] = intent
        self._persist_intent(intent)
        
        return intent
    
    def sign_intent(self, intent_id: str) -> Intent:
        """
        Cryptographically sign an intent with the human identity.
        
        This is the critical handoff — the human has reviewed and approved
        the intent, and their signature authorizes the planning phase.
        
        Args:
            intent_id: The intent to sign
            
        Returns:
            The signed Intent
            
        Raises:
            ValueError: If intent not found or already signed
        """
        intent = self._intents.get(intent_id)
        if intent is None:
            raise ValueError(f"Intent {intent_id} not found")
        
        if intent.status != IntentStatus.PENDING:
            raise ValueError(f"Intent {intent_id} is not pending (status: {intent.status.value})")
        
        # Sign the canonical payload
        payload = intent.to_signing_payload()
        intent.signature = self.identity.sign_intent(json.loads(payload))
        
        intent.record_transition(IntentStatus.PENDING, IntentStatus.SIGNED, "Human signed intent")
        self._persist_intent(intent)
        
        return intent
    
    def revoke_intent(self, intent_id: str, reason: str = "Human revoked") -> Intent:
        """
        Revoke a previously signed intent.
        
        Revocation propagates to the FlowController, which halts any
        in-progress execution of this intent's plan.
        
        Args:
            intent_id: The intent to revoke
            reason: Human-readable reason for revocation
            
        Returns:
            The revoked Intent
        """
        intent = self._intents.get(intent_id)
        if intent is None:
            raise ValueError(f"Intent {intent_id} not found")
        
        if intent.status == IntentStatus.REVOKED:
            return intent
        
        old_status = intent.status
        intent.record_transition(old_status, IntentStatus.REVOKED, reason)
        self._persist_intent(intent)
        
        return intent
    
    def get_intent(self, intent_id: str) -> Optional[Intent]:
        """Get an intent by ID."""
        return self._intents.get(intent_id)
    
    def get_active_intents(self) -> list[Intent]:
        """Get all currently active (signed, non-expired) intents."""
        return [i for i in self._intents.values() if i.is_active()]
    
    def get_pending_intents(self) -> list[Intent]:
        """Get all intents awaiting human signature."""
        return [i for i in self._intents.values() if i.status == IntentStatus.PENDING]
    
    def attach_proof_tree(self, intent_id: str, proof_tree: dict) -> None:
        """
        Attach a proof tree from the SymbolicPlanner to an intent.
        
        This is called by the FlowController after plan generation.
        The proof tree becomes part of the permanent audit record.
        """
        intent = self._intents.get(intent_id)
        if intent is None:
            raise ValueError(f"Intent {intent_id} not found")
        
        intent.proof_tree = proof_tree
        intent.record_transition(IntentStatus.PLANNING, IntentStatus.PLANNING, "Proof tree attached")
        self._persist_intent(intent)
    
    def _persist_intent(self, intent: Intent) -> None:
        """Save a single intent to the vault."""
        raw_intents = self.vault.get("_intents", {})
        raw_intents[intent.id] = {
            "id": intent.id,
            "goal": intent.goal,
            "constraints": intent.constraints,
            "status": intent.status.value,
            "signature": intent.signature.hex() if intent.signature else None,
            "created_at": intent.created_at,
            "expires_at": intent.expires_at,
            "proof_tree": intent.proof_tree,
            "audit_log": intent.audit_log,
        }
        self.vault.set("_intents", raw_intents)
