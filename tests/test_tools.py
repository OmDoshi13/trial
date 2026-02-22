"""Tests for HR tools — uses a real in-process mock HR service via httpx."""

import pytest
import httpx
from unittest.mock import patch

from src.tools.vacation import get_vacation_days, get_sick_leave, get_upcoming_leave
from src.tools.employee import get_employee_profile
from src.tools.payslip import get_payslip_info
from src.tools.mock_hr_service import mock_app


@pytest.fixture(autouse=True)
def _mock_httpx_get(monkeypatch):
    """Route all httpx.get calls through the mock FastAPI app directly."""
    from starlette.testclient import TestClient
    client = TestClient(mock_app)

    original_get = httpx.get

    def fake_get(url: str, **kwargs):
        # Extract the path from the full URL (e.g., http://localhost:8001/api/vacation/EMP001)
        from urllib.parse import urlparse
        path = urlparse(url).path
        resp = client.get(path)
        # Return an httpx.Response-compatible object
        return httpx.Response(
            status_code=resp.status_code,
            json=resp.json(),
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)


def test_get_vacation_days():
    result = get_vacation_days("EMP001")
    assert result["remaining_vacation_days"] == 12
    assert result["total_vacation_days"] == 25
    assert "error" not in result


def test_get_vacation_days_unknown_employee():
    result = get_vacation_days("UNKNOWN")
    assert "error" in result


def test_get_sick_leave():
    result = get_sick_leave("EMP001")
    assert result["sick_days_remaining"] == 26
    assert "error" not in result


def test_get_employee_profile():
    result = get_employee_profile("EMP001")
    assert result["name"] == "Om Doshi"
    assert result["department"] == "Engineering"


def test_get_employee_profile_unknown():
    result = get_employee_profile("UNKNOWN")
    assert "error" in result


def test_get_payslip_info():
    result = get_payslip_info("EMP001")
    assert result["gross_salary"] == 6500.00
    assert result["next_pay_date"] == "2026-02-28"


def test_get_payslip_info_unknown():
    result = get_payslip_info("UNKNOWN")
    assert "error" in result


def test_get_upcoming_leave():
    result = get_upcoming_leave("EMP001")
    assert len(result["upcoming_leave"]) == 2


def test_get_upcoming_leave_emp002():
    result = get_upcoming_leave("EMP002")
    assert result["upcoming_leave"] == []
    assert "error" not in result
