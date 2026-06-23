"""
Constraint Engine — Hard Logical Verification

The ConstraintEngine verifies that proof trees from the SymbolicPlanner
satisfy all hard constraints from the vault's PolicyStore.

It uses Prolog/Datalog evaluation to check that every step in a plan
is authorized by the user's governance rules. A plan that violates
any hard constraint is rejected before any agent executes it.

Principle: The human's law is absolute. No plan executes without proof of compliance.
"""

from __future__ import annotations

import re
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from ..vault.policy_store import PolicyStore
    from ..vault.policy_store import Policy


@dataclass
class ConstraintResult:
    """
    Result of constraint verification on a proof tree.
    
    Attributes:
        passed: Whether all constraints were satisfied
        violations: List of constraint violations found
        checked_policies: List of policies that were checked
        proof_tree_summary: Human-readable summary of the verification
    """
    passed: bool
    violations: list[dict] = field(default_factory=list)
    checked_policies: list[str] = field(default_factory=list)
    proof_tree_summary: str = ""
    
    def to_explanation(self) -> str:
        """Generate a natural language explanation of the result."""
        if self.passed:
            return (
                f"All {len(self.checked_policies)} policies verified. "
                "Plan is authorized for execution."
            )
        
        violation_descs = [v["explanation"] for v in self.violations]
        return (
            f"Plan blocked: {len(self.violations)} constraint violation(s) found. "
            f"Violations: {'; '.join(violation_descs)}"
        )


