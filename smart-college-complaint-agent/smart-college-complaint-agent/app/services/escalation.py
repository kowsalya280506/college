from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.config import SLA_PENDING_HOURS
from app.memory.data_manager import get_complaints, update_complaint, add_notification


def check_pending_complaints(complaints: List[Dict[str, Any]], hours_threshold: int = SLA_PENDING_HOURS) -> List[Dict[str, Any]]:
    """
    Find complaints that have been in 'Pending' or unassigned status longer than the SLA threshold.
    """
    now = datetime.now()
    overdue = []

    for complaint in complaints:
        if complaint.get("status") not in ["Pending", "Assigned"]:
            continue

        created_at_str = complaint.get("created_at")
        if not created_at_str:
            continue

        try:
            created_time = datetime.fromisoformat(created_at_str)
            if now - created_time > timedelta(hours=hours_threshold):
                overdue.append(complaint)
        except ValueError:
            continue

    return overdue


def escalate_complaint(complaint_id: str, reason: str = "Urgent attention required / SLA breach") -> Optional[Dict[str, Any]]:
    """
    Escalate a complaint to Critical priority and Escalated status.
    Dispatches a notification to the student automatically.
    """
    updated = update_complaint(
        complaint_id,
        {
            "status": "Escalated",
            "priority": "Critical",
            "escalated": True,
            "escalation_reason": reason,
            "escalated_at": datetime.now().isoformat()
        }
    )

    if updated:
        student = updated.get("student") or updated.get("student_id") or "Student"
        add_notification(
            student_id=student,
            message=f"Complaint {complaint_id} has been escalated to Critical status. Reason: {reason}"
        )

    return updated


def run_sla_escalation_sweep(hours_threshold: int = SLA_PENDING_HOURS) -> List[Dict[str, Any]]:
    """
    Scan all complaints and escalate any that have exceeded the resolution time threshold.
    """
    all_complaints = get_complaints()
    overdue = check_pending_complaints(all_complaints, hours_threshold=hours_threshold)
    escalated_records = []

    for comp in overdue:
        cid = comp.get("id")
        if cid:
            result = escalate_complaint(cid, reason=f"Automatic SLA Escalation: Pending for > {hours_threshold}h")
            if result:
                escalated_records.append(result)

    return escalated_records
