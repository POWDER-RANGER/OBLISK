"""
Intent Parser — Natural Language → Governed Intent

Translates human natural language into structured, governed intents that
conform to vault policies. This is the entry point where human expression
meets machine enforceability.

The parser ensures:
    1. The intent is syntactically valid
    2. The intent does not violate hard constraints (pre-check)
    3. The intent contains enough information for planning
    4. Ambiguous or dangerous intents are flagged for human clarification
"""

from __future__ import annotations

import re
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from ..vault.policy_store import PolicyStore
    from ..vault.intent_store import IntentStore


@dataclass
class ParsedIntent:
    """
    A structured intent parsed from natural language.
    
    This is the intermediate representation between raw human expression
    and a cryptographically signed vault intent.
    
    Attributes:
        raw_input: The original natural language input
        goal: Extracted goal statement
        entities: Named entities detected in the input
        constraints: Additional constraints extracted or implied
        risk_flags: Warnings about potentially risky operations
        requires_clarification: Whether human needs to clarify before proceeding
        clarification_prompt: Question to ask the human if clarification needed
    """
    raw_input: str
    goal: str
    entities: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    requires_clarification: bool = False
    clarification_prompt: str = ""


class IntentParser:
    """
    Translates human natural language into governed, structured intents.
    
    The IntentParser is the bridge between human expression and machine
    governance. It extracts intent from natural language, checks against
    vault policies, and flags anything requiring human attention.
    
    Attributes:
        policy_store: Reference to vault policies for pre-check
    """
    
    # Patterns that suggest data exfiltration risk
    EXFIL_PATTERNS = [
        r"\b(send|email|upload|share|transmit|forward)\b.*\b(data|file|document|information)\b",
        r"\b(export|backup to cloud|sync to)\b",
        r"\b(third.party|external service|API)\b",
    ]
    
    # Patterns that suggest irreversible actions
    IRREVERSIBLE_PATTERNS = [
        r"\b(delete|remove|destroy|wipe|erase)\b",
        r"\b(irreversible|permanent|can't undo)\b",
    ]
    
    # Patterns that suggest financial/legal risk
    FINANCIAL_PATTERNS = [
        r"\b(pay|transfer|send money|wire)\b.*\$?\d+",
        r"\b(sign|agree to|accept)\b.*\b(contract|terms|agreement)\b",
    ]
    
    def __init__(self, policy_store: "PolicyStore"):
        self.policy_store = policy_store
    
    def parse(self, natural_language: str) -> ParsedIntent:
        """
        Parse natural language into a structured, governed intent.
        
        Args:
            natural_language: Raw human input, e.g.
                "Find my documents about Project Alpha and summarize them"
                
        Returns:
            ParsedIntent with extracted goal, entities, constraints, and risk flags
        """
        raw = natural_language.strip()
        
        # Extract the core goal
        goal = self._extract_goal(raw)
        
        # Detect entities
        entities = self._extract_entities(raw)
        
        # Apply risk analysis
        risk_flags = self._analyze_risk(raw, goal)
        
        # Extract implied constraints from policies
        constraints = self._infer_constraints(raw)
        
        # Determine if clarification is needed
        requires_clarification, prompt = self._check_clarification_needed(
            raw, goal, risk_flags
        )
        
        parsed = ParsedIntent(
            raw_input=raw,
            goal=goal,
            entities=entities,
            constraints=constraints,
            risk_flags=risk_flags,
            requires_clarification=requires_clarification,
            clarification_prompt=prompt,
        )
        
        return parsed
    
    def _extract_goal(self, text: str) -> str:
        """
        Extract the core goal from natural language.
        
        Simple extraction — in production this would use an LLM
        constrained by the inference filter to prevent data leakage.
        """
        # Remove filler words and normalize
        text = text.lower().strip()
        
        # Common prefixes to strip
        prefixes = [
            "can you", "could you", "please", "i want you to",
            "i need you to", "i'd like you to", "help me",
            "i want", "i need", "i'd like",
        ]
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
        
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]
        
        return text
    
    def _extract_entities(self, text: str) -> list[str]:
        """
        Extract named entities from the input.
        
        Simple regex-based extraction. In production, this runs
        through the InferenceFilter to prevent vault data leakage.
        """
        entities = []
        
        # Quoted strings are likely entity names
        quoted = re.findall(r'["\'](.+?)["\']', text)
        entities.extend(quoted)
        
        # Capitalized phrases (potential proper nouns)
        # Filter out sentence-start capitals
        words = text.split()
        for i, word in enumerate(words):
            if i > 0 and word[0].isupper() and len(word) > 1:
                entities.append(word)
        
        return list(set(entities))
    
    def _analyze_risk(self, raw: str, goal: str) -> list[str]:
        """
        Analyze the intent for risky operations.
        
        Returns a list of risk flag strings. Non-empty list means
        the human should review before proceeding.
        """
        flags = []
        text_lower = raw.lower()
        
        for pattern in self.EXFIL_PATTERNS:
            if re.search(pattern, text_lower):
                flags.append("POTENTIAL_DATA_EXFILTRATION: Intent involves sending data externally")
                break
        
        for pattern in self.IRREVERSIBLE_PATTERNS:
            if re.search(pattern, text_lower):
                flags.append("IRREVERSIBLE_ACTION: Intent may delete or destroy data")
                break
        
        for pattern in self.FINANCIAL_PATTERNS:
            if re.search(pattern, text_lower):
                flags.append("FINANCIAL_OR_LEGAL_RISK: Intent involves financial or legal commitments")
                break
        
        return flags
    
    def _infer_constraints(self, raw: str) -> list[str]:
        """
        Infer additional constraints from the natural language and vault policies.
        
        For example, if vault policy says "never share location data",
        and the intent mentions location, add an implicit constraint.
        """
        constraints = []
        text_lower = raw.lower()
        
        # Check active policies for relevance
        for policy in self.policy_store.get_active_policies():
            if policy.constraint_type.value in text_lower:
                constraints.append(f"policy:{policy.id}")
        
        return constraints
    
    def _check_clarification_needed(
        self, raw: str, goal: str, risk_flags: list[str]
    ) -> tuple[bool, str]:
        """
        Determine if the human needs to clarify before proceeding.
        
        Returns:
            (needs_clarification, prompt_for_human)
        """
        if risk_flags:
            risk_summary = "; ".join(risk_flags)
            return True, (
                f"This intent has been flagged for review: {risk_summary}. "
                f"Please confirm you want to proceed with: '{goal}'"
            )
        
        if len(goal.split()) < 3:
            return True, (
                "Your intent seems unclear. Could you provide more details "
                "about what you'd like me to do?"
            )
        
        # Check against hard constraints
        for policy in self.policy_store.get_active_policies():
            # Simple keyword check — in production, this uses the constraint engine
            if policy.constraint_type.value in raw.lower():
                return True, (
                    f"Your intent may conflict with policy '{policy.id}'. "
                    f"Please review and confirm."
                )
        
        return False, ""
