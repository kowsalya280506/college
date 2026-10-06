from typing import Dict, Any, List
from app.services.routing import find_department, find_staff
from app.services.priority import calculate_priority
from app.services.escalation import escalate_complaint
from app.memory.data_manager import get_history, update_complaint


def tool_route_complaint(complaint: str) -> Dict[str, Any]:
    """Determine responsible department."""
    department = find_department(complaint)
    return {
        "status": "success",
        "department": department,
        "message": f"Routed to {department}"
    }


def tool_assign_staff(department: str) -> Dict[str, Any]:
    """Find available staff for the department."""
    staff = find_staff(department)
    if staff:
        return {
            "status": "success",
            "staff": staff,
            "message": f"Assigned staff: {staff.get('name')} ({staff.get('role')})"
        }
    return {
        "status": "not_found",
        "staff": None,
        "message": f"No currently active staff available for {department}. Ticket queued for next supervisor."
    }


def tool_assess_priority(complaint: str) -> Dict[str, Any]:
    """Assess urgency and priority."""
    priority, reason = calculate_priority(complaint)
    return {
        "status": "success",
        "priority": priority,
        "reason": reason
    }


def tool_search_history(keyword: str) -> Dict[str, Any]:
    """Search previous complaint resolutions for solutions."""
    history = get_history()
    k_lower = keyword.lower()
    matches = []

    for item in history:
        issue = item.get("issue", "").lower()
        cat = item.get("category", "").lower()
        if k_lower in issue or issue in k_lower or k_lower in cat:
            matches.append(item)

    return {
        "status": "success",
        "matches": matches,
        "count": len(matches)
    }


def tool_change_complaint_status(complaint_id: str, new_status: str) -> Dict[str, Any]:
    """Update complaint status."""
    updated = update_complaint(complaint_id, {"status": new_status})
    if updated:
        return {
            "status": "success",
            "complaint": updated,
            "message": f"Complaint {complaint_id} status updated to {new_status}."
        }
    return {
        "status": "error",
        "message": f"Complaint {complaint_id} not found."
    }


def tool_escalate_complaint(complaint_id: str, reason: str = "Urgent college activity impacted") -> Dict[str, Any]:
    """Escalate complaint."""
    updated = escalate_complaint(complaint_id, reason=reason)
    if updated:
        return {
            "status": "escalated",
            "complaint": updated,
            "message": f"Complaint {complaint_id} successfully escalated to Critical priority."
        }
    return {
        "status": "error",
        "message": f"Failed to escalate complaint {complaint_id}."
    }


# Map of tool names to callable functions
TOOL_REGISTRY = {
    "route_complaint": tool_route_complaint,
    "assign_staff": tool_assign_staff,
    "assess_priority": tool_assess_priority,
    "search_history": tool_search_history,
    "change_complaint_status": tool_change_complaint_status,
    "escalate_complaint": tool_escalate_complaint
}


def execute_agent_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute tool with given name and arguments safely."""
    func = TOOL_REGISTRY.get(tool_name)
    if not func:
        return {
            "status": "error",
            "message": f"Unknown tool: {tool_name}"
        }
    try:
        return func(**arguments)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error executing tool {tool_name}: {str(e)}"
        }
