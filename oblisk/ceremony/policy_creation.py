"""
Policy Creation — Natural Language to Datalog Wizard

The PolicyWizard guides humans through creating governance rules
without requiring them to know Prolog/Datalog syntax.

It translates natural language descriptions into formal constraints
that the ConstraintEngine can verify against proof trees.

Principle: The human writes the law in their own words. The system enforces it precisely.
"""

from __future__ import annotations

from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

from ..vault.policy_store import PolicyStore, Policy, ConstraintType


class PolicyTemplate(Enum):
    """Pre-built policy templates for common governance needs."""
    NO_LOCATION_SHARING = "no_location_sharing"
    NO_CONTACT_SHARING = "no_contact_sharing"
    NO_FINANCIAL_DATA = "no_financial_data"
    NO_CLOUD_UPLOAD = "no_cloud_upload"
    NO_THIRD_PARTY_APIS = "no_third_party_apis"
    APPROVE_ALL_TRANSFERS = "approve_all_transfers"
    LIMIT_REQUEST_RATE = "limit_request_rate"
    TIME_RESTRICTED = "time_restricted"
    DOMAIN_WHITELIST = "domain_whitelist"
    CUSTOM = "custom"


@dataclass
class TemplateConfig:
    """Configuration for a policy template."""
    template: PolicyTemplate
    description: str
    rule_template: str
    constraint_type: ConstraintType
    default_metadata: dict = field(default_factory=dict)
    questions: list[str] = field(default_factory=list)


