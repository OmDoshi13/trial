"""Mock vacation/leave service.

Simulates an external HR system API that returns employee leave data.
In production, this would call a real HR system (e.g., SAP, Workday).
"""

from datetime import date

# Simulated employee leave data (as if from an external database/API)
_LEAVE_DATA = {
    "EMP001": {
        "employee_name": "Manav Modi",
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
        "employee_name": "Anna Schmidt",
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


def get_vacation_days(employee_id: str = "EMP001") -> dict:
    """Retrieve vacation day information for an employee.

    Args:
        employee_id: The employee identifier (default: EMP001 for demo).

    Returns:
        Dictionary with vacation day details.
    """
    data = _LEAVE_DATA.get(employee_id)
    if not data:
        return {"error": f"Employee {employee_id} not found"}

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


def get_sick_leave(employee_id: str = "EMP001") -> dict:
    """Retrieve sick leave balance for an employee.

    Args:
        employee_id: The employee identifier.

    Returns:
        Dictionary with sick leave details.
    """
    data = _LEAVE_DATA.get(employee_id)
    if not data:
        return {"error": f"Employee {employee_id} not found"}

    return {
        "employee_id": employee_id,
        "employee_name": data["employee_name"],
        "year": data["year"],
        "sick_days_total": data["sick_days_total"],
        "sick_days_used": data["sick_days_used"],
        "sick_days_remaining": data["sick_days_remaining"],
        "as_of_date": str(date.today()),
    }


def get_upcoming_leave(employee_id: str = "EMP001") -> dict:
    """Retrieve upcoming scheduled leave for an employee.

    Args:
        employee_id: The employee identifier.

    Returns:
        Dictionary with upcoming leave entries.
    """
    data = _LEAVE_DATA.get(employee_id)
    if not data:
        return {"error": f"Employee {employee_id} not found"}

    return {
        "employee_id": employee_id,
        "employee_name": data["employee_name"],
        "upcoming_leave": data["upcoming_leave"],
        "as_of_date": str(date.today()),
    }
