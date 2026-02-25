"""AES-256-GCM cryptographic primitives for the OBLISK vault.

Provides authenticated encryption (AES-256-GCM) and PBKDF2-HMAC-SHA256
key derivation. All values encrypted here are indistinguishable from
random bytes without the key, and any tampering raises InvalidTag.

Security properties:
    - Confidentiality: AES-256 (256-bit key, NIST-approved)
    - Integrity / Authenticity: GCM tag (128-bit)
    - Nonce: 96-bit random, unique per encryption call
    - KDF: PBKDF2-HMAC-SHA256 @ 600,000 iterations (OWASP 2023)
"""

from __future__ import annotations

import os
from base64 import b64decode, b64encode

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

__all__ = ["derive_key", "encrypt", "decrypt", "encode_blob", "decode_blob", "InvalidTag"]

# NIST SP 800-38D recommended nonce size for AES-GCM
NONCE_SIZE: int = 12   # bytes (96 bits)
KEY_SIZE: int = 32     # bytes (256 bits)
SALT_SIZE: int = 16    # bytes (128 bits)
PBKDF2_ITERATIONS: int = 600_000  # OWASP 2023 minimum for PBKDF2-HMAC-SHA256


def derive_key(passphrase: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    """Derive a 256-bit key from a passphrase using PBKDF2-HMAC-SHA256.

    Args:
        passphrase: Human-readable passphrase.
        salt: Optional 16-byte salt. If None, a cryptographically random
              salt is generated. Re-use the same salt to reproduce the same key.

    Returns:
        Tuple of (key: bytes, salt: bytes).  Store the salt alongside the
        encrypted vault so the key can be re-derived on load.

    Example::

        key, salt = derive_key("my-strong-passphrase")
        vault = Vault(key=key)
        # Save `salt` somewhere safe (it is NOT secret, but required for re-derivation)
    """
    if salt is None:
        salt = os.urandom(SALT_SIZE)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    key = kdf.derive(passphrase.encode("utf-8"))
    return key, salt


def encrypt(key: bytes, plaintext: str) -> bytes:
    """Encrypt a UTF-8 string using AES-256-GCM.

    Each call generates a fresh 96-bit random nonce, so encrypting the same
    plaintext twice yields different ciphertexts (IND-CPA secure).

    Args:
        key: Exactly 32 bytes (256-bit symmetric key).
        plaintext: String value to encrypt.

    Returns:
        Raw bytes in the format: nonce (12 bytes) || ciphertext+tag.

    Raises:
        ValueError: If key length is not exactly 32 bytes.
    """
    if len(key) != KEY_SIZE:
        raise ValueError(
            f"Vault key must be exactly {KEY_SIZE} bytes (256-bit). "
            f"Got {len(key)} bytes. Use derive_key() to generate a valid key."
        )
    nonce = os.urandom(NONCE_SIZE)
    aesgcm = AESGCM(key)
    # AESGCM.encrypt returns ciphertext || 16-byte GCM tag
    ciphertext_and_tag = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ciphertext_and_tag


def decrypt(key: bytes, blob: bytes) -> str:
    """Decrypt an AES-256-GCM blob produced by :func:`encrypt`.

    Args:
        key: Exactly 32 bytes — must be the same key used during encryption.
        blob: Raw bytes: nonce (12 bytes) || ciphertext+tag.

    Returns:
        The original plaintext string.

    Raises:
        ValueError: If key length is wrong or blob is too short.
        InvalidTag: If the ciphertext has been tampered with, or the key is wrong.
    """
    if len(key) != KEY_SIZE:
        raise ValueError(
            f"Vault key must be exactly {KEY_SIZE} bytes (256-bit). "
            f"Got {len(key)} bytes."
        )
    if len(blob) < NONCE_SIZE + 16:  # 16 = minimum GCM tag size
        raise ValueError(
            f"Ciphertext blob too short ({len(blob)} bytes). "
            "Expected at least nonce (12) + GCM tag (16) bytes."
        )
    nonce = blob[:NONCE_SIZE]
    ciphertext_and_tag = blob[NONCE_SIZE:]
    aesgcm = AESGCM(key)
    # Raises cryptography.exceptions.InvalidTag on any tampering or wrong key
    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext_and_tag, None)
    return plaintext_bytes.decode("utf-8")


def encode_blob(blob: bytes) -> str:
    """Base64-encode a raw ciphertext blob for JSON-safe storage.

    Args:
        blob: Raw encrypted bytes from :func:`encrypt`.

    Returns:
        ASCII-safe base64 string.
    """
    return b64encode(blob).decode("ascii")


def decode_blob(encoded: str) -> bytes:
    """Decode a base64-encoded ciphertext blob.

    Args:
        encoded: Base64 string produced by :func:`encode_blob`.

    Returns:
        Raw bytes suitable for passing to :func:`decrypt`.
    """
    return b64decode(encoded)
