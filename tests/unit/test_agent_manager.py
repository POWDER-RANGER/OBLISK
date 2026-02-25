"""Unit tests for agents.agent_manager — AgentManager class."""

from __future__ import annotations

import pytest

from agents.agent import Agent
from agents.agent_manager import AgentManager
from vault import Vault

TEST_KEY: bytes = b"oblisk-test-key!oblisk-test-key!"


@pytest.fixture
def vault() -> Vault:
    return Vault(key=TEST_KEY)


@pytest.fixture
def manager(vault: Vault) -> AgentManager:
    return AgentManager(vault=vault)


@pytest.fixture
def agent_a(vault: Vault) -> Agent:
    return Agent(name="alpha", vault=vault)


@pytest.fixture
def agent_b(vault: Vault) -> Agent:
    return Agent(name="beta", vault=vault)


class TestManagerInit:
    def test_empty_on_init(self, manager: AgentManager) -> None:
        agents = manager.list_agents()
        assert len(agents) == 0

    def test_vault_stored(self, manager: AgentManager, vault: Vault) -> None:
        assert manager.vault is vault


class TestRegisterUnregister:
    def test_register_adds_agent(self, manager: AgentManager, agent_a: Agent) -> None:
        manager.register_agent(agent_a)
        assert len(manager.list_agents()) == 1

    def test_register_two_agents(self, manager: AgentManager, agent_a: Agent, agent_b: Agent) -> None:
        manager.register_agent(agent_a)
        manager.register_agent(agent_b)
        assert len(manager.list_agents()) == 2

    def test_get_agent_by_id(self, manager: AgentManager, agent_a: Agent) -> None:
        manager.register_agent(agent_a)
        found = manager.get_agent(agent_a.agent_id)
        assert found is agent_a

    def test_get_nonexistent_returns_none(self, manager: AgentManager) -> None:
        assert manager.get_agent("nonexistent-id") is None

    def test_list_agents_returns_list(self, manager: AgentManager, agent_a: Agent) -> None:
        manager.register_agent(agent_a)
        agents = manager.list_agents()
        assert isinstance(agents, list)
        assert agent_a in agents


class TestManagerStats:
    def test_get_stats_keys(self, manager: AgentManager) -> None:
        stats = manager.get_stats()
        for key in ["total_agents", "running_agents", "idle_agents"]:
            assert key in stats

    def test_stats_total_count(self, manager: AgentManager, agent_a: Agent, agent_b: Agent) -> None:
        manager.register_agent(agent_a)
        manager.register_agent(agent_b)
        assert manager.get_stats()["total_agents"] == 2
