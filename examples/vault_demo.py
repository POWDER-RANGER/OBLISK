"""Demonstrate encrypted vault storage and backup recovery.

Run with python examples/vault_demo.py from the repository root after
installing the package. Replace the sample passphrase before use.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from vault import Vault, derive_key


def main() -> None:
    key, _salt = derive_key("demo-passphrase-change-before-use")
    with TemporaryDirectory() as directory:
        backup = Path(directory) / "vault-backup.json"
        vault = Vault(key=key, name="demo")
        vault.store("api_key", "example-secret")
        vault.export_encrypted(backup)

        restored = Vault.import_encrypted(backup, key)
        print(f"Keys: {restored.list_keys()}")
        print(f"Recovered value: {restored.retrieve('api_key')}")


if __name__ == "__main__":
    main()
