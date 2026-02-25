"""Shared pytest fixtures for OBLISK test suite."""

from __future__ import annotations

import pytest

from vault import Vault, derive_key
from agents.agent import Agent, AgentStatus
from agents.agent_manager import AgentManager
from core.governance_engine import GovernanceEngine
from core.symbolic_planner import SymbolicPlanner

# Deterministic 32-byte test key — NEVER use in production
TEST_KEY: bytes = b"oblisk-test-key!oblisk-test-key!"  # exactly 32 bytes


@pytest.fixture
def vault() -> Vault:
    """Return a fresh in-memory Vault with the test key."""
    return Vault(key=TEST_KEY, name="test-vault")


@pytest.fixture
def agent(vault: Vault) -> Agent:
    """Return a fresh Agent wired to the test vault."""
    return Agent(name="test-agent", vault=vault)


@pytest.fixture
def agent_manager(vault: Vault) -> AgentManager:
    """Return a fresh AgentManager wired to the test vault."""
    return AgentManager(vault=vault)


@pytest.fixture
def governance(vault: Vault) -> GovernanceEngine:
    """Return a fresh GovernanceEngine wired to the test vault."""
    return GovernanceEngine(vault=vault)


@pytest.fixture
def planner() -> SymbolicPlanner:
    """Return a fresh SymbolicPlanner."""
    return SymbolicPlanner()
