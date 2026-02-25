"""OBLISK Vault package.

Exports::

    from vault import Vault, derive_key, InvalidTag
"""

from vault.crypto import InvalidTag, derive_key
from vault.vault import Vault

__all__ = ["Vault", "derive_key", "InvalidTag"]
