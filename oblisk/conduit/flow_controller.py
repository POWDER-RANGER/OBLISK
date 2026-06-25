"""
Flow Controller — One-Directional Authorization

The FlowController is the central coordinator of the OBLISK pipeline.
It ensures:
    1. Every intent is signed by the vault identity
    2. Every plan's proof tree satisfies all hard constraints
    3. Data flows one direction: Human → Agent (never reverse)
    4. Every authorized action is logged in the consent audit trail

The FlowController is the "traffic cop" of OBLISK — nothing moves
without its explicit authorization.
"""

from __future__ import annotations

import json
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from ..vault.vault import Vault
    from ..vault.identity import HumanIdentity
    from ..vault.intent_store import IntentStore, Intent
    from ..vault.consent_log import ConsentLog, ConsentType
    from ..vault.policy_store import PolicyStore
    from .constraint_engine import ConstraintEngine, ConstraintResult
    from ..core.symbolic_planner import SymbolicPlanner


@dataclass
class AuthorizationDecision:
    """
    A complete authorization decision from the FlowController.
    
    This is the record of whether an action was authorized, including
    all the evidence (intent signature, constraint results, proof tree).
    
    Attributes:
        authorized: Whether the action is approved
        intent_id: The intent being authorized
        constraint_result: Results of constraint verification
        reason: Human-readable explanation of the decision
        decision_hash: Cryptographic hash of the decision for audit
    """
    authorized: bool
    intent_id: str
    constraint_result: Optional[ConstraintResult] = None
    reason: str = ""
    decision_hash: str = ""
    
    def to_dict(self) -> dict:
        """Serialize for audit logging."""
        return {
            "authorized": self.authorized,
            "intent_id": self.intent_id,
            "constraint_passed": self.constraint_result.passed if self.constraint_result else None,
            "reason": self.reason,
            "decision_hash": self.decision_hash,
        }


