"""Vault module for OBLISK.

Provides secure encrypted storage for sensitive data.
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime
import hashlib
import base64


class Vault:
    """Secure encrypted vault for storing sensitive data.
    
    The Vault class provides encrypted storage with access control for
    sensitive agent data including API keys, credentials, and state information.
    
    Attributes:
        vault_id (str): Unique identifier for the vault
        name (str): Human-readable name
        encrypted (bool): Whether encryption is enabled
        data (Dict): Stored data (encrypted in production)
        
    Example:
        >>> vault = Vault.create(name="my_vault", encrypted=True)
        >>> vault.store("api_key", "secret_value")
        >>> value = vault.retrieve("api_key")
    """
    
    def __init__(
        self,
        name: str,
        vault_id: Optional[str] = None,
        encrypted: bool = True,
        encryption_key: Optional[str] = None
    ):
        """Initialize a Vault instance.
        
        Args:
            name: Name of the vault
            vault_id: Optional vault ID (auto-generated if not provided)
            encrypted: Whether to enable encryption
            encryption_key: Optional encryption key
        """
        self.vault_id = vault_id or self._generate_vault_id()
        self.name = name
        self.encrypted = encrypted
        self._encryption_key = encryption_key
        self._data: Dict[str, Any] = {}
        self._access_log: list = []
        self._logger = logging.getLogger(f"oblisk.vault.{self.name}")
        self._logger.info(f"Vault '{self.name}' initialized (encrypted={encrypted})")
    
    @classmethod
    def create(
        cls,
        name: str = "default",
        encrypted: bool = True,
        encryption_key: Optional[str] = None,
        access_policy: Optional[Dict] = None
    ) -> "Vault":
        """Factory method to create a new vault.
        
        Args:
            name: Name of the vault
            encrypted: Whether to enable encryption
            encryption_key: Optional encryption key
            access_policy: Optional access control policy
            
        Returns:
            Vault: New vault instance
        """
        vault = cls(name=name, encrypted=encrypted, encryption_key=encryption_key)
        if access_policy:
            vault._access_policy = access_policy
        return vault
    
    def store(self, key: str, value: Any) -> bool:
        """Store a value in the vault.
        
        Args:
            key: Storage key
            value: Value to store
            
        Returns:
            bool: True if stored successfully
        """
        # In production, value would be encrypted here
        encrypted_value = self._encrypt(value) if self.encrypted else value
        self._data[key] = {
            "value": encrypted_value,
            "stored_at": datetime.now().isoformat(),
            "encrypted": self.encrypted
        }
        self._log_access("store", key)
        self._logger.debug(f"Stored key '{key}' in vault")
        return True
    
    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value from the vault.
        
        Args:
            key: Storage key
            
        Returns:
            Optional value if found, None otherwise
        """
        if key not in self._data:
            self._logger.warning(f"Key '{key}' not found in vault")
            return None
        
        data_entry = self._data[key]
        value = data_entry["value"]
        
        # In production, would decrypt here
        decrypted_value = self._decrypt(value) if data_entry["encrypted"] else value
        self._log_access("retrieve", key)
        return decrypted_value
    
    def delete(self, key: str) -> bool:
        """Delete a value from the vault.
        
        Args:
            key: Storage key
            
        Returns:
            bool: True if deleted, False if not found
        """
        if key in self._data:
            del self._data[key]
            self._log_access("delete", key)
            self._logger.info(f"Deleted key '{key}' from vault")
            return True
        return False
    
    def list_keys(self) -> list:
        """List all keys stored in the vault.
        
        Returns:
            List of storage keys
        """
        return list(self._data.keys())
    
    def _encrypt(self, value: Any) -> str:
        """Encrypt a value (stub implementation).
        
        Args:
            value: Value to encrypt
            
        Returns:
            Encrypted value as string
        """
        # Stub: In production, use proper encryption (AES-256, etc.)
        value_str = str(value)
        return base64.b64encode(value_str.encode()).decode()
    
    def _decrypt(self, encrypted_value: str) -> Any:
        """Decrypt a value (stub implementation).
        
        Args:
            encrypted_value: Encrypted value
            
        Returns:
            Decrypted value
        """
        # Stub: In production, use proper decryption
        try:
            return base64.b64decode(encrypted_value.encode()).decode()
        except:
            return encrypted_value
    
    def _log_access(self, operation: str, key: str) -> None:
        """Log vault access for audit trail.
        
        Args:
            operation: Type of operation (store/retrieve/delete)
            key: Key being accessed
        """
        self._access_log.append({
            "operation": operation,
            "key": key,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_access_log(self, limit: int = 100) -> list:
        """Get vault access log.
        
        Args:
            limit: Maximum number of entries
            
        Returns:
            List of access log entries
        """
        return self._access_log[-limit:]
    
    def _generate_vault_id(self) -> str:
        """Generate a unique vault ID.
        
        Returns:
            Unique vault identifier
        """
        import uuid
        return f"vault-{uuid.uuid4().hex[:12]}"
    
    def __repr__(self) -> str:
        return f"Vault(id={self.vault_id}, name='{self.name}', keys={len(self._data)})"
