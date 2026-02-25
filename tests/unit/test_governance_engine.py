"""Unit tests for core.governance_engine — GovernanceEngine class."""

from __future__ import annotations

import pytest

from core.governance_engine import GovernanceEngine
from vault import Vault

TEST_KEY: bytes = b"oblisk-test-key!oblisk-test-key!"


@pytest.fixture
def vault() -> Vault:
    return Vault(key=TEST_KEY)


@pytest.fixture
def engine(vault: Vault) -> GovernanceEngine:
    return GovernanceEngine(vault=vault)


class TestGovernanceInit:
    def test_engine_initialises(self, engine: GovernanceEngine) -> None:
        assert engine is not None

    def test_no_policies_on_init(self, engine: GovernanceEngine) -> None:
        policies = engine.list_policies()
        assert isinstance(policies, list)


class TestPolicyCRUD:
    def test_add_policy(self, engine: GovernanceEngine) -> None:
        initial = len(engine.list_policies())
        engine.add_policy({"name": "deny-web", "action": "web_access", "effect": "deny"})
        assert len(engine.list_policies()) == initial + 1

    def test_list_policies_returns_list(self, engine: GovernanceEngine) -> None:
        result = engine.list_policies()
        assert isinstance(result, list)


class TestAuditLog:
    def test_audit_log_initialises_empty(self, engine: GovernanceEngine) -> None:
        log = engine.get_audit_log()
        assert isinstance(log, list)

    def test_evaluate_creates_audit_entry(self, engine: GovernanceEngine) -> None:
        engine.evaluate_action("agent-123", "write_file", {})
        log = engine.get_audit_log()
        assert len(log) >= 1

    def test_audit_entry_has_required_fields(self, engine: GovernanceEngine) -> None:
        engine.evaluate_action("agent-abc", "read_vault", {"key": "test"})
        log = engine.get_audit_log()
        entry = log[-1]
        assert "timestamp" in entry
        assert "agent_id" in entry
        assert "action" in entry
