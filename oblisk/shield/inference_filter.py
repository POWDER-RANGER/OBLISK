"""
Inference Filter — LLM Call Interceptor

The InferenceFilter intercepts all LLM/AI inference calls from agents
and ensures that no vault data, PII, or sensitive information leaks
into the inference context.

This is critical because LLMs are inherently leaky — they may memorize,
repeat, or exfiltrate data through prompts or context windows.

Principle: The LLM never sees vault data. Ever.
"""

from __future__ import annotations

import re
import hashlib
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from ..vault.vault import Vault
    from ..vault.consent_log import ConsentLog


class FilterAction(Enum):
    """Actions the inference filter can take."""
    PASS = "pass"           # Prompt is safe, allow inference
    REDACT = "redact"       # Remove sensitive data, then allow
    BLOCK = "block"         # Prompt contains vault data, block entirely
    SANITIZE = "sanitize"   # Replace sensitive values with placeholders


@dataclass
class FilterResult:
    """
    Result of filtering an inference prompt.
    
    Attributes:
        action: What the filter decided
        original_prompt: The original prompt (for audit only)
        sanitized_prompt: The safe prompt to send to LLM (if action != BLOCK)
        replacements: List of what was redacted/sanitized
        reason: Human-readable explanation
    """
    action: FilterAction
    original_prompt: str
    sanitized_prompt: str
    replacements: list[dict] = field(default_factory=list)
    reason: str = ""


class InferenceFilter:
    """
    Intercepts and sanitizes all LLM inference calls.
    
    The InferenceFilter ensures that no vault data, PII, or sensitive
    information ever reaches an external LLM. It acts as a transparent
    proxy between agents and inference APIs.
    
    Attributes:
        vault: Reference to vault (for pattern matching)
        vault_patterns: Patterns that match vault data formats
        pii_patterns: Patterns that match PII
        redaction_map: Maps sensitive values to placeholders
    """
    
    # Patterns that match vault data
    VAULT_PATTERNS = [
        r"vault://[^\s]+",
        r"[A-Fa-f0-9]{128,}",  # Very long hex = likely ciphertext
        r"OBLISK_(?:MASTER|PRIVATE|SIGNING)_KEY",
        r"-----BEGIN (?:ENCRYPTED|PRIVATE) KEY-----",
    ]
    
    # PII patterns (expanded from DataGuardian)
    PII_PATTERNS = [
        (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN_REDACTED]"),
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_REDACTED]"),
        (r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE_REDACTED]"),
        (r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "[CARD_REDACTED]"),
    ]
    
    def __init__(self, vault: "Vault"):
        self.vault = vault
        self._interception_count: int = 0
        self._block_count: int = 0
        self._redact_count: int = 0
    
    def filter_prompt(self, agent_id: str, prompt: str) -> FilterResult:
        """
        Filter an inference prompt before it reaches the LLM.
        
        This is called by the agent runtime before every LLM call.
        It scans for vault data, PII, and other sensitive information.
        
        Args:
            agent_id: Which agent is making the inference call
            prompt: The raw prompt text
            
        Returns:
            FilterResult with sanitized prompt or block decision
        """
        self._interception_count += 1
        
        # Check for vault data patterns
        vault_detected, vault_matches = self._scan_vault_data(prompt)
        
        if vault_detected:
            self._block_count += 1
            return FilterResult(
                action=FilterAction.BLOCK,
                original_prompt=prompt,
                sanitized_prompt="",
                replacements=[{"type": "vault_data", "matches": vault_matches}],
                reason=(
                    f"BLOCKED: Vault data pattern(s) detected in prompt from agent {agent_id}. "
                    f"The LLM must never see vault data. Matches: {vault_matches}"
                ),
            )
        
        # Sanitize PII
        sanitized = prompt
        replacements = []
        
        for pattern, placeholder in self.PII_PATTERNS:
            matches = re.findall(pattern, sanitized)
            if matches:
                sanitized = re.sub(pattern, placeholder, sanitized)
                replacements.append({
                    "type": "pii",
                    "pattern": placeholder,
                    "count": len(matches),
                })
        
        if replacements:
            self._redact_count += 1
            return FilterResult(
                action=FilterAction.SANITIZE,
                original_prompt=prompt,
                sanitized_prompt=sanitized,
                replacements=replacements,
                reason=(
                    f"SANITIZED: Removed {len(replacements)} type(s) of PII "
                    f"from prompt before inference."
                ),
            )
        
        # No issues found
        return FilterResult(
            action=FilterAction.PASS,
            original_prompt=prompt,
            sanitized_prompt=prompt,
            reason="Prompt passed all security checks. No vault data or PII detected.",
        )
    
    def filter_response(self, agent_id: str, response: str) -> str:
        """
        Filter an LLM response before it reaches the agent.
        
        Ensures the LLM didn't inadvertently include vault data patterns
        in its response (e.g., from training data or prompt injection).
        
        Args:
            agent_id: Which agent receives the response
            response: Raw LLM response
            
        Returns:
            Sanitized response
        """
        # Scan for vault data that shouldn't be in responses
        vault_detected, _ = self._scan_vault_data(response)
        
        if vault_detected:
            # Replace vault patterns with warning
            sanitized = response
            for pattern in self.VAULT_PATTERNS:
                sanitized = re.sub(pattern, "[VAULT_DATA_FILTERED]", sanitized)
            return sanitized
        
        return response
    
    def get_statistics(self) -> dict:
        """Get filter interception statistics."""
        return {
            "interceptions": self._interception_count,
            "blocked": self._block_count,
            "redacted": self._redact_count,
            "pass_rate": (
                (self._interception_count - self._block_count - self._redact_count)
                / self._interception_count if self._interception_count > 0 else 0
            ),
        }
    
    def _scan_vault_data(self, text: str) -> tuple[bool, list[str]]:
        """Scan text for vault data patterns. Returns (detected, matches)."""
        matches = []
        for pattern in self.VAULT_PATTERNS:
            found = re.findall(pattern, text)
            matches.extend(found)
        return len(matches) > 0, matches
