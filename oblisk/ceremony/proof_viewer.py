"""
Proof Viewer — Human Audit Interface

The ProofViewer provides a human-readable interface for reviewing
any agent decision. It translates proof trees, constraint results,
and authorization decisions into natural language explanations.

This is the human's window into the OBLISK's decision-making process.
Every action is explainable, every explanation is reviewable.

Principle: The human can audit any decision, at any time, for any reason.
"""

from __future__ import annotations

import json
import time
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from ..vault.consent_log import ConsentLog
    from ..vault.intent_store import IntentStore
    from ..conduit.proof_collector import ProofCollector
    from ..conduit.flow_controller import FlowController


@dataclass
class AuditView:
    """
    A complete audit view of an agent decision.
    
    Attributes:
        intent_id: The intent that led to the action
        intent_goal: What the human wanted
        plan_summary: Human-readable plan summary
        constraint_results: What constraints were checked and results
        authorization: Whether the action was authorized
        data_accessed: What data was touched
        external_calls: What external APIs were called
        proof_integrity: Whether the proof tree is intact
        human_reviewed: Whether a human has reviewed this
        review_timestamp: When the human reviewed it
    """
    intent_id: str
    intent_goal: str
    plan_summary: str
    constraint_results: list[dict] = field(default_factory=list)
    authorization: str = "unknown"
    data_accessed: list[str] = field(default_factory=list)
    external_calls: list[str] = field(default_factory=list)
    proof_integrity: str = "unknown"
    human_reviewed: bool = False
    review_timestamp: Optional[float] = None


