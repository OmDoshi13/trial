"""Tests for mock tools."""

from src.tools.vacation import get_vacation_days, get_sick_leave, get_upcoming_leave
from src.tools.employee import get_employee_profile
from src.tools.payslip import get_payslip_info


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
    assert result["name"] == "Manav Modi"
    assert result["department"] == "Engineering"


def test_get_payslip_info():
    result = get_payslip_info("EMP001")
    assert result["gross_salary"] == 6500.00
    assert result["next_pay_date"] == "2026-02-28"


def test_get_upcoming_leave():
    result = get_upcoming_leave("EMP001")
    assert len(result["upcoming_leave"]) == 2
