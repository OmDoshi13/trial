"""Mock employee profile service.

Simulates an external employee directory / HR system.
"""

_EMPLOYEES = {
    "EMP001": {
        "employee_id": "EMP001",
        "name": "Manav Modi",
        "email": "manav.modi@trenkwalder.com",
        "department": "Engineering",
        "position": "Senior Full-Stack Developer",
        "manager": "Thomas Berger",
        "location": "Remote (Vienna, AT)",
        "start_date": "2025-06-01",
        "employment_type": "Full-time",
        "team": "Platform Engineering",
    },
    "EMP002": {
        "employee_id": "EMP002",
        "name": "Anna Schmidt",
        "email": "anna.schmidt@trenkwalder.com",
        "department": "Engineering",
        "position": "Backend Developer",
        "manager": "Thomas Berger",
        "location": "Munich, DE",
        "start_date": "2024-01-15",
        "employment_type": "Full-time",
        "team": "Platform Engineering",
    },
}


def get_employee_profile(employee_id: str = "EMP001") -> dict:
    """Retrieve employee profile information.

    Args:
        employee_id: The employee identifier.

    Returns:
        Dictionary with employee profile data.
    """
    profile = _EMPLOYEES.get(employee_id)
    if not profile:
        return {"error": f"Employee {employee_id} not found"}
    return profile
