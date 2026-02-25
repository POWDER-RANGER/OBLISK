"""Unit tests for vault.crypto — AES-256-GCM primitives.

Covers:
- encrypt/decrypt round-trip
- nonce uniqueness (IND-CPA)
- tamper detection (InvalidTag)
- wrong-key rejection
- key-length enforcement
- derive_key determinism and salt uniqueness
- blob encode/decode helpers
"""

from __future__ import annotations

import pytest
from cryptography.exceptions import InvalidTag

from vault.crypto import (
    KEY_SIZE,
    NONCE_SIZE,
    decode_blob,
    decrypt,
    derive_key,
    encode_blob,
    encrypt,
)

KEY_A: bytes = b"a" * KEY_SIZE
KEY_B: bytes = b"b" * KEY_SIZE


class TestEncryptDecrypt:
    def test_roundtrip_ascii(self) -> None:
        assert decrypt(KEY_A, encrypt(KEY_A, "hello")) == "hello"

    def test_roundtrip_unicode(self) -> None:
        value = "caf\u00e9 🔒 s\u00e9curit\u00e9"
        assert decrypt(KEY_A, encrypt(KEY_A, value)) == value

    def test_roundtrip_empty_string(self) -> None:
        assert decrypt(KEY_A, encrypt(KEY_A, "")) == ""

    def test_roundtrip_long_value(self) -> None:
        value = "x" * 100_000
        assert decrypt(KEY_A, encrypt(KEY_A, value)) == value

    def test_nonce_is_prepended(self) -> None:
        blob = encrypt(KEY_A, "test")
        assert len(blob) >= NONCE_SIZE + 16  # nonce + GCM tag minimum

    def test_nonces_are_unique(self) -> None:
        """Same plaintext encrypted 200 times must produce 200 distinct nonces."""
        blobs = [encrypt(KEY_A, "same-value") for _ in range(200)]
        nonces = {b[:NONCE_SIZE] for b in blobs}
        assert len(nonces) == 200


class TestTamperDetection:
    def test_flip_ciphertext_byte_raises(self) -> None:
        blob = bytearray(encrypt(KEY_A, "secret"))
        blob[NONCE_SIZE + 2] ^= 0xFF  # flip a byte inside ciphertext
        with pytest.raises(InvalidTag):
            decrypt(KEY_A, bytes(blob))

    def test_flip_tag_byte_raises(self) -> None:
        blob = bytearray(encrypt(KEY_A, "secret"))
        blob[-1] ^= 0xFF  # last byte is part of the GCM tag
        with pytest.raises(InvalidTag):
            decrypt(KEY_A, bytes(blob))

    def test_truncated_blob_raises_value_error(self) -> None:
        blob = encrypt(KEY_A, "secret")[:5]  # too short
        with pytest.raises(ValueError, match="too short"):
            decrypt(KEY_A, blob)

    def test_wrong_key_raises_invalid_tag(self) -> None:
        blob = encrypt(KEY_A, "secret")
        with pytest.raises(InvalidTag):
            decrypt(KEY_B, blob)


class TestKeyLengthEnforcement:
    def test_encrypt_short_key_raises(self) -> None:
        with pytest.raises(ValueError, match="32 bytes"):
            encrypt(b"short", "value")

    def test_decrypt_short_key_raises(self) -> None:
        blob = encrypt(KEY_A, "value")
        with pytest.raises(ValueError, match="32 bytes"):
            decrypt(b"short", blob)

    def test_encrypt_long_key_raises(self) -> None:
        with pytest.raises(ValueError, match="32 bytes"):
            encrypt(b"x" * 64, "value")


class TestDeriveKey:
    def test_returns_32_byte_key(self) -> None:
        key, salt = derive_key("passphrase")
        assert len(key) == KEY_SIZE

    def test_deterministic_with_same_salt(self) -> None:
        key1, salt = derive_key("passphrase")
        key2, _ = derive_key("passphrase", salt)
        assert key1 == key2

    def test_different_passphrases_differ(self) -> None:
        key1, salt = derive_key("passphrase-a")
        key2, _ = derive_key("passphrase-b", salt)
        assert key1 != key2

    def test_random_salt_when_none(self) -> None:
        key1, _ = derive_key("passphrase")
        key2, _ = derive_key("passphrase")
        assert key1 != key2  # different random salts each call


class TestBlobHelpers:
    def test_encode_decode_roundtrip(self) -> None:
        raw = b"\x00\xff\xde\xad\xbe\xef"
        assert decode_blob(encode_blob(raw)) == raw

    def test_encoded_is_ascii(self) -> None:
        encoded = encode_blob(encrypt(KEY_A, "test"))
        encoded.encode("ascii")  # must not raise
