"""Vault module for OBLISK.

Provides AES-256-GCM authenticated encryption for secure key-value storage.
Every stored value is encrypted with a fresh random nonce; retrieval authenticates
the GCM tag before returning any plaintext, making tampering detectable.

Quick start::

    from oblisk.vault import Vault, derive_key

    # From a raw 32-byte key:
    key = bytes.fromhex("your-64-hex-char-string")  # 32 bytes
    vault = Vault(key=key)

    # Or derive from a passphrase:
    key, salt = derive_key("strong-passphrase")
    vault = Vault(key=key)

    vault.store("api_key", "sk-abc123")
    secret = vault.retrieve("api_key")  # returns "sk-abc123"
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.exceptions import InvalidTag

from vault.crypto import (
    KEY_SIZE,
    decode_blob,
    decrypt,
    derive_key,
    encode_blob,
    encrypt,
)

__all__ = ["Vault", "derive_key", "InvalidTag"]


class Vault:
    """AES-256-GCM encrypted key-value store for the OBLISK framework.

    Each secret is encrypted with a fresh 96-bit random nonce and authenticated
    with a 128-bit GCM tag. Stored values are never exposed as plaintext, and
    any in-storage tampering raises :class:`cryptography.exceptions.InvalidTag`
    before any plaintext is returned.

    Args:
        key: Exactly 32 bytes (256-bit) symmetric key. Use :func:`derive_key`
             to generate from a passphrase.
        path: Optional file path for persistent JSON storage. If provided, the
              vault is loaded from this path on init and saved after every write.

    Raises:
        ValueError: If ``key`` is not exactly 32 bytes.

    Attributes:
        vault_id (str): Auto-generated unique identifier.
        name (str): Descriptive name (defaults to ``"vault"``).
        encrypted (bool): Always ``True`` — AES-256-GCM is always active.
    """

    def __init__(
        self,
        key: bytes,
        name: str = "vault",
        path: Optional[str | Path] = None,
        vault_id: Optional[str] = None,
    ) -> None:
        if len(key) != KEY_SIZE:
            raise ValueError(
                f"Vault key must be exactly {KEY_SIZE} bytes (256-bit). "
                f"Got {len(key)} bytes. Use vault.crypto.derive_key() to generate a valid key."
            )
        self._key: bytes = key
        self.vault_id: str = vault_id or self._generate_vault_id()
        self.name: str = name
        self.encrypted: bool = True  # always True — no unencrypted mode
        self._path: Optional[Path] = Path(path) if path else None
        self._store: Dict[str, str] = {}   # key -> base64(nonce||ciphertext||tag)
        self._access_log: List[Dict[str, Any]] = []
        self._logger = logging.getLogger(f"oblisk.vault.{self.name}")

        if self._path and self._path.exists():
            self._load()

        self._logger.info(
            "Vault '%s' initialised (id=%s, AES-256-GCM)", self.name, self.vault_id
        )

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        key: bytes,
        name: str = "default",
        path: Optional[str | Path] = None,
    ) -> "Vault":
        """Factory method — thin wrapper over ``__init__`` for readability.

        Example::

            vault = Vault.create(key=my_key, name="agent-secrets")
        """
        return cls(key=key, name=name, path=path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store(self, key: str, value: str) -> None:
        """Encrypt *value* and store it under *key*.

        Args:
            key: Lookup key (plain text, not encrypted).
            value: Secret string to encrypt and store.

        Raises:
            TypeError: If *value* is not a ``str``.
        """
        if not isinstance(value, str):
            raise TypeError(
                f"Vault.store() only accepts str values; got {type(value).__name__}. "
                "Serialise complex objects to JSON before storing."
            )
        blob = encrypt(self._key, value)
        self._store[key] = encode_blob(blob)
        self._log_access("store", key)
        if self._path:
            self._save()
        self._logger.debug("Stored key '%s' (encrypted, AES-256-GCM)", key)

    def retrieve(self, key: str) -> str:
        """Decrypt and return the value stored under *key*.

        Args:
            key: Lookup key.

        Returns:
            The original plaintext string.

        Raises:
            KeyError: If *key* does not exist in the vault.
            InvalidTag: If the stored ciphertext has been tampered with, or
                        the vault was opened with the wrong key.
        """
        if key not in self._store:
            raise KeyError(f"Secret '{key}' not found in vault '{self.name}'")
        blob = decode_blob(self._store[key])
        plaintext = decrypt(self._key, blob)  # raises InvalidTag on any tampering
        self._log_access("retrieve", key)
        return plaintext

    def delete(self, key: str) -> None:
        """Remove a secret from the vault.

        Args:
            key: Lookup key to remove.

        Raises:
            KeyError: If *key* does not exist.
        """
        if key not in self._store:
            raise KeyError(f"Secret '{key}' not found in vault '{self.name}'")
        del self._store[key]
        self._log_access("delete", key)
        if self._path:
            self._save()
        self._logger.info("Deleted key '%s' from vault", key)

    def list_keys(self) -> List[str]:
        """Return the list of stored secret names (never the values).

        Returns:
            Sorted list of key strings.
        """
        return sorted(self._store.keys())

    def rotate_key(self, new_key: bytes) -> None:
        """Re-encrypt all secrets under *new_key*.

        Decrypts every value with the current key, re-encrypts with *new_key*,
        then atomically replaces the internal key reference.

        Args:
            new_key: New 32-byte key to use going forward.

        Raises:
            ValueError: If *new_key* is not exactly 32 bytes.
        """
        if len(new_key) != KEY_SIZE:
            raise ValueError(
                f"New key must be exactly {KEY_SIZE} bytes. Got {len(new_key)}."
            )
        new_store: Dict[str, str] = {}
        for k, encoded in self._store.items():
            blob = decode_blob(encoded)
            plaintext = decrypt(self._key, blob)
            new_blob = encrypt(new_key, plaintext)
            new_store[k] = encode_blob(new_blob)
        self._key = new_key
        self._store = new_store
        if self._path:
            self._save()
        self._logger.info("Key rotation complete (%d secrets re-encrypted)", len(new_store))

    def get_access_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return the most recent *limit* vault access events.

        Each entry contains ``operation``, ``key``, and ``timestamp``.
        """
        return self._access_log[-limit:]

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def __len__(self) -> int:
        return len(self._store)

    def __repr__(self) -> str:
        return (
            f"Vault(id={self.vault_id!r}, name={self.name!r}, "
            f"secrets={len(self._store)}, encrypted=AES-256-GCM)"
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log_access(self, operation: str, key: str) -> None:
        self._access_log.append(
            {
                "operation": operation,
                "key": key,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        )

    def _save(self) -> None:
        """Persist the encrypted store to disk as JSON."""
        assert self._path is not None
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "vault_id": self.vault_id,
            "name": self.name,
            "version": 1,
            "store": self._store,
        }
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load(self) -> None:
        """Load the encrypted store from a JSON file."""
        assert self._path is not None
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(
                f"Vault file '{self._path}' is corrupted or unreadable: {exc}"
            ) from exc
        if not isinstance(payload, dict) or "store" not in payload:
            raise ValueError(f"Vault file '{self._path}' has invalid format.")
        self._store = payload["store"]

    @staticmethod
    def _generate_vault_id() -> str:
        import uuid

        return f"vault-{uuid.uuid4().hex[:12]}"
