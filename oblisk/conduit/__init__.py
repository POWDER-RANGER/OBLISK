"""
CONDUIT — The Shaft of the OBLISK

The conduit ensures one-directional flow: Human Intent → Vault → Planner → Agents.
No agent can push information back up to the human without consent.
No action executes without proof tree verification.

Components:
    - intent_parser.py: Translates human natural language into governed intent
    - constraint_engine.py: Hard logical constraints from vault policy
    - flow_controller.py: Ensures one-directional flow and authorizes actions
    - proof_collector.py: Gathers proof trees from planner for audit

Principle: The flow is one-directional. The human initiates, agents execute.
"""

from .intent_parser import IntentParser
from .constraint_engine import ConstraintEngine
from .flow_controller import FlowController
from .proof_collector import ProofCollector

__all__ = ["IntentParser", "ConstraintEngine", "FlowController", "ProofCollector"]
