import os
import base64
import uuid
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.agent.core import ComplaintAgent
from app.config import UPLOADS_DIR, STUDENT_USERNAME, STUDENT_PASSWORD
from app.memory.data_manager import (
    get_complaints,
    get_complaint_by_id,
    update_complaint,
    mark_complaint_seen,
    get_departments,
    get_staff,
    get_history,
    get_incidents,
    get_notifications,
    mark_notification_read,
    get_stats,
    get_dashboard_analytics
)
from app.services.escalation import escalate_complaint, run_sla_escalation_sweep
from app.services.notification import notify_complaint_resolved

router = APIRouter(prefix="/api")
agent = ComplaintAgent()


# ==========================================
# PYDANTIC SCHEMAS
# ==========================================

class StudentLoginRequest(BaseModel):
    username: str = Field(..., description="Student username")
    password: str = Field(..., description="Student password")


class ImageUploadRequest(BaseModel):
    image_data: str = Field(..., description="Base64 data URI or raw base64 string")
    filename: Optional[str] = Field("photo.jpg", description="Original or preferred filename")


class ComplaintSubmission(BaseModel):
    student: str = Field(..., description="Student name or ID", min_length=1)
    location: str = Field(..., description="Location of issue", min_length=1)
    complaint: str = Field(..., description="Description of the issue", min_length=3)
    category: Optional[str] = Field(None, description="Optional manual category")
    photo_url: Optional[str] = Field(None, description="Optional uploaded photo URL")
    photo_data: Optional[str] = Field(None, description="Optional base64 image data")


class StatusUpdateRequest(BaseModel):
    status: str = Field(..., description="New status (e.g. Action Started, In Progress, Resolved, Escalated, Pending, Seen)")
    resolution_notes: Optional[str] = Field(None, description="Optional notes on resolution")


class SeenRequest(BaseModel):
    role: str = Field("department", description="Role viewing the ticket: 'department' or 'management'")


class EscalateRequest(BaseModel):
    reason: Optional[str] = Field("Manual escalation by Administrator", description="Reason for escalation")


class SLACheckRequest(BaseModel):
    hours_threshold: Optional[int] = Field(24, description="SLA hours threshold")


def _save_base64_image(image_data: str, filename: Optional[str] = None) -> str:
    """Safely decode base64 image data and save to UPLOADS_DIR, returning URL path."""
    if not image_data or not image_data.strip():
        return ""
    image_str = image_data.strip()
    ext = ".jpg"
    if "," in image_str:
        header, encoded = image_str.split(",", 1)
        if "png" in header.lower():
            ext = ".png"
        elif "webp" in header.lower():
            ext = ".webp"
        elif "gif" in header.lower():
            ext = ".gif"
    else:
        encoded = image_str

    if filename:
        f_ext = os.path.splitext(filename)[1].lower()
        if f_ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
            ext = f_ext

    raw_bytes = base64.b64decode(encoded)
    unique_filename = f"cmp_{uuid.uuid4().hex[:12]}{ext}"
    target_path = UPLOADS_DIR / unique_filename
    with open(target_path, "wb") as f:
        f.write(raw_bytes)
    return f"/uploads/{unique_filename}"


# ==========================================
# AUTHENTICATION & PHOTO UPLOAD
# ==========================================

@router.post("/auth/student-login")
def student_login(data: StudentLoginRequest):
    """Authenticate student with VCET26 / velalar credentials."""
    uname = (data.username or "").strip()
    pwd = (data.password or "").strip()

    if uname == STUDENT_USERNAME and pwd == STUDENT_PASSWORD:
        return {
            "success": True,
            "student": {
                "username": STUDENT_USERNAME,
                "name": "VCET Student (VCET26)",
                "roll_number": STUDENT_USERNAME,
                "college": "Velalar College of Engineering and Technology",
                "role": "student"
            },
            "token": f"stu-token-{uuid.uuid4().hex[:12]}"
        }
    raise HTTPException(
        status_code=401,
        detail="Invalid student credentials. Please use username 'VCET26' and password 'velalar'."
    )


