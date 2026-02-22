"""Tests for tool registry."""

import json
import httpx
import pytest
from src.tools.registry import execute_tool, get_tools_description
from src.tools.mock_hr_service import mock_app


@pytest.fixture(autouse=True)
def _mock_httpx_get(monkeypatch):
    """Route httpx.get through the mock HR app in-process."""
    from starlette.testclient import TestClient
    client = TestClient(mock_app)

    def fake_get(url: str, **kwargs):
        from urllib.parse import urlparse
        path = urlparse(url).path
        resp = client.get(path)
        return httpx.Response(
            status_code=resp.status_code,
            json=resp.json(),
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)


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
