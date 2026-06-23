"""
VAULT — The Base of the OBLISK

The vault is the foundation of human sovereignty in the OBLISK architecture.
It stores identity, policy, signed intents, and an immutable consent audit log.

Components:
    - vault.py: AES-256-GCM encrypted store (existing, the bedrock)
    - identity.py: User identity + sovereign key ceremony
    - policy_store.py: User-authored governance rules in Prolog/Datalog
    - intent_store.py: Cryptographically signed human intents
    - consent_log.py: Immutable audit of what the user approved

Principle: The human IS the key. No cloud backup. No recovery.
"""

from .vault import Vault
from .identity import HumanIdentity
from .policy_store import PolicyStore
from .intent_store import IntentStore
from .consent_log import ConsentLog

__all__ = ["Vault", "HumanIdentity", "PolicyStore", "IntentStore", "ConsentLog"]