@router.post("/upload")
def upload_complaint_photo(data: ImageUploadRequest):
    """Upload an optional photo attached to a complaint via base64 data."""
    try:
        url = _save_base64_image(data.image_data, data.filename)
        return {
            "success": True,
            "photo_url": url,
            "filename": os.path.basename(url)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")


# ==========================================
# COMPLAINT ENDPOINTS
# ==========================================

@router.post("/complaints")
def submit_complaint(data: ComplaintSubmission):
    """
    Ingest a student complaint and execute the full Agentic AI processing pipeline.
    Photo upload is completely optional.
    """
    try:
        photo_url = data.photo_url
        if not photo_url and data.photo_data:
            try:
                photo_url = _save_base64_image(data.photo_data)
            except Exception:
                pass

        result = agent.process_complaint(
            student=data.student,
            location=data.location,
            complaint_text=data.complaint,
            category=data.category,
            photo_url=photo_url
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")


@router.get("/complaints")
def list_complaints(
    status: Optional[str] = Query(None, description="Filter by status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    student_id: Optional[str] = Query(None, description="Filter by student ID / username"),
    search: Optional[str] = Query(None, description="Search query")
):
    """List complaints with multi-criteria filtering across student, department, status, priority, and search."""
    complaints = get_complaints()

    if student_id and student_id.lower() != "all":
        s_id = student_id.lower()
        complaints = [
            c for c in complaints
            if s_id in (c.get("student") or "").lower()
            or s_id in (c.get("student_id") or "").lower()
        ]

    if status and status.lower() != "all":
        complaints = [c for c in complaints if c.get("status", "").lower() == status.lower()]

    if department and department.lower() != "all":
        d_lower = department.lower()
        complaints = [
            c for c in complaints
            if d_lower in (c.get("department") or "").lower()
            or (c.get("department") or "").lower() in d_lower
        ]

    if priority and priority.lower() != "all":
        complaints = [c for c in complaints if c.get("priority", "").lower() == priority.lower()]

    if search:
        s = search.lower()
        complaints = [
            c for c in complaints
            if s in c.get("complaint", "").lower()
            or s in c.get("student", "").lower()
            or s in c.get("location", "").lower()
            or s in c.get("id", "").lower()
            or s in (c.get("department") or "").lower()
        ]

    # Return newest complaints first
    complaints.reverse()
    return {"success": True, "count": len(complaints), "complaints": complaints}


@router.get("/complaints/{complaint_id}")
def get_complaint(complaint_id: str):
    """Get single complaint by ID with full timeline."""
    complaint = get_complaint_by_id(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {"success": True, "complaint": complaint}


@router.post("/complaints/{complaint_id}/seen")
def record_complaint_seen(complaint_id: str, body: SeenRequest):
    """Record department or management viewed timestamp."""
    updated = mark_complaint_seen(complaint_id, body.role)
    if not updated:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {"success": True, "complaint": updated}


@router.patch("/complaints/{complaint_id}/status")
def update_status(complaint_id: str, body: StatusUpdateRequest):
    """Update complaint status and update timeline timestamps."""
    updates = {"status": body.status}
    if body.resolution_notes:
        updates["resolution_notes"] = body.resolution_notes

    updated = update_complaint(complaint_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # If resolved, notify student
    if body.status.lower() == "resolved":
        student = updated.get("student") or updated.get("student_id") or "Student"
        notify_complaint_resolved(student, complaint_id, body.resolution_notes or "Marked resolved by Admin")

    return {"success": True, "complaint": updated}


@router.post("/complaints/{complaint_id}/escalate")
def escalate(complaint_id: str, body: EscalateRequest):
    """Manually escalate a complaint."""
    updated = escalate_complaint(complaint_id, reason=body.reason or "Manual escalation")
    if not updated:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {"success": True, "complaint": updated}


# ==========================================
# INCIDENTS, NOTIFICATIONS & STATS
# ==========================================

@router.get("/incidents")
def list_incidents():
    """List all incident clusters."""
    incidents = get_incidents()
    return {"success": True, "count": len(incidents), "incidents": incidents}


@router.get("/notifications")
def list_notifications(student_id: Optional[str] = Query(None)):
    """List notifications."""
    notifs = get_notifications(student_id)
    notifs.reverse()
    return {"success": True, "count": len(notifs), "notifications": notifs}


@router.patch("/notifications/{notif_id}/read")
def read_notification(notif_id: str):
    """Mark a notification as read."""
    n = mark_notification_read(notif_id)
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True, "notification": n}


@router.get("/stats")
def get_dashboard_stats():
    """Get system summary statistics."""
    stats = get_stats()
    return {"success": True, "stats": stats}


@router.get("/stats/dashboard")
def get_detailed_dashboard_analytics():
    """Get dynamic analytics with date-wise, time-wise, department-wise, and resolution stats."""
    analytics = get_dashboard_analytics()
    return {"success": True, "analytics": analytics}


@router.get("/departments")
def list_departments():
    """List all departments."""
    return {"success": True, "departments": get_departments()}


@router.get("/staff")
def list_staff():
    """List all staff members."""
    return {"success": True, "staff": get_staff()}


@router.get("/history")
def list_history():
    """List historical resolved complaints."""
    return {"success": True, "history": get_history()}


@router.post("/escalation/run-check")
def run_escalation_check(body: SLACheckRequest):
    """Run automated SLA check across all complaints."""
    escalated = run_sla_escalation_sweep(hours_threshold=body.hours_threshold or 24)
    return {
        "success": True,
        "escalated_count": len(escalated),
        "escalated_complaints": escalated
    }
