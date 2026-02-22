"""Vacation/leave tools — fetch data from mock HR service over HTTP."""

import httpx
from src.config import settings


def _get(endpoint: str) -> dict:
    """GET from mock HR service, return JSON or error dict."""
    try:
        r = httpx.get(f"{settings.mock_hr_base_url}{endpoint}", timeout=10.0)
        if r.status_code == 404:
            return {"error": r.json().get("detail", "Not found")}
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        return {"error": "Mock HR service is not running"}
    except Exception as e:
        return {"error": f"HR service request failed: {e}"}


def get_vacation_days(employee_id: str = "EMP001") -> dict:
    """Fetch vacation day balance from mock HR service."""
    return _get(f"/api/vacation/{employee_id}")


def get_sick_leave(employee_id: str = "EMP001") -> dict:
    """Fetch sick leave balance from mock HR service."""
    return _get(f"/api/sick-leave/{employee_id}")


def get_upcoming_leave(employee_id: str = "EMP001") -> dict:
    """Fetch upcoming scheduled leave from mock HR service."""
    return _get(f"/api/upcoming-leave/{employee_id}")
