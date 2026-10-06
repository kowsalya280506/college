from typing import Optional, Dict, Any
from app.memory.data_manager import get_departments, get_staff


def find_department(complaint_text: str) -> str:
    """
    Route a complaint to the appropriate college department based on dynamic
    departments configuration or keyword rules.
    """
    text = complaint_text.lower()
    departments = get_departments()

    # Match against dynamic handles defined in departments.json
    for dept in departments:
        dept_name = dept.get("department", "")
        handles = dept.get("handles", [])
        for keyword in handles:
            if keyword.lower() in text:
                return dept_name

    # Fallback keyword matching for standard college departments
    if any(k in text for k in ["wifi", "wi-fi", "internet", "network", "router", "lan", "ethernet"]):
        return "Network Department"
    elif any(k in text for k in ["electricity", "power", "light", "fan", "switch", "generator"]):
        return "Maintenance Department"
    elif any(k in text for k in ["water", "tap", "pipe", "leak", "flush", "plumbing", "washroom"]):
        return "Maintenance Department"
    elif any(k in text for k in ["projector", "computer", "pc", "software", "printer", "lab"]):
        return "IT Support"
    elif any(k in text for k in ["food", "mess", "canteen", "lunch", "dinner", "breakfast"]):
        return "Food & Hostel Department"
    elif any(k in text for k in ["fee", "payment", "scholarship", "dues", "challan"]):
        return "Accounts Department"
    elif any(k in text for k in ["exam", "hall ticket", "marks", "grade", "attendance", "registration"]):
        return "Academic Office"

    return "General Administration"


def find_staff(department: str) -> Optional[Dict[str, Any]]:
    """
    Find an available staff member for the designated department.
    """
    staff_list = get_staff()
    
    # Priority: Find available staff member matching the department
    for staff in staff_list:
        if staff.get("department", "").lower() == department.lower() and staff.get("available", False):
            return staff

    # Secondary: If no one is available in department, return any matching staff or None
    for staff in staff_list:
        if staff.get("department", "").lower() == department.lower():
            return staff

    return None
