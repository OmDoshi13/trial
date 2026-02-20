"""Mock payslip service.

Simulates an external payroll system.
"""

from datetime import date, timedelta


_PAYSLIP_DATA = {
    "EMP001": {
        "employee_name": "Manav Modi",
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
        "employee_name": "Anna Schmidt",
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


def get_payslip_info(employee_id: str = "EMP001") -> dict:
    """Retrieve latest payslip information for an employee.

    Args:
        employee_id: The employee identifier.

    Returns:
        Dictionary with payslip details.
    """
    data = _PAYSLIP_DATA.get(employee_id)
    if not data:
        return {"error": f"Employee {employee_id} not found"}

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
