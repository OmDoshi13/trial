"""Tests for tool registry."""

import json
from src.tools.registry import execute_tool, get_tools_description


def test_execute_known_tool():
    result = execute_tool("get_vacation_days", {"employee_id": "EMP001"})
    data = json.loads(result)
    assert data["remaining_vacation_days"] == 12


def test_execute_unknown_tool():
    result = execute_tool("nonexistent_tool", {})
    data = json.loads(result)
    assert "error" in data


def test_tools_description():
    desc = get_tools_description()
    assert "get_vacation_days" in desc
    assert "search_documents" in desc
