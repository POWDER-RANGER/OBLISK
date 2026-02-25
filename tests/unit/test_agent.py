"""Unit tests for agents.agent — Agent class.

Covers:
- initialisation defaults
- start/stop/pause/resume lifecycle
- status transitions and idempotency
- execute_task returns correct shape
- get_status dict
- __repr__
"""

from __future__ import annotations

import pytest

from agents.agent import Agent, AgentStatus
from vault import Vault

TEST_KEY: bytes = b"oblisk-test-key!oblisk-test-key!"


@pytest.fixture
def vault() -> Vault:
    return Vault(key=TEST_KEY)


@pytest.fixture
def agent(vault: Vault) -> Agent:
    return Agent(name="unit-agent", vault=vault)


class TestAgentInit:
    def test_default_status_idle(self, agent: Agent) -> None:
        assert agent.status == AgentStatus.IDLE

    def test_name_stored(self, agent: Agent) -> None:
        assert agent.name == "unit-agent"

    def test_agent_id_generated(self, agent: Agent) -> None:
        assert agent.agent_id.startswith("agent-")

    def test_capabilities_default_empty(self, agent: Agent) -> None:
        assert agent.capabilities == []

    def test_capabilities_stored(self, vault: Vault) -> None:
        a = Agent(name="capable", capabilities=["research", "write"], vault=vault)
        assert "research" in a.capabilities

    def test_vault_reference(self, agent: Agent, vault: Vault) -> None:
        assert agent.vault is vault

    def test_task_history_empty(self, agent: Agent) -> None:
        assert agent._task_history == []


class TestAgentLifecycle:
    def test_start_returns_true(self, agent: Agent) -> None:
        assert agent.start() is True

    def test_start_changes_status_to_running(self, agent: Agent) -> None:
        agent.start()
        assert agent.status == AgentStatus.RUNNING

    def test_start_already_running_returns_false(self, agent: Agent) -> None:
        agent.start()
        assert agent.start() is False

    def test_stop_returns_true(self, agent: Agent) -> None:
        assert agent.stop() is True

    def test_stop_changes_status_to_stopped(self, agent: Agent) -> None:
        agent.stop()
        assert agent.status == AgentStatus.STOPPED

    def test_stop_already_stopped_returns_false(self, agent: Agent) -> None:
        agent.stop()
        assert agent.stop() is False

    def test_pause_requires_running(self, agent: Agent) -> None:
        assert agent.pause() is False  # not running yet

    def test_pause_from_running(self, agent: Agent) -> None:
        agent.start()
        assert agent.pause() is True
        assert agent.status == AgentStatus.PAUSED

    def test_resume_requires_paused(self, agent: Agent) -> None:
        agent.start()
        assert agent.resume() is False  # running, not paused

    def test_resume_from_paused(self, agent: Agent) -> None:
        agent.start()
        agent.pause()
        assert agent.resume() is True
        assert agent.status == AgentStatus.RUNNING


class TestAgentExecuteTask:
    def test_execute_returns_dict(self, agent: Agent) -> None:
        result = agent.execute_task({"id": "t1", "name": "test"})
        assert isinstance(result, dict)

    def test_execute_result_has_status(self, agent: Agent) -> None:
        result = agent.execute_task({"id": "t1", "name": "test"})
        assert result["status"] == "completed"

    def test_execute_result_has_agent_id(self, agent: Agent) -> None:
        result = agent.execute_task({"id": "t1", "name": "test"})
        assert result["agent_id"] == agent.agent_id

    def test_execute_appends_history(self, agent: Agent) -> None:
        agent.execute_task({"id": "t1", "name": "test"})
        agent.execute_task({"id": "t2", "name": "test2"})
        assert len(agent._task_history) == 2


class TestAgentGetStatus:
    def test_get_status_keys(self, agent: Agent) -> None:
        s = agent.get_status()
        for key in ["agent_id", "name", "status", "capabilities", "tasks_completed", "has_vault"]:
            assert key in s

    def test_has_vault_true(self, agent: Agent) -> None:
        assert agent.get_status()["has_vault"] is True

    def test_has_vault_false(self) -> None:
        a = Agent(name="no-vault")
        assert a.get_status()["has_vault"] is False


class TestAgentRepr:
    def test_repr_contains_name(self, agent: Agent) -> None:
        assert "unit-agent" in repr(agent)

    def test_repr_contains_status(self, agent: Agent) -> None:
        assert "idle" in repr(agent)