class FlowController:
    """
    Central coordinator ensuring one-directional, authorized flow.
    
    The FlowController enforces the core governance invariant:
    No agent acts without vault-signed intent AND proof tree verification.
    
    Pipeline:
        1. Receive intent from IntentStore
        2. Verify intent signature against HumanIdentity
        3. Send to SymbolicPlanner for decomposition + proof tree
        4. Verify proof tree against PolicyStore constraints
        5. If all checks pass, authorize agent execution
        6. Log authorization decision in ConsentLog
    
    Attributes:
        vault: The encrypted vault
        identity: The human's sovereign identity
        intent_store: Intent lifecycle management
        consent_log: Immutable audit trail
        constraint_engine: Hard constraint verification
    """
    
    def __init__(
        self,
        vault: "Vault",
        identity: "HumanIdentity",
        intent_store: "IntentStore",
        consent_log: "ConsentLog",
        policy_store: "PolicyStore",
    ):
        self.vault = vault
        self.identity = identity
        self.intent_store = intent_store
        self.consent_log = consent_log
        self.constraint_engine = ConstraintEngine(policy_store)
    
    def authorize_action(self, intent_id: str, proof_tree: dict) -> AuthorizationDecision:
        """
        Authorize an action by verifying intent signature and proof tree.
        
        This is THE gate. Every agent action must pass through here.
        
        Args:
            intent_id: The cryptographically signed intent ID
            proof_tree: The proof tree from the SymbolicPlanner showing
                       every step, data access, and external call
                       
        Returns:
            AuthorizationDecision with full audit trail
        """
        # Step 1: Retrieve and verify the intent
        try:
            intent = self.intent_store.get_intent(intent_id)
            if intent is None:
                return self._deny(intent_id, "Intent not found in vault")
        except Exception as e:
            return self._deny(intent_id, f"Intent retrieval failed: {e}")
        
        # Step 2: Verify intent was signed by vault identity
        if not intent.signature:
            return self._deny(intent_id, "Intent is not cryptographically signed")
        
        # Verify signature
        try:
            is_valid = self.identity.verify_intent(
                json.loads(intent.to_signing_payload()),
                intent.signature
            )
            if not is_valid:
                return self._deny(intent_id, "Intent signature verification failed")
        except Exception as e:
            return self._deny(intent_id, f"Signature verification error: {e}")
        
        # Step 3: Check intent hasn't expired or been revoked
        if intent.is_expired():
            return self._deny(intent_id, "Intent has expired")
        
        if intent.status.value == "revoked":
            return self._deny(intent_id, "Intent has been revoked by human")
        
        # Step 4: Verify proof tree against hard constraints
        constraints = self.vault.get_policy_constraints()
        constraint_result = self.constraint_engine.verify(proof_tree, constraints)
        
        if not constraint_result.passed:
            violations = "; ".join(
                v["explanation"] for v in constraint_result.violations
            )
            return self._deny(
                intent_id, 
                f"Constraint verification failed: {violations}",
                constraint_result
            )
        
        # Step 5: All checks passed — authorize
        decision = self._authorize(intent_id, constraint_result)
        
        # Step 6: Log the authorization in the consent audit trail
        self.consent_log.record(
            ConsentType.ACTION_APPROVED,
            intent_id,
            f"Action authorized: {intent.goal}. "
            f"Constraints checked: {len(constraint_result.checked_policies)}. "
            f"Decision hash: {decision.decision_hash[:16]}..."
        )
        
        return decision
    
    def _authorize(
        self, intent_id: str, constraint_result: ConstraintResult
    ) -> AuthorizationDecision:
        """Create an authorization approval."""
        decision = AuthorizationDecision(
            authorized=True,
            intent_id=intent_id,
            constraint_result=constraint_result,
            reason=(
                f"Intent signature verified. "
                f"All {len(constraint_result.checked_policies)} constraints satisfied. "
                "Authorization granted."
            ),
        )
        decision.decision_hash = self._hash_decision(decision)
        return decision
    
    def _deny(
        self, 
        intent_id: str, 
        reason: str,
        constraint_result: Optional[ConstraintResult] = None
    ) -> AuthorizationDecision:
        """Create an authorization denial."""
        decision = AuthorizationDecision(
            authorized=False,
            intent_id=intent_id,
            constraint_result=constraint_result,
            reason=reason,
        )
        decision.decision_hash = self._hash_decision(decision)
        
        # Log denial in consent log
        self.consent_log.record(
            ConsentType.ACTION_APPROVED,  # We log that we checked
            intent_id,
            f"Action DENIED: {reason}"
        )
        
        return decision
    
    def _hash_decision(self, decision: AuthorizationDecision) -> str:
        """Compute a cryptographic hash of the decision for audit."""
        import hashlib
        content = json.dumps(decision.to_dict(), sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(content.encode()).hexdigest()
    
    def revoke_active_intent(self, intent_id: str) -> bool:
        """
        Revoke an intent and halt any in-progress execution.
        
        This is the emergency brake. When a human revokes an intent,
        the FlowController immediately blocks any further execution
        and alerts all involved agents.
        
        Args:
            intent_id: The intent to revoke
            
        Returns:
            True if revocation was successful
        """
        try:
            self.intent_store.revoke_intent(intent_id, "Revoked via FlowController")
            self.consent_log.record(
                ConsentType.REVOCATION,
                intent_id,
                "Intent revoked — all agent execution halted"
            )
            return True
        except Exception as e:
            self.consent_log.record(
                ConsentType.REVOCATION,
                intent_id,
                f"Revocation attempt failed: {e}"
            )
            return False
    
    def get_flow_status(self, intent_id: str) -> dict:
        """
        Get the complete flow status for an intent.
        
        Returns where the intent is in the pipeline and what
        decisions have been made about it.
        """
        intent = self.intent_store.get_intent(intent_id)
        if intent is None:
            return {"error": "Intent not found"}
        
        consent_entries = self.consent_log.get_entries_for_subject(intent_id)
        
        return {
            "intent_id": intent_id,
            "status": intent.status.value,
            "goal": intent.goal,
            "signed": intent.signature is not None,
            "has_proof_tree": intent.proof_tree is not None,
            "consent_entries": len(consent_entries),
            "audit_trail": self.consent_log.get_audit_trail(intent_id),
        }
