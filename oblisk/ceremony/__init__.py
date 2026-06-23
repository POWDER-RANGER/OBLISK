"""
CEREMONY — The Rituals of the OBLISK

The ceremony module contains the ritualized processes that bind
the human to their OBLISK. These are not mere setup steps — they
are deliberate, meaningful acts that establish the human's sovereignty.

Components:
    - key_generation.py: The capstone moment — sovereign key creation
    - policy_creation.py: Natural language → Datalog constraint wizard
    - trust_ritual.py: First agent binding to vault
    - proof_viewer.py: UI for human to audit any agent decision

Principle: Every binding is intentional. Every ceremony is irreversible by design.
"""

from .key_generation import KeyCeremony
from .policy_creation import PolicyWizard
from .trust_ritual import TrustRitual
from .proof_viewer import ProofViewer

__all__ = ["KeyCeremony", "PolicyWizard", "TrustRitual", "ProofViewer"]
