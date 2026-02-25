"""Unit tests for vault.vault — Vault class.

Covers:
- store/retrieve round-trip
- key-length enforcement at init
- missing-key raises KeyError
- delete
- list_keys
- contains / len
- plaintext never stored in internal _store dict
- access log entries
- persistence (save/load round-trip)
- wrong-key persistence raises InvalidTag
- rotate_key re-encrypts everything
- create() factory
"""

from __future__ import annotations

from pathlib import Path

import pytest
from cryptography.exceptions import InvalidTag

from vault import Vault, derive_key
from vault.crypto import KEY_SIZE

TEST_KEY: bytes = b"oblisk-test-key!oblisk-test-key!"  # 32 bytes
ALT_KEY: bytes = b"different-32byte-key-for-test!!!"  # 32 bytes


@pytest.fixture
def vault() -> Vault:
    return Vault(key=TEST_KEY, name="unit-test-vault")


class TestVaultInit:
    def test_short_key_raises(self) -> None:
        with pytest.raises(ValueError, match="32 bytes"):
            Vault(key=b"tooshort")

    def test_long_key_raises(self) -> None:
        with pytest.raises(ValueError, match="32 bytes"):
            Vault(key=b"x" * 64)

    def test_encrypted_always_true(self, vault: Vault) -> None:
        assert vault.encrypted is True

    def test_vault_id_generated(self, vault: Vault) -> None:
        assert vault.vault_id.startswith("vault-")

    def test_create_factory(self) -> None:
        v = Vault.create(key=TEST_KEY, name="factory-vault")
        assert v.name == "factory-vault"
        assert len(v) == 0


class TestStoreRetrieve:
    def test_roundtrip(self, vault: Vault) -> None:
        vault.store("k", "secret-value")
        assert vault.retrieve("k") == "secret-value"

    def test_unicode_roundtrip(self, vault: Vault) -> None:
        value = "caf\u00e9 🔐"
        vault.store("uni", value)
        assert vault.retrieve("uni") == value

    def test_non_string_value_raises(self, vault: Vault) -> None:
        with pytest.raises(TypeError, match="str"):
            vault.store("k", 12345)  # type: ignore[arg-type]

    def test_plaintext_not_in_store(self, vault: Vault) -> None:
        vault.store("key", "hunter2")
        # The raw _store must never expose plaintext
        assert "hunter2" not in str(vault._store)

    def test_retrieve_missing_raises_key_error(self, vault: Vault) -> None:
        with pytest.raises(KeyError, match="nonexistent"):
            vault.retrieve("nonexistent")

    def test_overwrite_key(self, vault: Vault) -> None:
        vault.store("k", "v1")
        vault.store("k", "v2")
        assert vault.retrieve("k") == "v2"


class TestDeleteListContains:
    def test_delete_removes_key(self, vault: Vault) -> None:
        vault.store("k", "v")
        vault.delete("k")
        assert "k" not in vault

    def test_delete_missing_raises(self, vault: Vault) -> None:
        with pytest.raises(KeyError):
            vault.delete("nonexistent")

    def test_list_keys(self, vault: Vault) -> None:
        vault.store("b", "1")
        vault.store("a", "2")
        keys = vault.list_keys()
        assert keys == ["a", "b"]  # sorted

    def test_contains(self, vault: Vault) -> None:
        vault.store("present", "v")
        assert "present" in vault
        assert "absent" not in vault

    def test_len(self, vault: Vault) -> None:
        assert len(vault) == 0
        vault.store("a", "1")
        vault.store("b", "2")
        assert len(vault) == 2
        vault.delete("a")
        assert len(vault) == 1


class TestAccessLog:
    def test_store_logged(self, vault: Vault) -> None:
        vault.store("k", "v")
        log = vault.get_access_log()
        assert any(e["operation"] == "store" and e["key"] == "k" for e in log)

    def test_retrieve_logged(self, vault: Vault) -> None:
        vault.store("k", "v")
        vault.retrieve("k")
        log = vault.get_access_log()
        ops = [e["operation"] for e in log]
        assert "retrieve" in ops

    def test_delete_logged(self, vault: Vault) -> None:
        vault.store("k", "v")
        vault.delete("k")
        log = vault.get_access_log()
        ops = [e["operation"] for e in log]
        assert "delete" in ops

    def test_log_empty_on_new_vault(self, vault: Vault) -> None:
        assert vault.get_access_log() == []


class TestPersistence:
    def test_save_and_reload(self, tmp_path: Path) -> None:
        path = tmp_path / "vault.json"
        v1 = Vault(key=TEST_KEY, path=path)
        v1.store("persist", "survives")
        v2 = Vault(key=TEST_KEY, path=path)  # reload
        assert v2.retrieve("persist") == "survives"

    def test_wrong_key_on_reload_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "vault.json"
        v1 = Vault(key=TEST_KEY, path=path)
        v1.store("secret", "value")
        v2 = Vault(key=ALT_KEY, path=path)
        with pytest.raises(InvalidTag):
            v2.retrieve("secret")


class TestRotateKey:
    def test_rotate_preserves_values(self, vault: Vault) -> None:
        vault.store("a", "alpha")
        vault.store("b", "beta")
        vault.rotate_key(ALT_KEY)
        assert vault.retrieve("a") == "alpha"
        assert vault.retrieve("b") == "beta"

    def test_rotate_rejects_short_key(self, vault: Vault) -> None:
        with pytest.raises(ValueError, match="32 bytes"):
            vault.rotate_key(b"tooshort")

    def test_old_key_cannot_decrypt_after_rotation(self, vault: Vault) -> None:
        vault.store("k", "v")
        vault.rotate_key(ALT_KEY)
        # Manually try to decrypt with old key — should fail
        from vault.crypto import decode_blob, decrypt as raw_decrypt
        blob = decode_blob(vault._store["k"])
        with pytest.raises(InvalidTag):
            raw_decrypt(TEST_KEY, blob)