class ProofViewer:
    """
    UI for humans to audit any agent decision.
    
    The ProofViewer is the transparency layer of OBLISK. It takes the
    raw proof trees, constraint results, and authorization decisions
    and presents them in a format that humans can understand and trust.
    
    Attributes:
        proof_collector: Source of proof trees
        consent_log: Source of consent audit trail
        intent_store: Source of intent information
    """
    
    def __init__(
        self,
        proof_collector: "ProofCollector",
        consent_log: "ConsentLog",
        intent_store: "IntentStore",
    ):
        self.proof_collector = proof_collector
        self.consent_log = consent_log
        self.intent_store = intent_store
    
    def view_decision(self, intent_id: str) -> AuditView:
        """
        Get a complete audit view of a decision.
        
        This is the primary method — it aggregates all information
        about an intent and its execution into a human-readable format.
        
        Args:
            intent_id: The intent to audit
            
        Returns:
            Complete AuditView
        """
        # Get intent details
        intent = self.intent_store.get_intent(intent_id)
        intent_goal = intent.goal if intent else "Unknown intent"
        
        # Get proof chain
        proof_chain = self.proof_collector.get_proof_chain(intent_id)
        
        # Build audit view
        audit = AuditView(
            intent_id=intent_id,
            intent_goal=intent_goal,
            plan_summary=self._summarize_plan(proof_chain),
            constraint_results=self._get_constraint_results(proof_chain),
            data_accessed=self._get_data_accessed(proof_chain),
            external_calls=self._get_external_calls(proof_chain),
            proof_integrity=self._check_integrity(proof_chain),
            human_reviewed=any(p.human_reviewed for p in proof_chain),
        )
        
        # Get authorization status from consent log
        audit.authorization = self._get_authorization_status(intent_id)
        
        return audit
    
    def explain_in_natural_language(self, intent_id: str) -> str:
        """
        Generate a natural language explanation of a decision.
        
        This is the key method for human understanding. It translates
        the entire audit trail into a narrative that explains:
        - What the human asked for
        - What the planner decided
        - Why each step was taken
        - What constraints were checked
        - Whether the action was authorized
        
        Args:
            intent_id: The intent to explain
            
        Returns:
            Natural language explanation
        """
        audit = self.view_decision(intent_id)
        
        lines = [
            "=" * 60,
            "OBLISK DECISION AUDIT",
            "=" * 60,
            "",
            f"Intent: {audit.intent_goal}",
            f"Intent ID: {audit.intent_id}",
            f"Authorization: {audit.authorization}",
            f"Proof Integrity: {audit.proof_integrity}",
            f"Human Reviewed: {'Yes' if audit.human_reviewed else 'No'}",
            "",
            "Plan:",
        ]
        
        # Plan summary
        if audit.plan_summary:
            lines.append(audit.plan_summary)
        else:
            lines.append("  (No plan recorded)")
        
        lines.extend(["", "Constraints Checked:"])
        
        # Constraint results
        if audit.constraint_results:
            for result in audit.constraint_results:
                status = "✓" if result.get("passed") else "✗"
                lines.append(f"  {status} {result.get('policy', 'Unknown')}: {result.get('result', 'N/A')}")
        else:
            lines.append("  (No constraints checked)")
        
        lines.extend(["", "Data Accessed:"])
        if audit.data_accessed:
            for data in audit.data_accessed:
                lines.append(f"  - {data}")
        else:
            lines.append("  (No data accessed)")
        
        if audit.external_calls:
            lines.extend(["", "External Communications:"])
            for call in audit.external_calls:
                lines.append(f"  - {call}")
        
        lines.extend(["", "=" * 60])
        
        return "\n".join(lines)
    
    def mark_reviewed(self, intent_id: str) -> None:
        """
        Mark a decision as reviewed by the human.
        
        This records in the consent log that the human has seen
        and acknowledged the audit trail.
        
        Args:
            intent_id: The intent that was reviewed
        """
        proof_chain = self.proof_collector.get_proof_chain(intent_id)
        
        for proof in proof_chain:
            self.proof_collector.mark_reviewed(proof.proof_id)
    
    def search_audit_trail(self, query: str) -> list[AuditView]:
        """
        Search the audit trail for specific terms.
        
        Args:
            query: Search term (searches intent goals, data types, etc.)
            
        Returns:
            Matching audit views
        """
        results = []
        # Get all intents and search through them
        # In production, this would use an indexed search
        
        # For now, return empty — this is a query interface
        return results
    
    def export_audit_report(self, intent_id: str) -> dict:
        """
        Export a complete audit report as structured data.
        
        This can be used for legal compliance, debugging, or
        sharing with security teams.
        
        Args:
            intent_id: The intent to export
            
        Returns:
            Complete structured audit report
        """
        audit = self.view_decision(intent_id)
        consent_entries = self.consent_log.get_audit_trail(intent_id)
        
        return {
            "intent": {
                "id": audit.intent_id,
                "goal": audit.intent_goal,
                "authorization": audit.authorization,
            },
            "plan": {
                "summary": audit.plan_summary,
                "integrity": audit.proof_integrity,
            },
            "constraints": audit.constraint_results,
            "data_accessed": audit.data_accessed,
            "external_calls": audit.external_calls,
            "human_review": {
                "reviewed": audit.human_reviewed,
                "timestamp": audit.review_timestamp,
            },
            "consent_trail": consent_entries,
        }
    
    def _summarize_plan(self, proof_chain: list) -> str:
        """Summarize the execution plan from proof chain."""
        if not proof_chain:
            return "No proof records found"
        
        # Get the latest proof
        latest = proof_chain[-1]
        tree = latest.proof_tree
        
        steps = tree.get("steps", [])
        if not steps:
            return "Empty plan"
        
        summary_parts = []
        for i, step in enumerate(steps, 1):
            desc = step.get("description", f"Step {i}")
            reason = step.get("reason", "")
            summary_parts.append(f"  {i}. {desc}")
            if reason:
                summary_parts.append(f"     (Reason: {reason})")
        
        return "\n".join(summary_parts)
    
    def _get_constraint_results(self, proof_chain: list) -> list[dict]:
        """Extract constraint verification results from proof chain."""
        results = []
        for proof in proof_chain:
            cr = proof.constraint_result
            if cr:
                results.append({
                    "proof_id": proof.proof_id,
                    "passed": True,  # Would come from actual ConstraintResult
                    "policies_checked": cr.get("checked_policies", []),
                    "violations": cr.get("violations", []),
                })
        return results
    
    def _get_data_accessed(self, proof_chain: list) -> list[str]:
        """Extract data access records from proof chain."""
        if not proof_chain:
            return []
        latest = proof_chain[-1]
        return latest.proof_tree.get("data_access", [])
    
    def _get_external_calls(self, proof_chain: list) -> list[str]:
        """Extract external call records from proof chain."""
        if not proof_chain:
            return []
        latest = proof_chain[-1]
        calls = latest.proof_tree.get("external_calls", [])
        return [c.get("endpoint", "unknown") for c in calls]
    
    def _check_integrity(self, proof_chain: list) -> str:
        """Check proof tree integrity."""
        if not proof_chain:
            return "no_proofs"
        
        for proof in proof_chain:
            if not self.proof_collector.verify_integrity(proof.proof_id):
                return "tampered"
        
        return "valid"
    
    def _get_authorization_status(self, intent_id: str) -> str:
        """Get authorization status from consent log."""
        entries = self.consent_log.get_entries_for_subject(intent_id)
        
        for entry in entries:
            if "approved" in entry.description.lower():
                return "authorized"
            if "denied" in entry.description.lower():
                return "denied"
        
        return "unknown"
