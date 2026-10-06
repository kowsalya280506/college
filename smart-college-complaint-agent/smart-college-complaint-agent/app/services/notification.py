from typing import List, Dict, Any, Optional
from app.memory.data_manager import add_notification, get_notifications, mark_notification_read


def notify_complaint_registered(student: str, complaint_id: str, department: str, priority: str) -> Dict[str, Any]:
    """Notify student that their complaint was logged and processed by AI."""
    msg = f"Complaint {complaint_id} received. AI classified as [{priority}] priority and assigned to {department}."
    return add_notification(student, msg)


def notify_complaint_assigned(student: str, complaint_id: str, staff_name: str, department: str) -> Dict[str, Any]:
    """Notify student that a specific staff member was assigned."""
    msg = f"Complaint {complaint_id} has been assigned to staff member {staff_name} ({department})."
    return add_notification(student, msg)


def notify_complaint_resolved(student: str, complaint_id: str, resolution_notes: str = "Resolved") -> Dict[str, Any]:
    """Notify student when issue is marked resolved."""
    msg = f"Complaint {complaint_id} has been marked RESOLVED. Notes: {resolution_notes}"
    return add_notification(student, msg)


def notify_complaint_escalated(student: str, complaint_id: str, reason: str) -> Dict[str, Any]:
    """Notify student when ticket is escalated to leadership."""
    msg = f"URGENT: Complaint {complaint_id} escalated to Critical priority. Reason: {reason}"
    return add_notification(student, msg)
