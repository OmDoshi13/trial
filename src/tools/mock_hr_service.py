"""Mock external HR REST API.

Runs as a background FastAPI app on port 8001. The tool functions in
vacation.py, employee.py, and payslip.py call this over HTTP — just
like they would with a real SAP/Workday endpoint in production.
"""

from datetime import date
from fastapi import FastAPI, HTTPException

mock_app = FastAPI(title="Mock HR Service")

# ── Vacation / leave data ──

_LEAVE_DATA = {
    "EMP001": {
        "employee_name": "Om Doshi",
        "total_vacation_days": 25,
        "used_vacation_days": 13,
        "remaining_vacation_days": 12,
        "carried_over_days": 3,
        "sick_days_total": 30,
        "sick_days_used": 4,
        "sick_days_remaining": 26,
        "upcoming_leave": [
            {"start": "2026-03-15", "end": "2026-03-19", "type": "vacation", "status": "approved"},
            {"start": "2026-04-10", "end": "2026-04-10", "type": "personal", "status": "pending"},
        ],
        "year": 2026,
    },
    "EMP002": {
        "employee_name": "Klahm Sebestian",
        "total_vacation_days": 25,
        "used_vacation_days": 8,
        "remaining_vacation_days": 17,
        "carried_over_days": 5,
        "sick_days_total": 30,
        "sick_days_used": 2,
        "sick_days_remaining": 28,
        "upcoming_leave": [],
        "year": 2026,
    },
}


def _get_leave(employee_id: str) -> dict:
    data = _LEAVE_DATA.get(employee_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    return data


@mock_app.get("/api/vacation/{employee_id}")
def vacation(employee_id: str):
    data = _get_leave(employee_id)
    return {
        "employee_id": employee_id,
        "employee_name": data["employee_name"],
        "year": data["year"],
        "total_vacation_days": data["total_vacation_days"],
        "used_vacation_days": data["used_vacation_days"],
        "remaining_vacation_days": data["remaining_vacation_days"],
        "carried_over_days": data["carried_over_days"],
        "as_of_date": str(date.today()),
    }


@mock_app.get("/api/sick-leave/{employee_id}")
def sick_leave(employee_id: str):
    data = _get_leave(employee_id)
    return {
        "employee_id": employee_id,
        "employee_name": data["employee_name"],
        "year": data["year"],
        "sick_days_total": data["sick_days_total"],
        "sick_days_used": data["sick_days_used"],
        "sick_days_remaining": data["sick_days_remaining"],
        "as_of_date": str(date.today()),
    }


@mock_app.get("/api/upcoming-leave/{employee_id}")
def upcoming_leave(employee_id: str):
    data = _get_leave(employee_id)
    return {
        "employee_id": employee_id,
        "employee_name": data["employee_name"],
        "upcoming_leave": data["upcoming_leave"],
        "as_of_date": str(date.today()),
    }


# ── Employee profiles ──

_EMPLOYEES = {
    "EMP001": {
        "employee_id": "EMP001",
        "name": "Om Doshi",
        "email": "omdoshi2@trenkwalder.com",
        "department": "Engineering",
        "position": "Senior Full-Stack Developer",
        "manager": "Thomas Berger",
        "location": "Remote (Ireland)",
        "start_date": "2025-06-01",
        "employment_type": "Full-time",
        "team": "Platform Engineering",
    },
    "EMP002": {
        "employee_id": "EMP002",
        "name": "Klahm Sebestian",
        "email": "klahm.sebestian@trenkwalder.com",
        "department": "Engineering",
        "position": "Backend Developer",
        "manager": "Thomas Berger",
        "location": "Munich, DE",
        "start_date": "2024-01-15",
        "employment_type": "Full-time",
        "team": "Platform Engineering",
    },
}


@mock_app.get("/api/employee/{employee_id}")
def employee_profile(employee_id: str):
    profile = _EMPLOYEES.get(employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    return profile


# ── Payslip data ──

_PAYSLIP_DATA = {
    "EMP001": {
        "employee_name": "Om Doshi",
        "gross_salary": 6500.00,
        "net_salary": 4200.00,
        "currency": "EUR",
        "pay_frequency": "monthly",
        "last_pay_date": "2026-01-31",
        "next_pay_date": "2026-02-28",
        "deductions": {
            "income_tax": 1450.00,
            "social_security": 650.00,
            "pension_contribution": 195.00,
            "health_insurance": 5.00,
        },
        "ytd_gross": 6500.00,
        "ytd_net": 4200.00,
    },
    "EMP002": {
        "employee_name": "Klahm Sebestian",
        "gross_salary": 5500.00,
        "net_salary": 3600.00,
        "currency": "EUR",
        "pay_frequency": "monthly",
        "last_pay_date": "2026-01-31",
        "next_pay_date": "2026-02-28",
        "deductions": {
            "income_tax": 1200.00,
            "social_security": 550.00,
            "pension_contribution": 165.00,
            "health_insurance": 5.00,
        },
        "ytd_gross": 5500.00,
        "ytd_net": 3600.00,
    },
}


@mock_app.get("/api/payslip/{employee_id}")
def payslip(employee_id: str):
    data = _PAYSLIP_DATA.get(employee_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    return {
        "employee_id": employee_id,
        "employee_name": data["employee_name"],
        "gross_salary": data["gross_salary"],
        "net_salary": data["net_salary"],
        "currency": data["currency"],
        "pay_frequency": data["pay_frequency"],
        "last_pay_date": data["last_pay_date"],
        "next_pay_date": data["next_pay_date"],
        "deductions": data["deductions"],
        "as_of_date": str(date.today()),
    }


@mock_app.get("/api/health")
def health():
    return {"status": "healthy", "service": "mock-hr-api"}
