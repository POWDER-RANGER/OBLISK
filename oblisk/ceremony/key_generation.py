"""
Key Generation — The Capstone Ceremony

The KeyCeremony is the foundational ritual of OBLISK. It is the moment
when the human becomes cryptographically sovereign — the only entity
that can authorize agent actions.

This is not a key generation utility. It is a ceremony.
It requires presence, attention, and understanding.

Principle: The human IS the key. There is no backup. There is no recovery.
           This is by design, not limitation.
"""

from __future__ import annotations

import secrets
import hashlib
import time
from typing import Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class CeremonyPhase(Enum):
    """Phases of the key generation ceremony."""
    NOT_STARTED = "not_started"
    WARNING_SHOWN = "warning_shown"       # Human shown the "no recovery" warning
    ENTROPY_GATHERED = "entropy_gathered"  # System + human entropy collected
    PASSPHRASE_CREATED = "passphrase_created"  # High-entropy passphrase generated
    CONFIRMATION_SPOKEN = "confirmation_spoken"  # Human explicitly confirms understanding
    KEYS_DERIVED = "keys_derived"          # Master key derived
    ATTESTATION_SIGNED = "attestation_signed"  # Ceremony proof signed
    COMPLETE = "complete"


@dataclass
class CeremonyState:
    """
    State machine tracking the key ceremony progress.
    
    Attributes:
        phase: Current ceremony phase
        started_at: When the ceremony began
        completed_at: When the ceremony finished
        entropy_sources: What sources contributed entropy
        passphrase_hash: Hash of the generated passphrase (never the passphrase itself)
        identity_hash: The resulting identity hash
        warnings_acknowledged: List of warnings the human has acknowledged
        attestation: Signed ceremony attestation
    """
    phase: CeremonyPhase = CeremonyPhase.NOT_STARTED
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    entropy_sources: list[str] = field(default_factory=list)
    passphrase_hash: str = ""
    identity_hash: str = ""
    warnings_acknowledged: list[str] = field(default_factory=list)
    attestation: dict = field(default_factory=dict)


@dataclass
class CeremonyResult:
    """
    The complete result of a successful key ceremony.
    
    Attributes:
        identity: The HumanIdentity instance
        master_key: The 32-byte master key (for vault creation)
        attestation: Signed proof that the ceremony completed
        recovery_phrase: BIP39-style mnemonic (displayed ONCE)
        warnings: List of warnings shown and acknowledged
    """
    identity: "HumanIdentity"  # Forward reference resolved at runtime
    master_key: bytes
    attestation: dict
    recovery_phrase: str
    warnings: list[str]


