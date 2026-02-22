"""Payslip tool — fetch data from mock HR service over HTTP."""

import httpx
from src.config import settings


def get_payslip_info(employee_id: str = "EMP001") -> dict:
    """Fetch latest payslip details from mock HR service."""
    try:
        r = httpx.get(
            f"{settings.mock_hr_base_url}/api/payslip/{employee_id}",
            timeout=10.0,
        )
        if r.status_code == 404:
            return {"error": r.json().get("detail", "Not found")}
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        return {"error": "Mock HR service is not running"}
    except Exception as e:
        return {"error": f"HR service request failed: {e}"}
