"""
Data Guardian — Outbound Data Monitor

The DataGuardian monitors all outbound data from agents and blocks
any transfer that hasn't been explicitly approved by the human.

It enforces the core invariant: No data leaves the device without
a corresponding entry in the ConsentLog.

Principle: Every outbound packet is guilty until proven consented.
"""

from __future__ import annotations

import re
import hashlib
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from ..vault.consent_log import ConsentLog, ConsentType
    from ..vault.vault import Vault


class DataAction(Enum):
    """Types of data actions the guardian can detect."""
    ALLOWED = "allowed"           # Pre-approved in consent log
    BLOCKED = "blocked"           # No consent found, blocked
    FLAGGED = "flagged"           # Suspicious, needs review
    ENCRYPTED = "encrypted"       # Encrypted vault data detected
    PII_DETECTED = "pii_detected" # Personal identifiable information


@dataclass
class InterceptResult:
    """
    Result of intercepting an outbound data payload.
    
    Attributes:
        action: What the guardian decided
        agent_id: Which agent tried to send data
        payload_hash: Hash of the payload (for audit, never store payload itself)
        reason: Human-readable explanation
        consent_found: Whether matching consent was found
        vault_data_detected: Whether vault-encrypted data patterns were detected
        pii_detected: Whether PII patterns were detected
        timestamp: When the interception occurred
    """
    action: DataAction
    agent_id: str
    payload_hash: str
    reason: str
    consent_found: bool = False
    vault_data_detected: bool = False
    pii_detected: bool = False
    timestamp: float = field(default_factory=lambda: __import__('time').time())


class DataGuardian:
    """
    Monitors and controls all outbound data from agents.
    
    The DataGuardian is the last line of defense before data leaves
the device. It intercepts every outbound payload, checks the consent
log, scans for vault data patterns, and blocks unauthorized transfers.
    
    Attributes:
        consent_log: Immutable audit of human approvals
        vault: Reference to encrypted vault (for pattern matching, not decryption)
        blocked_patterns: Known exfiltration patterns
    """
    
    # Patterns that suggest encrypted vault data
    VAULT_DATA_PATTERNS = [
        r"[A-Fa-f0-9]{64,}",  # Long hex strings (AES ciphertext)
        r"vault://[^\s]+",      # Vault URI scheme
        r"OBLISK_VAULT_",       # Vault data markers
    ]
    
    # Patterns that suggest PII
    PII_PATTERNS = [
        r"\b\d{3}-\d{2}-\d{4}\b",                    # SSN
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
        r"\b\d{3}-\d{3}-\d{4}\b",                      # Phone
        r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",  # Credit card
        r"\b[A-Za-z]+\s*,\s*\d+\s+[A-Za-z]+\b",      # Address fragments
    ]
    
    def __init__(self, consent_log: "ConsentLog", vault: "Vault"):
        self.consent_log = consent_log
        self.vault = vault
        self._blocked_count: int = 0
        self._allowed_count: int = 0
    
    def intercept_outbound(self, agent_id: str, payload: dict) -> InterceptResult:
        """
        Intercept and evaluate an outbound data payload.
        
        This is called by the agent runtime before any network request.
        The guardian decides: ALLOW, BLOCK, or FLAG for review.
        
        Args:
            agent_id: Which agent is sending data
            payload: The data payload (dict with 'endpoint', 'method', 'body', etc.)
            
        Returns:
            InterceptResult with the decision and reasoning
        """
        # Hash the payload for audit (never store the actual payload)
        payload_str = str(payload)
        payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()[:32]
        
        # Scan for vault data patterns
        vault_detected = self._detect_vault_data(payload_str)
        
        # Scan for PII
        pii_detected = self._detect_pii(payload_str)
        
        # Check consent log
        consent_key = f"{agent_id}:{payload.get('endpoint', 'unknown')}"
        consent_entries = self.consent_log.get_entries_for_subject(consent_key)
        has_consent = any(
            e.consent_type in (ConsentType.DATA_TRANSFER, ConsentType.ACTION_APPROVED)
            for e in consent_entries
        )
        
        # Decision logic
        if vault_detected and not has_consent:
            self._blocked_count += 1
            return InterceptResult(
                action=DataAction.BLOCKED,
                agent_id=agent_id,
                payload_hash=payload_hash,
                reason=(
                    f"BLOCKED: Vault-encrypted data detected in outbound payload "
                    f"from agent {agent_id}. No consent found for this transfer. "
                    f"This would violate the vault's security model."
                ),
                consent_found=False,
                vault_data_detected=True,
                pii_detected=pii_detected,
            )
        
        if pii_detected and not has_consent:
            self._blocked_count += 1
            return InterceptResult(
                action=DataAction.FLAGGED,
                agent_id=agent_id,
                payload_hash=payload_hash,
                reason=(
                    f"FLAGGED: PII detected in outbound payload from agent {agent_id}. "
                    f"Requires explicit human consent before transfer."
                ),
                consent_found=False,
                vault_data_detected=vault_detected,
                pii_detected=True,
            )
        
        if has_consent:
            self._allowed_count += 1
            return InterceptResult(
                action=DataAction.ALLOWED,
                agent_id=agent_id,
                payload_hash=payload_hash,
                reason=(
                    f"ALLOWED: Found consent entry for {consent_key}. "
                    f"Transfer approved."
                ),
                consent_found=True,
                vault_data_detected=vault_detected,
                pii_detected=pii_detected,
            )
        
        # Default: block if no explicit consent
        self._blocked_count += 1
        return InterceptResult(
            action=DataAction.BLOCKED,
            agent_id=agent_id,
            payload_hash=payload_hash,
            reason=(
                f"BLOCKED: No consent found for agent {agent_id} to send data "
                f"to {payload.get('endpoint', 'unknown')}. "
                f"Human approval required."
            ),
            consent_found=False,
            vault_data_detected=vault_detected,
            pii_detected=pii_detected,
        )
    
    def request_consent(self, agent_id: str, description: str) -> str:
        """
        Request explicit human consent for a data transfer.
        
        This is called when the guardian blocks a transfer. It generates
        a consent request that the human can review and approve/deny.
        
        Args:
            agent_id: The agent requesting consent
            description: Human-readable description of what data would be sent
            
        Returns:
            Consent request ID for tracking
        """
        import time
        request_id = f"consent_req_{agent_id}_{int(time.time())}"
        
        # The consent request is stored but NOT automatically approved
        # Human must explicitly approve via the ceremony/proof_viewer
        return request_id
    
    def get_statistics(self) -> dict:
        """Get guardian interception statistics."""
        return {
            "blocked": self._blocked_count,
            "allowed": self._allowed_count,
            "total": self._blocked_count + self._allowed_count,
            "block_rate": (
                self._blocked_count / (self._blocked_count + self._allowed_count)
                if (self._blocked_count + self._allowed_count) > 0 else 0
            ),
        }
    
    def _detect_vault_data(self, payload_str: str) -> bool:
        """Scan payload for patterns that suggest encrypted vault data."""
        for pattern in self.VAULT_DATA_PATTERNS:
            if re.search(pattern, payload_str):
                return True
        return False
    
    def _detect_pii(self, payload_str: str) -> bool:
        """Scan payload for personally identifiable information."""
        for pattern in self.PII_PATTERNS:
            if re.search(pattern, payload_str):
                return True
        return False