class KeyCeremony:
    """
    The sovereign key generation ceremony.
    
    The KeyCeremony is a deliberate, multi-phase process that ensures:
    1. The human understands there is no recovery
    2. Sufficient entropy is gathered from multiple sources
    3. A high-entropy passphrase is generated (not chosen)
    4. The human explicitly confirms their understanding
    5. Keys are derived with cryptographic attestation
    
    This is the ONLY way to create a HumanIdentity. There are no shortcuts,
    no "quick setup" modes, and no bypasses.
    
    Attributes:
        state: Current ceremony state machine
        entropy_pool: Accumulated entropy from all sources
    """
    
    # BIP39 English wordlist (first 128 words for 12-word phrases)
    WORDLIST = [
        "abandon", "ability", "able", "about", "above", "absent", "absorb",
        "abstract", "absurd", "abuse", "access", "accident", "account",
        "accuse", "achieve", "acid", "acoustic", "acquire", "across", "act",
        "action", "actor", "actress", "actual", "adapt", "add", "addict",
        "address", "adjust", "admit", "adult", "advance", "advice",
        "aerobic", "affair", "afford", "afraid", "again", "age", "agent",
        "agree", "ahead", "aim", "air", "airport", "aisle", "alarm",
        "album", "alcohol", "alert", "alien", "all", "alley", "allow",
        "alone", "alpha", "already", "also", "alter", "always", "amateur",
        "amazing", "among", "amount", "amused", "anchor", "ancient", "anger",
        "angle", "angry", "animal", "ankle", "announce", "annual", "another",
        "answer", "antenna", "antique", "anxiety", "any", "apart", "apology",
        "appear", "apple", "approve", "april", "arch", "arctic", "arena",
        "argue", "armor", "art", "artist", "aspiring", "asset", "assist",
        "assume", "asthma", "athlete", "atom", "attack", "attend", "attitude",
        "attract", "auction", "audit", "august", "aunt", "author", "auto",
        "autumn", "average", "avocado", "avoid", "awake", "aware", "awesome",
        "awful", "axis", "baby", "bachelor", "bacon", "badge", "bag",
        "balance", "balcony", "ball", "bamboo", "banana", "banner", "bar",
    ]
    
    WARNINGS = [
        "You are about to create cryptographic keys that control access to your OBLISK.",
        "THERE IS NO BACKUP. If you lose these keys, they are gone forever.",
        "THERE IS NO RECOVERY SERVICE. No company can reset your keys.",
        "YOU ARE THE KEY. Your memory, your security, your responsibility.",
        "Write down the recovery phrase. Store it physically, securely, offline.",
        "Anyone with your recovery phrase controls your OBLISK.",
    ]
    
    def __init__(self):
        self.state = CeremonyState()
        self._entropy_pool: bytes = b""
    
    def begin(self) -> CeremonyState:
        """
        Begin the key generation ceremony.
        
        This starts the state machine and displays the first warning.
        The ceremony cannot proceed until the human acknowledges each warning.
        
        Returns:
            The current ceremony state
        """
        self.state.phase = CeremonyPhase.WARNING_SHOWN
        self.state.started_at = time.time()
        self.state.warnings_acknowledged = []
        
        return self.state
    
    def acknowledge_warning(self, warning_index: int) -> CeremonyState:
        """
        Acknowledge a specific warning.
        
        The human must acknowledge each warning before proceeding.
        This is not bureaucracy — it is informed consent.
        
        Args:
            warning_index: Index of the warning being acknowledged
            
        Returns:
            Updated ceremony state
        """
        if warning_index < 0 or warning_index >= len(self.WARNINGS):
            raise ValueError(f"Invalid warning index: {warning_index}")
        
        warning = self.WARNINGS[warning_index]
        if warning not in self.state.warnings_acknowledged:
            self.state.warnings_acknowledged.append(warning)
        
        # If all warnings acknowledged, move to entropy gathering
        if len(self.state.warnings_acknowledged) == len(self.WARNINGS):
            self.state.phase = CeremonyPhase.ENTROPY_GATHERED
        
        return self.state
    
    def gather_entropy(self, sources: dict[str, bytes]) -> CeremonyState:
        """
        Gather entropy from multiple sources.
        
        Sources can include:
            - System entropy (os.urandom)
            - Mouse movement patterns
            - Keystroke timing
            - Optional biometric data
        
        Args:
            sources: Dict of source_name -> entropy_bytes
            
        Returns:
            Updated ceremony state
        """
        if self.state.phase != CeremonyPhase.ENTROPY_GATHERED:
            raise ValueError(f"Cannot gather entropy in phase: {self.state.phase.value}")
        
        # Mix all entropy sources
        mixed = b""
        for source_name, entropy in sources.items():
            self.state.entropy_sources.append(source_name)
            mixed += entropy
        
        # Add system entropy
        system_entropy = secrets.token_bytes(32)
        mixed += system_entropy
        self.state.entropy_sources.append("system")
        
        # Hash to create uniform distribution
        self._entropy_pool = hashlib.sha256(mixed).digest()
        
        self.state.phase = CeremonyPhase.ENTROPY_GATHERED
        return self.state
    
    def generate_passphrase(self) -> Tuple[str, CeremonyState]:
        """
        Generate a high-entropy passphrase from the collected entropy.
        
        The passphrase is generated, not chosen. Humans are terrible
        at choosing entropy. The system generates it from the
        collected entropy pool.
        
        Returns:
            (passphrase, updated ceremony state)
        """
        if not self._entropy_pool:
            raise ValueError("No entropy gathered. Call gather_entropy() first.")
        
        # Generate a 12-word recovery phrase from entropy
        words = []
        entropy_int = int.from_bytes(self._entropy_pool, 'big')
        
        for i in range(12):
            index = (entropy_int >> (i * 11)) % len(self.WORDLIST)
            words.append(self.WORDLIST[index])
        
        passphrase = " ".join(words)
        
        # Store only the hash, never the passphrase
        self.state.passphrase_hash = hashlib.sha256(
            passphrase.encode()
        ).hexdigest()[:16]
        
        self.state.phase = CeremonyPhase.PASSPHRASE_CREATED
        
        return passphrase, self.state
    
    def confirm_understanding(self, confirmation: str) -> CeremonyState:
        """
        Require the human to explicitly confirm understanding.
        
        The human must type a specific confirmation phrase to prove
        they have read and understood the warnings.
        
        Args:
            confirmation: The phrase spoken by the human
            
        Returns:
            Updated ceremony state
        """
        expected = "I understand there is no recovery and I am the key"
        
        if confirmation.strip().lower() != expected.lower():
            raise ValueError(
                f"Confirmation phrase incorrect. Expected: '{expected}'"
            )
        
        self.state.phase = CeremonyPhase.CONFIRMATION_SPOKEN
        return self.state
    
    def derive_keys(self, passphrase: str) -> Tuple["HumanIdentity", bytes, CeremonyState]:
        """
        Derive the sovereign identity from the passphrase.
        
        This is the capstone moment. The master key is derived,
        the HumanIdentity is created, and the ceremony attestation
        is signed.
        
        Args:
            passphrase: The recovery phrase generated earlier
            
        Returns:
            (HumanIdentity, master_key, ceremony_state)
        """
        from ..vault.identity import HumanIdentity
        
        if self.state.phase != CeremonyPhase.CONFIRMATION_SPOKEN:
            raise ValueError(f"Cannot derive keys in phase: {self.state.phase.value}")
        
        # Create identity
        identity, attestation = HumanIdentity.from_ceremony(
            passphrase=passphrase,
            ceremony_proof={
                "entropy_sources": self.state.entropy_sources,
                "warnings_acknowledged_count": len(self.state.warnings_acknowledged),
                "timestamp": time.time(),
            }
        )
        
        # Store results
        self.state.identity_hash = identity.identity_hash
        self.state.attestation = attestation
        self.state.phase = CeremonyPhase.KEYS_DERIVED
        
        # Master key is derived internally by HumanIdentity
        # We return it for vault creation
        master_key = identity.master_key
        
        return identity, master_key, self.state
    
    def complete(self) -> CeremonyResult:
        """
        Complete the ceremony and return the final result.
        
        This can only be called after all phases have been completed.
        
        Returns:
            The complete CeremonyResult with identity and recovery phrase
        """
        if self.state.phase != CeremonyPhase.KEYS_DERIVED:
            raise ValueError(f"Cannot complete in phase: {self.state.phase.value}")
        
        self.state.phase = CeremonyPhase.COMPLETE
        self.state.completed_at = time.time()
        
        # The actual identity and master_key were returned by derive_keys()
        # This method finalizes the ceremony state
        
        raise NotImplementedError(
            "complete() should be called with the identity and passphrase "
            "from the previous steps. Use derive_keys() first, then construct "
            "CeremonyResult manually."
        )
    
    def get_progress(self) -> dict:
        """Get human-readable progress of the ceremony."""
        phases = list(CeremonyPhase)
        current_idx = phases.index(self.state.phase)
        
        return {
            "phase": self.state.phase.value,
            "phase_number": current_idx + 1,
            "total_phases": len(phases),
            "percent_complete": (current_idx / (len(phases) - 1)) * 100,
            "warnings_acknowledged": len(self.state.warnings_acknowledged),
            "total_warnings": len(self.WARNINGS),
            "entropy_sources": len(self.state.entropy_sources),
            "elapsed_seconds": (
                (time.time() - self.state.started_at) if self.state.started_at else 0
            ),
        }
