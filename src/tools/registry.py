"""Tool registry — maps tool names to functions and their schemas."""

import json
from src.tools.vacation import get_vacation_days, get_sick_leave, get_upcoming_leave
from src.tools.employee import get_employee_profile
from src.tools.payslip import get_payslip_info


# Each tool has a name, description, and parameter schema the LLM uses to decide what to call
TOOL_DEFINITIONS = [
    {
        "name": "get_vacation_days",
        "description": "Get the number of remaining vacation/holiday days for an employee. Use this when the user asks about vacation days, PTO, holidays, time off balance, or annual leave.",
        "parameters": {
            "employee_id": {
                "type": "string",
                "description": "Employee ID. Defaults to EMP001.",
                "default": "EMP001",
            }
        },
    },
    {
        "name": "get_sick_leave",
        "description": "Get sick leave balance and usage for an employee. Use this when the user asks about sick days, sick leave, or illness-related absence.",
        "parameters": {
            "employee_id": {
                "type": "string",
                "description": "Employee ID. Defaults to EMP001.",
                "default": "EMP001",
            }
        },
    },
    {
        "name": "get_upcoming_leave",
        "description": "Get upcoming scheduled leave/time-off for an employee. Use this when the user asks about planned vacations, scheduled time off, or upcoming leave.",
        "parameters": {
            "employee_id": {
                "type": "string",
                "description": "Employee ID. Defaults to EMP001.",
                "default": "EMP001",
            }
        },
    },
    {
        "name": "get_employee_profile",
        "description": "Get employee profile information like name, department, position, manager, start date. Use this when the user asks about their profile, who their manager is, what team they are on, employee details.",
        "parameters": {
            "employee_id": {
                "type": "string",
                "description": "Employee ID. Defaults to EMP001.",
                "default": "EMP001",
            }
        },
    },
    {
        "name": "get_payslip_info",
        "description": "Get payslip/salary information including gross salary, net salary, deductions, next pay date. Use this when the user asks about salary, pay, payslip, deductions, or when they get paid.",
        "parameters": {
            "employee_id": {
                "type": "string",
                "description": "Employee ID. Defaults to EMP001.",
                "default": "EMP001",
            }
        },
    },
    {
        "name": "search_documents",
        "description": "Search the company knowledge base (policies, FAQ, onboarding guide, benefits) for information. Use this when the user asks about company policies, work arrangements, benefits, onboarding, data protection, expense policy, performance reviews, or any general company information.",
        "parameters": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant information in company documents.",
            }
        },
    },
]

# Name → callable mapping
TOOL_FUNCTIONS = {
    "get_vacation_days": get_vacation_days,
    "get_sick_leave": get_sick_leave,
    "get_upcoming_leave": get_upcoming_leave,
    "get_employee_profile": get_employee_profile,
    "get_payslip_info": get_payslip_info,
    # search_documents is handled specially by the orchestrator
}


def execute_tool(tool_name: str, arguments: dict) -> str:
    """Look up a tool by name, call it, return JSON result."""
    func = TOOL_FUNCTIONS.get(tool_name)
    if not func:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    try:
        result = func(**arguments)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})


def get_tools_description() -> str:
    """Format tool definitions as text for the system prompt."""
    lines = ["Available tools:\n"]
    for tool in TOOL_DEFINITIONS:
        params = ", ".join(
            f'{k}: {v["type"]}' for k, v in tool["parameters"].items()
        )
        lines.append(f"- **{tool['name']}**({params}): {tool['description']}")
    return "\n".join(lines)
