"""
Consent Log — Immutable Audit of Human Approvals

The ConsentLog maintains a cryptographically chained, append-only record
of every action the human has approved. This creates an auditable trail
that proves (or disproves) that the human consented to any given action.

Principle: Trust but verify. Every approval is logged, chained, and auditable.
"""

from __future__ import annotations

import hashlib
import time
import json
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum


class ConsentType(Enum):
    """Types of consent recorded in the log."""
    INTENT_SIGNED = "intent_signed"           # Human signed an intent
    POLICY_CREATED = "policy_created"         # Human created a policy
    DATA_TRANSFER = "data_transfer"           # Human approved data leaving device
    AGENT_SPAWNED = "agent_spawned"           # Human approved agent creation
    ACTION_APPROVED = "action_approved"       # Human approved a specific action
    PROOF_REVIEWED = "proof_reviewed"         # Human reviewed and approved proof tree
    REVOCATION = "revocation"                 # Human revoked previous consent


@dataclass
class ConsentEntry:
    """
    A single entry in the immutable consent log.
    
    Each entry is cryptographically chained to the previous entry,
    creating a tamper-evident audit trail.
    
    Attributes:
        index: Sequential entry number (0, 1, 2, ...)
        timestamp: Unix timestamp
        consent_type: Category of consent
        subject_id: The ID of the intent/policy/agent being consented to
        description: Human-readable description
        identity_hash: Hash of the human identity that granted consent
        previous_hash: Hash of the previous entry (chains the log)
        entry_hash: Hash of this entry's content
    """
    index: int
    timestamp: float
    consent_type: ConsentType
    subject_id: str
    description: str
    identity_hash: str
    previous_hash: str
    entry_hash: str = ""
    
    def compute_hash(self) -> str:
        """Compute the cryptographic hash of this entry."""
        content = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "consent_type": self.consent_type.value,
            "subject_id": self.subject_id,
            "description": self.description,
            "identity_hash": self.identity_hash,
            "previous_hash": self.previous_hash,
        }, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(content.encode()).hexdigest()
    
    def finalize(self) -> "ConsentEntry":
        """Compute and set the entry hash."""
        self.entry_hash = self.compute_hash()
        return self
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for storage."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "consent_type": self.consent_type.value,
            "subject_id": self.subject_id,
            "description": self.description,
            "identity_hash": self.identity_hash,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ConsentEntry":
        """Deserialize from dictionary."""
        return cls(
            index=data["index"],
            timestamp=data["timestamp"],
            consent_type=ConsentType(data["consent_type"]),
            subject_id=data["subject_id"],
            description=data["description"],
            identity_hash=data["identity_hash"],
            previous_hash=data["previous_hash"],
            entry_hash=data["entry_hash"],
        )


class ConsentLog:
    """
    Immutable, cryptographically chained consent audit log.
    
    The ConsentLog answers the question: "Did the human actually approve this?"
    Every entry is chained to the previous one via SHA-256 hashes, making
    tampering detectable.
    
    Attributes:
        vault: Reference to the encrypted vault
        identity_hash: Hash of the human identity
        _entries: In-memory list of consent entries
    """
    
    def __init__(self, vault, identity_hash: str):
        self.vault = vault
        self.identity_hash = identity_hash
        self._entries: list[ConsentEntry] = []
        self._load()
    
    def _load(self) -> None:
        """Load the consent log from the vault."""
        raw_entries = self.vault.get("_consent_log", [])
        for raw in raw_entries:
            try:
                entry = ConsentEntry.from_dict(raw)
                self._entries.append(entry)
            except (KeyError, ValueError) as e:
                print(f"Warning: Skipping corrupted consent entry: {e}")
    
    @property
    def latest_hash(self) -> str:
        """Get the hash of the most recent entry (genesis if empty)."""
        if not self._entries:
            return hashlib.sha256(b"OBLISK_CONSENT_GENESIS").hexdigest()
        return self._entries[-1].entry_hash
    
    @property
    def length(self) -> int:
        """Get the number of entries in the log."""
        return len(self._entries)
    
    def record(
        self, 
        consent_type: ConsentType, 
        subject_id: str, 
        description: str
    ) -> ConsentEntry:
        """
        Record a new consent entry.
        
        This is the primary method for logging human approvals. Every
        significant action in OBLISK should generate a consent log entry.
        
        Args:
            consent_type: What kind of consent is being recorded
            subject_id: The ID of the thing being consented to
            description: Human-readable description
            
        Returns:
            The created ConsentEntry
        """
        entry = ConsentEntry(
            index=self.length,
            timestamp=time.time(),
            consent_type=consent_type,
            subject_id=subject_id,
            description=description,
            identity_hash=self.identity_hash,
            previous_hash=self.latest_hash,
        ).finalize()
        
        self._entries.append(entry)
        self._persist()
        
        return entry
    
    def verify_chain(self) -> tuple[bool, Optional[int]]:
        """
        Verify the cryptographic integrity of the entire chain.
        
        Checks that:
        1. Each entry's previous_hash matches the actual previous entry's hash
        2. Each entry's entry_hash is correctly computed
        
        Returns:
            (is_valid, first_broken_index) — None index means all valid
        """
        for i, entry in enumerate(self._entries):
            # Verify entry hash
            if entry.compute_hash() != entry.entry_hash:
                return False, i
            
            # Verify chain linkage
            if i == 0:
                expected_previous = hashlib.sha256(b"OBLISK_CONSENT_GENESIS").hexdigest()
            else:
                expected_previous = self._entries[i - 1].entry_hash
            
            if entry.previous_hash != expected_previous:
                return False, i
        
        return True, None
    
    def get_entries_for_subject(self, subject_id: str) -> list[ConsentEntry]:
        """Get all consent entries related to a specific subject."""
        return [e for e in self._entries if e.subject_id == subject_id]
    
    def has_consented(self, subject_id: str, consent_type: ConsentType) -> bool:
        """
        Check if the human has consented to a specific subject/action.
        
        This is used by the DataGuardian to check if data transfer is allowed.
        """
        entries = self.get_entries_for_subject(subject_id)
        return any(
            e.consent_type == consent_type and e.consents_type in (
                ConsentType.REVOCATION,
            )
            for e in entries
        )
    
    def get_audit_trail(self, subject_id: str) -> list[dict]:
        """
        Get a complete audit trail for a subject.
        
        Returns all consent entries in chronological order, useful for
        the proof_viewer UI and for human review.
        """
        entries = self.get_entries_for_subject(subject_id)
        return [e.to_dict() for e in entries]
    
    def _persist(self) -> None:
        """Save the consent log to the vault."""
        self.vault.set("_consent_log", [e.to_dict() for e in self._entries])
    
    def export(self) -> str:
        """
        Export the entire consent log as a human-readable string.
        
        Useful for audits, legal compliance, and the proof viewer UI.
        """
        lines = [
            "=" * 60,
            "OBLISK CONSENT LOG — Immutable Audit Trail",
            f"Identity: {self.identity_hash}",
            f"Entries: {self.length}",
            f"Chain Valid: {self.verify_chain()[0]}",
            "=" * 60,
            "",
        ]
        
        for entry in self._entries:
            lines.append(f"[{entry.index}] {entry.consents_type.value} — {entry.subject_id}")
            lines.append(f"    Time: {time.ctime(entry.timestamp)}")
            lines.append(f"    Description: {entry.description}")
            lines.append(f"    Hash: {entry.entry_hash[:16]}...")
            lines.append("")
        
        return "\n".join(lines)