class ConstraintEngine:
    """
    Verifies proof trees against vault policy constraints.
    
    The ConstraintEngine is the gatekeeper. It evaluates each step of
    a proposed plan against the user's hard constraints and rejects
    any plan that would violate them.
    
    Attributes:
        policy_store: Reference to the vault's policies
    """
    
    def __init__(self, policy_store: "PolicyStore"):
        self.policy_store = policy_store
    
    def verify(self, proof_tree: dict, constraints: list[dict]) -> ConstraintResult:
        """
        Verify that a proof tree satisfies all hard constraints.
        
        This is the primary method called by the FlowController before
        authorizing any agent action.
        
        Args:
            proof_tree: The proof tree from the SymbolicPlanner containing:
                - steps: List of planned actions
                - data_access: List of data elements accessed
                - external_calls: List of external API calls
                - data_flow: List of data movements
            constraints: Active policy constraints from the vault
            
        Returns:
            ConstraintResult with pass/fail and detailed violations
        """
        violations = []
        checked_policies = []
        
        steps = proof_tree.get("steps", [])
        data_access = proof_tree.get("data_access", [])
        external_calls = proof_tree.get("external_calls", [])
        data_flow = proof_tree.get("data_flow", [])
        
        # Get all active policies
        active_policies = self.policy_store.get_active_policies()
        
        for policy in active_policies:
            checked_policies.append(policy.id)
            
            # Check data locality constraints
            if "never_leaves_device" in policy.rule:
                violation = self._check_data_locality(data_flow, policy)
                if violation:
                    violations.append(violation)
            
            # Check sharing constraints
            if "never_share" in policy.rule:
                violation = self._check_sharing(external_calls, data_flow, policy)
                if violation:
                    violations.append(violation)
            
            # Check approval requirements
            if "requires_approval" in policy.rule:
                violation = self._check_approval_requirement(steps, external_calls, policy)
                if violation:
                    violations.append(violation)
            
            # Check rate limits
            if "rate_limited" in policy.rule:
                violation = self._check_rate_limit(steps, policy)
                if violation:
                    violations.append(violation)
            
            # Check domain restrictions
            if "domain_restricted" in policy.rule:
                violation = self._check_domain_restriction(external_calls, policy)
                if violation:
                    violations.append(violation)
            
            # Check custom constraints
            if policy.constraint_type.value == "custom":
                violation = self._check_custom_constraint(proof_tree, policy)
                if violation:
                    violations.append(violation)
        
        result = ConstraintResult(
            passed=len(violations) == 0,
            violations=violations,
            checked_policies=checked_policies,
            proof_tree_summary=self._summarize_proof_tree(proof_tree),
        )
        
        return result
    
    def _check_data_locality(self, data_flow: list[dict], policy: "Policy") -> Optional[dict]:
        """Check if data would leave the device."""
        for flow in data_flow:
            destination = flow.get("destination", "")
            if destination in ("external", "cloud", "third_party", "network"):
                data_type = flow.get("data_type", "unknown")
                if "location_data" in policy.rule or "sensitive_data" in policy.rule:
                    return {
                        "policy_id": policy.id,
                        "rule": policy.rule,
                        "explanation": (
                            f"Policy '{policy.id}' violated: {data_type} would leave "
                            f"the device (destination: {destination})"
                        ),
                        "severity": "critical",
                    }
        return None
    
    def _check_sharing(
        self, external_calls: list[dict], data_flow: list[dict], policy: "Policy"
    ) -> Optional[dict]:
        """Check if data would be shared externally."""
        for call in external_calls:
            if call.get("transmits_data", False):
                return {
                    "policy_id": policy.id,
                    "rule": policy.rule,
                    "explanation": (
                        f"Policy '{policy.id}' violated: External call to "
                        f"{call.get('endpoint', 'unknown')} would transmit data"
                    ),
                    "severity": "critical",
                }
        
        for flow in data_flow:
            if flow.get("destination") in ("shared", "third_party", "public"):
                return {
                    "policy_id": policy.id,
                    "rule": policy.rule,
                    "explanation": (
                        f"Policy '{policy.id}' violated: Data flow to "
                        f"{flow.get('destination')} constitutes sharing"
                    ),
                    "severity": "critical",
                }
        
        return None
    
    def _check_approval_requirement(
        self, steps: list[dict], external_calls: list[dict], policy: "Policy"
    ) -> Optional[dict]:
        """Check if any step requires explicit approval."""
        # This checks against the consent log — if the action hasn't been
        # explicitly consented to, it's a violation
        # (Integration with ConsentLog happens in FlowController)
        for step in steps:
            if step.get("requires_explicit_approval", False):
                return {
                    "policy_id": policy.id,
                    "rule": policy.rule,
                    "explanation": (
                        f"Policy '{policy.id}' requires explicit approval for: "
                        f"{step.get('description', 'unknown action')}"
                    ),
                    "severity": "warning",
                    "requires_human_approval": True,
                }
        return None
    
    def _check_rate_limit(self, steps: list[dict], policy: "Policy") -> Optional[dict]:
        """Check if plan exceeds rate limits."""
        max_actions = policy.metadata.get("max_actions_per_minute", 10)
        if len(steps) > max_actions:
            return {
                "policy_id": policy.id,
                "rule": policy.rule,
                "explanation": (
                    f"Policy '{policy.id}' violated: Plan has {len(steps)} actions, "
                    f"exceeding rate limit of {max_actions}"
                ),
                "severity": "warning",
            }
        return None
    
    def _check_domain_restriction(self, external_calls: list[dict], policy: "Policy") -> Optional[dict]:
        """Check if external calls are to allowed domains."""
        allowed_domains = policy.metadata.get("allowed_domains", [])
        if not allowed_domains:
            return None
        
        for call in external_calls:
            domain = call.get("domain", "")
            if domain and domain not in allowed_domains:
                return {
                    "policy_id": policy.id,
                    "rule": policy.rule,
                    "explanation": (
                        f"Policy '{policy.id}' violated: Call to {domain} is not in "
                        f"allowed domains: {allowed_domains}"
                    ),
                    "severity": "critical",
                }
        return None
    
    def _check_custom_constraint(self, proof_tree: dict, policy: "Policy") -> Optional[dict]:
        """
        Evaluate a custom Prolog/Datalog constraint.
        
        In production, this would embed a Datalog engine (like Souffle
        or a Python Prolog interpreter) to evaluate the rule against
        the proof tree facts.
        """
        # Parse the custom rule to extract what it guards
        rule = policy.rule
        
        # Extract the head of the rule (what it protects)
        match = re.match(r"(\w+)\(([^)]+)\)\s*:-", rule)
        if match:
            predicate = match.group(1)
            variable = match.group(2)
            
            # Check if the proof tree touches this predicate
            for step in proof_tree.get("steps", []):
                step_str = str(step).lower()
                if predicate.lower() in step_str:
                    return {
                        "policy_id": policy.id,
                        "rule": policy.rule,
                        "explanation": (
                            f"Custom policy '{policy.id}' triggered: "
                            f"step involves '{predicate}' which is guarded by: {rule}"
                        ),
                        "severity": "warning",
                    }
        
        return None
    
    def _summarize_proof_tree(self, proof_tree: dict) -> str:
        """Generate a human-readable summary of the proof tree."""
        steps = proof_tree.get("steps", [])
        data_access = proof_tree.get("data_access", [])
        external_calls = proof_tree.get("external_calls", [])
        
        summary_parts = [
            f"Plan: {len(steps)} step(s)",
            f"Data access: {len(data_access)} element(s)",
            f"External calls: {len(external_calls)} call(s)",
        ]
        
        if external_calls:
            call_list = ", ".join(c.get("endpoint", "?") for c in external_calls)
            summary_parts.append(f"Endpoints: {call_list}")
        
        return "; ".join(summary_parts)
    
    def explain_verification(self, result: ConstraintResult) -> str:
        """
        Generate a detailed natural language explanation of verification.
        
        This is used by the ProofExporter to create human-readable
        explanations of why a plan was or wasn't authorized.
        """
        lines = [
            "Constraint Verification Report",
            "=" * 40,
            f"Result: {'PASSED' if result.passed else 'BLOCKED'}",
            f"Policies checked: {', '.join(result.checked_policies)}",
            "",
        ]
        
        if result.violations:
            lines.append("Violations:")
            for v in result.violations:
                lines.append(f"  - [{v['severity'].upper()}] {v['explanation']}")
            lines.append("")
        
        lines.append(f"Summary: {result.proof_tree_summary}")
        
        return "\n".join(lines)