class PolicyWizard:
    """
    Guides humans through creating governance policies.
    
    The PolicyWizard provides a user-friendly interface for policy creation:
    1. Presents templates for common scenarios
    2. Asks clarifying questions
    3. Translates answers into Datalog rules
    4. Validates the generated rules
    5. Stores policies in the vault
    
    Attributes:
        policy_store: Where created policies are stored
        templates: Available policy templates
    """
    
    TEMPLATES: dict[PolicyTemplate, TemplateConfig] = {
        PolicyTemplate.NO_LOCATION_SHARING: TemplateConfig(
            template=PolicyTemplate.NO_LOCATION_SHARING,
            description="Prevent any location data from leaving your device",
            rule_template="location_data(X) :- never_leaves_device(X).",
            constraint_type=ConstraintType.NEVER_LEAVE_DEVICE,
            questions=[
                "Should this apply to approximate location (GPS neighborhood) or exact coordinates?",
                "Are there any apps that should be exempt from this rule?",
            ],
        ),
        PolicyTemplate.NO_CONTACT_SHARING: TemplateConfig(
            template=PolicyTemplate.NO_CONTACT_SHARING,
            description="Prevent your contacts/address book from being shared",
            rule_template="contact_data(X) :- never_share(X).",
            constraint_type=ConstraintType.NEVER_SHARE,
            questions=[
                "Does this include sharing with apps you currently use?",
            ],
        ),
        PolicyTemplate.NO_FINANCIAL_DATA: TemplateConfig(
            template=PolicyTemplate.NO_FINANCIAL_DATA,
            description="Block any financial or payment data from external transfer",
            rule_template="financial_data(X) :- never_leaves_device(X), never_share(X).",
            constraint_type=ConstraintType.NEVER_SHARE,
            questions=[
                "Should this block all payment-related API calls?",
                "Do you use any financial apps that need exemptions?",
            ],
        ),
        PolicyTemplate.NO_CLOUD_UPLOAD: TemplateConfig(
            template=PolicyTemplate.NO_CLOUD_UPLOAD,
            description="Prevent any data from being uploaded to cloud services",
            rule_template="cloud_upload(X) :- blocked(X).",
            constraint_type=ConstraintType.NEVER_LEAVE_DEVICE,
            questions=[
                "Are there specific cloud services you trust (iCloud, Google Drive, etc.)?",
            ],
        ),
        PolicyTemplate.NO_THIRD_PARTY_APIS: TemplateConfig(
            template=PolicyTemplate.NO_THIRD_PARTY_APIS,
            description="Block calls to third-party APIs unless explicitly approved",
            rule_template="third_party_api(X) :- requires_approval(X).",
            constraint_type=ConstraintType.REQUIRES_EXPLICIT_APPROVAL,
            questions=[
                "Should this block ALL external APIs or only unknown ones?",
            ],
        ),
        PolicyTemplate.APPROVE_ALL_TRANSFERS: TemplateConfig(
            template=PolicyTemplate.APPROVE_ALL_TRANSFERS,
            description="Require your explicit approval for ANY data transfer",
            rule_template="data_transfer(X) :- requires_approval(X), user_consented(X).",
            constraint_type=ConstraintType.REQUIRES_EXPLICIT_APPROVAL,
            questions=[
                "Do you want to approve each transfer individually or set up blanket rules?",
            ],
        ),
        PolicyTemplate.LIMIT_REQUEST_RATE: TemplateConfig(
            template=PolicyTemplate.LIMIT_REQUEST_RATE,
            description="Limit how many API requests agents can make per minute",
            rule_template="agent_action(X) :- rate_limited(X, {limit}).",
            constraint_type=ConstraintType.RATE_LIMITED,
            default_metadata={"max_actions_per_minute": 10},
            questions=[
                "How many requests per minute should be allowed? (default: 10)",
            ],
        ),
        PolicyTemplate.TIME_RESTRICTED: TemplateConfig(
            template=PolicyTemplate.TIME_RESTRICTED,
            description="Only allow agent actions during certain hours",
            rule_template="agent_action(X) :- time_bound(X, {start}, {end}).",
            constraint_type=ConstraintType.TIME_BOUND,
            default_metadata={"allowed_hours": "09:00-17:00"},
            questions=[
                "What hours should agents be active? (e.g., 9 AM to 5 PM)",
            ],
        ),
        PolicyTemplate.DOMAIN_WHITELIST: TemplateConfig(
            template=PolicyTemplate.DOMAIN_WHITELIST,
            description="Only allow connections to approved domains",
            rule_template="api_call(X) :- domain_restricted(X, {domains}).",
            constraint_type=ConstraintType.DOMAIN_RESTRICTED,
            default_metadata={"allowed_domains": []},
            questions=[
                "Which domains should be allowed? (comma-separated)",
            ],
        ),
        PolicyTemplate.CUSTOM: TemplateConfig(
            template=PolicyTemplate.CUSTOM,
            description="Write your own rule in Prolog/Datalog",
            rule_template="",  # User provides this
            constraint_type=ConstraintType.CUSTOM,
            questions=[
                "Describe what you want to restrict (in your own words):",
                "Any specific data types, actions, or destinations to mention?",
            ],
        ),
    }
    
    def __init__(self, policy_store: PolicyStore):
        self.policy_store = policy_store
    
    def list_templates(self) -> list[dict]:
        """
        List all available policy templates.
        
        Returns:
            List of template descriptions for human selection
        """
        return [
            {
                "id": t.template.value,
                "description": t.description,
                "questions_count": len(t.questions),
            }
            for t in self.TEMPLATES.values()
        ]
    
    def create_from_template(
        self, 
        template_id: str, 
        answers: list[str],
        policy_id: Optional[str] = None
    ) -> Policy:
        """
        Create a policy from a template using human answers.
        
        Args:
            template_id: Which template to use
            answers: Human's answers to the template questions
            policy_id: Optional custom policy identifier
            
        Returns:
            The created Policy
        """
        try:
            template_enum = PolicyTemplate(template_id)
        except ValueError:
            raise ValueError(f"Unknown template: {template_id}")
        
        config = self.TEMPLATES[template_enum]
        
        # Generate the rule from template and answers
        rule = self._generate_rule(config, answers)
        
        # Generate metadata from answers
        metadata = self._generate_metadata(config, answers)
        
        # Create policy
        policy = Policy(
            id=policy_id or f"{template_id}_policy",
            constraint_type=config.constraint_type,
            rule=rule,
            description=config.description,
            metadata={**config.default_metadata, **metadata},
        )
        
        # Validate
        is_valid, error = policy.validate_rule()
        if not is_valid:
            raise ValueError(f"Generated rule is invalid: {error}")
        
        # Store
        self.policy_store.add_policy(policy)
        
        return policy
    
    def create_custom(self, description: str, policy_id: str) -> Policy:
        """
        Create a policy from a natural language description.
        
        This uses a simple translation layer to convert natural language
        into Datalog rules. In production, this could use a constrained LLM
        that runs through the InferenceFilter.
        
        Args:
            description: Human's description of the desired rule
            policy_id: Policy identifier
            
        Returns:
            The created Policy
        """
        description_lower = description.lower()
        
        # Simple keyword-based translation
        if "location" in description_lower or "gps" in description_lower:
            rule = "location_data(X) :- never_leaves_device(X)."
            constraint_type = ConstraintType.NEVER_LEAVE_DEVICE
        elif "contact" in description_lower or "address book" in description_lower:
            rule = "contact_data(X) :- never_share(X)."
            constraint_type = ConstraintType.NEVER_SHARE
        elif "financial" in description_lower or "payment" in description_lower or "money" in description_lower:
            rule = "financial_data(X) :- never_leaves_device(X), never_share(X)."
            constraint_type = ConstraintType.NEVER_SHARE
        elif "cloud" in description_lower or "upload" in description_lower:
            rule = "cloud_upload(X) :- blocked(X)."
            constraint_type = ConstraintType.NEVER_LEAVE_DEVICE
        elif "approve" in description_lower or "ask me" in description_lower or "permission" in description_lower:
            rule = "sensitive_action(X) :- requires_approval(X), user_consented(X)."
            constraint_type = ConstraintType.REQUIRES_EXPLICIT_APPROVAL
        elif "limit" in description_lower or "rate" in description_lower or "slow" in description_lower:
            rule = "agent_action(X) :- rate_limited(X, 10)."
            constraint_type = ConstraintType.RATE_LIMITED
        elif "domain" in description_lower or "website" in description_lower or "url" in description_lower:
            rule = "api_call(X) :- domain_restricted(X, [])."
            constraint_type = ConstraintType.DOMAIN_RESTRICTED
        elif "time" in description_lower or "hour" in description_lower or "schedule" in description_lower:
            rule = "agent_action(X) :- time_bound(X, 09, 17)."
            constraint_type = ConstraintType.TIME_BOUND
        else:
            # Fallback: create a custom rule from the description
            rule = f"custom_constraint(X) :- user_authorized(X), {self._sanitize_description(description)}."
            constraint_type = ConstraintType.CUSTOM
        
        policy = Policy(
            id=policy_id,
            constraint_type=constraint_type,
            rule=rule,
            description=description,
        )
        
        self.policy_store.add_policy(policy)
        return policy
    
    def preview_policy(self, description: str) -> str:
        """
        Preview what Datalog rule would be generated from a description.
        
        This lets humans see the translation before committing it.
        
        Args:
            description: Natural language description
            
        Returns:
            The Datalog rule that would be generated
        """
        # Reuse create_custom logic without storing
        description_lower = description.lower()
        
        if "location" in description_lower:
            return "location_data(X) :- never_leaves_device(X)."
        elif "contact" in description_lower:
            return "contact_data(X) :- never_share(X)."
        elif "financial" in description_lower or "payment" in description_lower:
            return "financial_data(X) :- never_leaves_device(X), never_share(X)."
        elif "cloud" in description_lower:
            return "cloud_upload(X) :- blocked(X)."
        elif "approve" in description_lower:
            return "sensitive_action(X) :- requires_approval(X), user_consented(X)."
        elif "limit" in description_lower or "rate" in description_lower:
            return "agent_action(X) :- rate_limited(X, 10)."
        elif "domain" in description_lower:
            return "api_call(X) :- domain_restricted(X, [])."
        elif "time" in description_lower:
            return "agent_action(X) :- time_bound(X, 09, 17)."
        else:
            return f"custom_constraint(X) :- user_authorized(X), {self._sanitize_description(description)}."
    
    def _generate_rule(self, config: TemplateConfig, answers: list[str]) -> str:
        """Generate a Datalog rule from template and answers."""
        rule = config.rule_template
        
        # Simple template substitution based on template type
        if config.template == PolicyTemplate.LIMIT_REQUEST_RATE and answers:
            try:
                limit = int(answers[0])
                rule = rule.replace("{limit}", str(limit))
            except ValueError:
                rule = rule.replace("{limit}", "10")
        
        elif config.template == PolicyTemplate.DOMAIN_WHITELIST and answers:
            domains = [d.strip() for d in answers[0].split(",")]
            domains_str = ", ".join(f'"{d}"' for d in domains)
            rule = rule.replace("{domains}", f"[{domains_str}]")
        
        return rule
    
    def _generate_metadata(self, config: TemplateConfig, answers: list[str]) -> dict:
        """Generate metadata from template answers."""
        metadata = {}
        
        if config.template == PolicyTemplate.LIMIT_REQUEST_RATE and answers:
            try:
                metadata["max_actions_per_minute"] = int(answers[0])
            except ValueError:
                pass
        
        elif config.template == PolicyTemplate.DOMAIN_WHITELIST and answers:
            domains = [d.strip() for d in answers[0].split(",")]
            metadata["allowed_domains"] = domains
        
        elif config.template == PolicyTemplate.TIME_RESTRICTED and answers:
            metadata["allowed_hours"] = answers[0] if answers else "09:00-17:00"
        
        return metadata
    
    def _sanitize_description(self, description: str) -> str:
        """Sanitize a natural language description for use in Datalog."""
        # Remove special characters, keep alphanumeric and underscores
        sanitized = "".join(c if c.isalnum() or c in " _" else "" for c in description)
        return "_".join(sanitized.lower().split())[:50]
