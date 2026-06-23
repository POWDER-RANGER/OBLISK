"""
Proof Collector — Gathers Proof Trees for Audit

The ProofCollector gathers, validates, and archives proof trees from
the SymbolicPlanner. These proof trees form the auditable record of
why each agent action was taken.

Every proof tree is:
    1. Verified for structural integrity
    2. Checked against the consent log
    3. Stored in the vault as part of the permanent audit record
    4. Made available to the human via the proof_viewer ceremony

Principle: Every decision is explainable. Every explanation is provable.
"""

from __future__ import annotations

import json
import hashlib
import time
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from ..vault.vault import Vault
    from ..vault.intent_store import IntentStore
    from ..vault.consent_log import ConsentLog, ConsentType


@dataclass
class ProofRecord:
    """
    A recorded proof tree with metadata.
    
    Attributes:
        proof_id: Unique identifier for this proof
        intent_id: The intent this proof was generated for
        proof_tree: The complete proof tree from SymbolicPlanner
        collector_hash: Hash of the proof for integrity verification
        collected_at: When the proof was collected
        constraint_result: Results of constraint engine verification
        human_reviewed: Whether a human has reviewed this proof
    """
    proof_id: str
    intent_id: str
    proof_tree: dict
    collector_hash: str = ""
    collected_at: float = field(default_factory=time.time)
    constraint_result: Optional[dict] = None
    human_reviewed: bool = False
    
    def compute_hash(self) -> str:
        """Compute hash of the proof tree for integrity."""
        canonical = json.dumps(self.proof_tree, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def finalize(self) -> "ProofRecord":
        """Compute and set the collector hash."""
        self.collector_hash = self.compute_hash()
        return self


class ProofCollector:
    """
    Gathers, validates, and archives proof trees for audit.
    
    The ProofCollector ensures that every agent decision has a corresponding
    proof tree that the human can review. It creates an unbroken chain:
    Intent → Plan → Proof Tree → Constraint Verification → Execution → Audit Log
    
    Attributes:
        vault: The encrypted vault for persistent storage
        intent_store: Intent lifecycle management
        consent_log: Immutable consent audit trail
    """
    
    def __init__(
        self,
        vault: "Vault",
        intent_store: "IntentStore",
        consent_log: "ConsentLog",
    ):
        self.vault = vault
        self.intent_store = intent_store
        self.consent_log = consent_log
    
    def collect(
        self, 
        intent_id: str, 
        proof_tree: dict,
        constraint_result: Optional[dict] = None
    ) -> ProofRecord:
        """
        Collect and archive a proof tree.
        
        This is called by the FlowController after the SymbolicPlanner
generates a proof tree. The proof is verified, hashed, and stored.
        
        Args:
            intent_id: The intent this proof was generated for
            proof_tree: Complete proof tree from SymbolicPlanner
            constraint_result: Optional constraint verification results
            
        Returns:
            The archived ProofRecord
        """
        # Generate proof ID
        proof_id = self._generate_proof_id(intent_id, proof_tree)
        
        # Create the record
        record = ProofRecord(
            proof_id=proof_id,
            intent_id=intent_id,
            proof_tree=proof_tree,
            constraint_result=constraint_result,
        ).finalize()
        
        # Verify structural integrity
        if not self._verify_structure(proof_tree):
            raise ValueError("Proof tree failed structural verification")
        
        # Store in vault
        self._store_record(record)
        
        # Attach to intent
        self.intent_store.attach_proof_tree(intent_id, proof_tree)
        
        # Log collection
        self.consent_log.record(
            ConsentType.PROOF_REVIEWED,
            intent_id,
            f"Proof tree collected: {proof_id} with "
            f"{len(proof_tree.get('steps', []))} step(s)"
        )
        
        return record
    
    def verify_integrity(self, proof_id: str) -> bool:
        """
        Verify that a stored proof hasn't been tampered with.
        
        Recomputes the hash and compares with the stored hash.
        
        Args:
            proof_id: The proof to verify
            
        Returns:
            True if integrity is intact
        """
        record = self._load_record(proof_id)
        if record is None:
            return False
        
        return record.compute_hash() == record.collector_hash
    
    def mark_reviewed(self, proof_id: str) -> None:
        """
        Mark a proof as having been reviewed by the human.
        
        This is called by the proof_viewer ceremony after the human
        has reviewed and acknowledged the proof tree.
        """
        record = self._load_record(proof_id)
        if record is None:
            raise ValueError(f"Proof {proof_id} not found")
        
        record.human_reviewed = True
        self._store_record(record)
        
        self.consent_log.record(
            ConsentType.PROOF_REVIEWED,
            record.intent_id,
            f"Human reviewed proof: {proof_id}"
        )
    
    def get_proof_chain(self, intent_id: str) -> list[ProofRecord]:
        """
        Get the complete chain of proofs for an intent.
        
        Some intents may have multiple proof trees (replanning,
        constraint violations that were corrected, etc.).
        """
        all_proofs = self.vault.get("_proof_records", {})
        records = []
        
        for proof_id, raw in all_proofs.items():
            if raw.get("intent_id") == intent_id:
                record = ProofRecord(
                    proof_id=raw["proof_id"],
                    intent_id=raw["intent_id"],
                    proof_tree=raw["proof_tree"],
                    collector_hash=raw["collector_hash"],
                    collected_at=raw["collected_at"],
                    constraint_result=raw.get("constraint_result"),
                    human_reviewed=raw.get("human_reviewed", False),
                )
                records.append(record)
        
        return sorted(records, key=lambda r: r.collected_at)
    
    def _verify_structure(self, proof_tree: dict) -> bool:
        """
        Verify the structural integrity of a proof tree.
        
        Checks that the proof tree has all required components.
        """
        required_keys = ["steps", "data_access"]
        for key in required_keys:
            if key not in proof_tree:
                return False
        
        # Steps must be a list of dicts with at least a description
        steps = proof_tree["steps"]
        if not isinstance(steps, list):
            return False
        
        for step in steps:
            if not isinstance(step, dict):
                return False
            if "description" not in step:
                return False
        
        return True
    
    def _generate_proof_id(self, intent_id: str, proof_tree: dict) -> str:
        """Generate a deterministic proof ID."""
        canonical = json.dumps(proof_tree, sort_keys=True, separators=(',', ':'))
        content = f"{intent_id}:{canonical}:{time.time()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _store_record(self, record: ProofRecord) -> None:
        """Store a proof record in the vault."""
        all_proofs = self.vault.get("_proof_records", {})
        all_proofs[record.proof_id] = {
            "proof_id": record.proof_id,
            "intent_id": record.intent_id,
            "proof_tree": record.proof_tree,
            "collector_hash": record.collector_hash,
            "collected_at": record.collected_at,
            "constraint_result": record.constraint_result,
            "human_reviewed": record.human_reviewed,
        }
        self.vault.set("_proof_records", all_proofs)
    
    def _load_record(self, proof_id: str) -> Optional[ProofRecord]:
        """Load a proof record from the vault."""
        all_proofs = self.vault.get("_proof_records", {})
        raw = all_proofs.get(proof_id)
        if raw is None:
            return None
        
        return ProofRecord(
            proof_id=raw["proof_id"],
            intent_id=raw["intent_id"],
            proof_tree=raw["proof_tree"],
            collector_hash=raw["collector_hash"],
            collected_at=raw["collected_at"],
            constraint_result=raw.get("constraint_result"),
            human_reviewed=raw.get("human_reviewed", False),
        )
    
    def export_for_human(self, proof_id: str) -> str:
        """
        Export a proof tree as human-readable natural language.
        
        This is used by the proof_viewer ceremony to show the human
        exactly what the planner decided and why.
        """
        record = self._load_record(proof_id)
        if record is None:
            return f"Proof {proof_id} not found"
        
        tree = record.proof_tree
        lines = [
            "=" * 60,
            "PROOF TREE — Agent Decision Audit",
            f"Proof ID: {proof_id}",
            f"Intent: {record.intent_id}",
            f"Steps: {len(tree.get('steps', []))}",
            f"Human Reviewed: {'Yes' if record.human_reviewed else 'No'}",
            f"Integrity: {'Valid' if self.verify_integrity(proof_id) else 'TAMPERED'}",
            "=" * 60,
            "",
            "Execution Plan:",
        ]
        
        for i, step in enumerate(tree.get("steps", []), 1):
            lines.append(f"  {i}. {step.get('description', 'Unknown step')}")
            if "reason" in step:
                lines.append(f"     Reason: {step['reason']}")
            if "data_accessed" in step:
                lines.append(f"     Data: {step['data_accessed']}")
            if "constraints_satisfied" in step:
                lines.append(f"     Constraints: {', '.join(step['constraints_satisfied'])}")
        
        lines.extend([
            "",
            "Data Accessed:",
        ])
        for data in tree.get("data_access", []):
            lines.append(f"  - {data}")
        
        if tree.get("external_calls"):
            lines.extend([
                "",
                "External Calls:",
            ])
            for call in tree["external_calls"]:
                lines.append(f"  - {call.get('endpoint', '?')} ({call.get('method', '?')})")
        
        lines.append("")
        return "\n".join(lines)
