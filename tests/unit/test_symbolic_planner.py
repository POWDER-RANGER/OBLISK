"""Unit tests for core.symbolic_planner — SymbolicPlanner class."""

from __future__ import annotations

import pytest

from core.symbolic_planner import SymbolicPlanner


@pytest.fixture
def planner() -> SymbolicPlanner:
    return SymbolicPlanner()


class TestPlannerInit:
    def test_planner_initialises(self, planner: SymbolicPlanner) -> None:
        assert planner is not None

    def test_initial_state_empty(self, planner: SymbolicPlanner) -> None:
        state = planner.get_state()
        assert isinstance(state, dict)


class TestPlanCreation:
    def test_create_plan_returns_list(self, planner: SymbolicPlanner) -> None:
        goal = {"target": "completed"}
        plan = planner.create_plan(goal)
        assert isinstance(plan, list)

    def test_create_plan_with_context(self, planner: SymbolicPlanner) -> None:
        goal = {"target": "analysed"}
        context = {"data": "input.csv"}
        plan = planner.create_plan(goal, context=context)
        assert isinstance(plan, list)


class TestActionRegistry:
    def test_get_available_actions(self, planner: SymbolicPlanner) -> None:
        actions = planner.get_available_actions()
        assert isinstance(actions, list)

    def test_get_plan_stats(self, planner: SymbolicPlanner) -> None:
        stats = planner.get_plan_stats()
        assert isinstance(stats, dict)
        assert "total_plans_created" in stats
