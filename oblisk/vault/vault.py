"""
Vault — AES-256-GCM Encrypted Store (The Bedrock)

The foundational encrypted storage layer. All vault data is encrypted at rest
with keys derived from the user's sovereign identity. This module is the
successor to the original vault.py, maintaining backward compatibility while
integrating with the broader v2 architecture.
"""

from __future__ import annotations

import json
import hashlib
import secrets
from pathlib import Path
from typing import Any, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


class Vault:
    """
    AES-256-GCM encrypted key-value store.
    
    The vault is the bedrock of OBLISK — all identity, policy, intent,
    and consent data flows through here encrypted with keys the human controls.
    
    Attributes:
        vault_path: Path to the encrypted vault file on disk
        _master_key: The AES-256 key derived from sovereign identity
        _data: Decrypted in-memory store
    """
    
    def __init__(self, vault_path: str, master_key: bytes):
        self.vault_path = Path(vault_path)
        self._master_key = master_key
        self._data: dict[str, Any] = {}
        self._load()
    
    @classmethod
    def create(cls, vault_path: str, passphrase: str, salt: Optional[bytes] = None) -> "Vault":
        """
        Create a new vault with a passphrase-derived key.
        
        In production, the passphrase comes from the sovereign key ceremony
        and the salt is derived from biometric data.
        """
        salt = salt or secrets.token_bytes(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600_000,
        )
        master_key = kdf.derive(passphrase.encode("utf-8"))
        vault = cls.__new__(cls)
        vault.vault_path = Path(vault_path)
        vault._master_key = master_key
        vault._data = {"_vault_meta": {"salt": salt.hex(), "version": "2.0.0"}}
        vault._save()
        return vault
    
    def _derive_key(self, context: str) -> bytes:
        """Derive a context-specific key from the master key using HKDF-like construction."""
        return hashlib.sha256(self._master_key + context.encode()).digest()
    
    def _load(self) -> None:
        """Load and decrypt vault data from disk."""
        if not self.vault_path.exists():
            self._data = {}
            return
        
        with open(self.vault_path, "rb") as f:
            payload = f.read()
        
        nonce = payload[:12]
        ciphertext = payload[12:]
        aesgcm = AESGCM(self._master_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        self._data = json.loads(plaintext.decode("utf-8"))
    
    def _save(self) -> None:
        """Encrypt and save vault data to disk."""
        plaintext = json.dumps(self._data).encode("utf-8")
        nonce = secrets.token_bytes(12)
        aesgcm = AESGCM(self._master_key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.vault_path, "wb") as f:
            f.write(nonce + ciphertext)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the vault."""
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in the vault and persist."""
        self._data[key] = value
        self._save()
    
    def delete(self, key: str) -> None:
        """Delete a key from the vault."""
        if key in self._data:
            del self._data[key]
            self._save()
    
    def keys(self):
        """Return all keys in the vault (excluding metadata)."""
        return [k for k in self._data.keys() if not k.startswith("_vault")]
    
    def get_signed_intent(self, intent_id: str) -> dict:
        """
        Retrieve a cryptographically signed intent by ID.
        Used by the FlowController to verify intent before execution.
        """
        intents = self._data.get("_intents", {})
        intent = intents.get(intent_id)
        if intent is None:
            raise ValueError(f"Intent {intent_id} not found in vault")
        return intent
    
    def get_policy_constraints(self) -> list[dict]:
        """
        Retrieve all active policy constraints.
        Used by the FlowController and ConstraintEngine.
        """
        return self._data.get("_policies", [])
    
    def store_intent(self, intent_id: str, intent: dict) -> None:
        """Store a signed intent in the vault."""
        if "_intents" not in self._data:
            self._data["_intents"] = {}
        self._data["_intents"][intent_id] = intent
        self._save()
    
    def store_policy(self, policy_id: str, policy: dict) -> None:
        """Store a policy constraint in the vault."""
        if "_policies" not in self._data:
            self._data["_policies"] = []
        policy["id"] = policy_id
        self._data["_policies"].append(policy)
        self._save()
