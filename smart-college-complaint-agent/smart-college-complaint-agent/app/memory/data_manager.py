import json
import os
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.config import (
    COMPLAINTS_FILE,
    DEPARTMENTS_FILE,
    STAFF_FILE,
    HISTORY_FILE,
    INCIDENTS_FILE,
    NOTIFICATIONS_FILE,
    DATA_DIR
)

# Global thread lock for file I/O safety
_file_lock = threading.Lock()


def _ensure_file_exists(file_path, default_data):
    """Ensure JSON file exists with valid default data."""
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4)


def load_json(file_path, default=None) -> Any:
    """Safely load JSON data from a file."""
    if default is None:
        default = []
    _ensure_file_exists(file_path, default)
    with _file_lock:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            return default


def save_json(file_path, data: Any) -> bool:
    """Safely write JSON data to a file."""
    with _file_lock:
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            return True
        except OSError:
            return False


# ==========================================
# COMPLAINTS MANAGEMENT
# ==========================================

def format_duration(seconds: float) -> str:
    """Format duration in seconds into a friendly human-readable string."""
    if seconds is None:
        return "N/A"
    seconds = int(max(0, seconds))
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    rem_seconds = seconds % 60
    if minutes < 60:
        return f"{minutes}m {rem_seconds}s" if rem_seconds else f"{minutes}m"
    hours = minutes // 60
    rem_minutes = minutes % 60
    if hours < 24:
        return f"{hours}h {rem_minutes}m"
    days = hours // 24
    rem_hours = hours % 24
    return f"{days}d {rem_hours}h"


def _normalize_complaint(c: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure complaint has complete timeline, photo_url, and duration metrics."""
    if not isinstance(c, dict):
        return c

    if "photo_url" not in c:
        c["photo_url"] = None

    created_iso = c.get("created_at") or datetime.now().isoformat()
    if "created_at" not in c:
        c["created_at"] = created_iso

    timeline = c.get("timeline")
    if not isinstance(timeline, dict):
        timeline = {}

    if "submitted_at" not in timeline or not timeline["submitted_at"]:
        timeline["submitted_at"] = created_iso
    if "department_seen_at" not in timeline:
        timeline["department_seen_at"] = None
    if "management_seen_at" not in timeline:
        timeline["management_seen_at"] = None
    if "action_started_at" not in timeline:
        timeline["action_started_at"] = None

    # Handle resolution and duration
    status = (c.get("status") or "Pending").strip()
    if "resolved_at" not in timeline:
        timeline["resolved_at"] = c.get("updated_at") if status.lower() == "resolved" else None

    # Calculate duration if resolved
    duration_sec = timeline.get("resolution_duration_seconds")
    if timeline.get("resolved_at") and duration_sec is None:
        try:
            dt_sub = datetime.fromisoformat(timeline["submitted_at"])
            dt_res = datetime.fromisoformat(timeline["resolved_at"])
            duration_sec = max(0, (dt_res - dt_sub).total_seconds())
        except Exception:
            duration_sec = None

    timeline["resolution_duration_seconds"] = duration_sec
    timeline["resolution_duration_formatted"] = format_duration(duration_sec) if duration_sec is not None else None
    c["timeline"] = timeline
    return c


# ==========================================
# COMPLAINTS MANAGEMENT
# ==========================================

def get_complaints() -> List[Dict[str, Any]]:
    """Retrieve all complaints with normalized timelines."""
    raw = load_json(COMPLAINTS_FILE, default=[])
    return [_normalize_complaint(c) for c in raw]


def get_complaint_by_id(complaint_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single complaint by its unique ID."""
    complaints = get_complaints()
    for c in complaints:
        if c.get("id") == complaint_id:
            return c
    return None


def add_complaint(complaint: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new complaint with auto-generated ID if missing and initial timeline."""
    complaints = load_json(COMPLAINTS_FILE, default=[])
    now_iso = datetime.now().isoformat()

    if "id" not in complaint or not complaint["id"]:
        next_num = len(complaints) + 1
        complaint["id"] = f"CMP{next_num:03d}"
    if "created_at" not in complaint:
        complaint["created_at"] = now_iso
    if "status" not in complaint:
        complaint["status"] = "Submitted"
    if "photo_url" not in complaint:
        complaint["photo_url"] = None

    if "timeline" not in complaint or not isinstance(complaint["timeline"], dict):
        complaint["timeline"] = {
            "submitted_at": complaint["created_at"],
            "department_seen_at": None,
            "management_seen_at": None,
            "action_started_at": None,
            "resolved_at": None,
            "resolution_duration_seconds": None,
            "resolution_duration_formatted": None
        }

    _normalize_complaint(complaint)
    complaints.append(complaint)
    save_json(COMPLAINTS_FILE, complaints)
    return complaint


def update_complaint(complaint_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update fields of an existing complaint and sync timeline."""
    complaints = load_json(COMPLAINTS_FILE, default=[])
    now_iso = datetime.now().isoformat()

    for complaint in complaints:
        if complaint.get("id") == complaint_id:
            _normalize_complaint(complaint)
            timeline = complaint["timeline"]

            # Check status transitions for timeline hooks
            new_status = updates.get("status")
            if new_status:
                norm_new_status = new_status.strip().title()
                if norm_new_status in ["Action Started", "In Progress"] and not timeline.get("action_started_at"):
                    timeline["action_started_at"] = now_iso
                elif norm_new_status == "Resolved":
                    timeline["resolved_at"] = now_iso
                    try:
                        dt_sub = datetime.fromisoformat(timeline["submitted_at"])
                        dt_res = datetime.fromisoformat(timeline["resolved_at"])
                        sec = max(0, (dt_res - dt_sub).total_seconds())
                        timeline["resolution_duration_seconds"] = sec
                        timeline["resolution_duration_formatted"] = format_duration(sec)
                    except Exception:
                        pass

            # Apply updates
            for k, v in updates.items():
                if k == "timeline" and isinstance(v, dict):
                    timeline.update(v)
                else:
                    complaint[k] = v

            complaint["timeline"] = timeline
            complaint["updated_at"] = now_iso
            _normalize_complaint(complaint)
            save_json(COMPLAINTS_FILE, complaints)
            return complaint
    return None


def mark_complaint_seen(complaint_id: str, role: str) -> Optional[Dict[str, Any]]:
    """Record department or management seen timestamp on complaint timeline."""
    complaints = load_json(COMPLAINTS_FILE, default=[])
    now_iso = datetime.now().isoformat()
    role_norm = (role or "").strip().lower()

    for complaint in complaints:
        if complaint.get("id") == complaint_id:
            _normalize_complaint(complaint)
            timeline = complaint["timeline"]
            changed = False

            if "department" in role_norm:
                if not timeline.get("department_seen_at"):
                    timeline["department_seen_at"] = now_iso
                    changed = True
                    if complaint.get("status") in ["Submitted", "Pending"]:
                        complaint["status"] = "Seen"
            elif "management" in role_norm or "admin" in role_norm:
                if not timeline.get("management_seen_at"):
                    timeline["management_seen_at"] = now_iso
                    changed = True

            if changed:
                complaint["timeline"] = timeline
                complaint["updated_at"] = now_iso
                save_json(COMPLAINTS_FILE, complaints)
            return complaint
    return None


# ==========================================
# DEPARTMENTS & STAFF
# ==========================================

def get_departments() -> List[Dict[str, Any]]:
    """Retrieve all college departments with keyword mappings."""
    return load_json(DEPARTMENTS_FILE, default=[])


def get_staff() -> List[Dict[str, Any]]:
    """Retrieve all staff members."""
    return load_json(STAFF_FILE, default=[])


def update_staff_availability(staff_id: str, available: bool) -> Optional[Dict[str, Any]]:
    """Update staff availability status."""
    staff_list = get_staff()
    for staff in staff_list:
        if staff.get("id") == staff_id:
            staff["available"] = available
            save_json(STAFF_FILE, staff_list)
            return staff
    return None


# ==========================================
# COMPLAINT HISTORY
# ==========================================

def get_history() -> List[Dict[str, Any]]:
    """Retrieve past resolved complaints for historical resolution matching."""
    return load_json(HISTORY_FILE, default=[])


def add_history(record: Dict[str, Any]) -> Dict[str, Any]:
    """Add a resolved complaint to history."""
    history = get_history()
    if "id" not in record:
        record["id"] = f"OLD{len(history)+1:03d}"
    history.append(record)
    save_json(HISTORY_FILE, history)
    return record


# ==========================================
# INCIDENTS MANAGEMENT
# ==========================================

def get_incidents() -> List[Dict[str, Any]]:
    """Retrieve all grouped incident clusters."""
    return load_json(INCIDENTS_FILE, default=[])


def get_incident_by_id(incident_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve incident by ID."""
    incidents = get_incidents()
    for inc in incidents:
        if inc.get("incident_id") == incident_id:
            return inc
    return None


def save_incidents(incidents: List[Dict[str, Any]]) -> bool:
    """Save all incidents list."""
    return save_json(INCIDENTS_FILE, incidents)


# ==========================================
# NOTIFICATIONS MANAGEMENT
# ==========================================

def get_notifications(student_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve notifications, optionally filtered by student_id."""
    notifications = load_json(NOTIFICATIONS_FILE, default=[])
    if student_id:
        return [n for n in notifications if n.get("student_id") == student_id]
    return notifications


def add_notification(student_id: str, message: str) -> Dict[str, Any]:
    """Create and persist a new student notification."""
    notifications = load_json(NOTIFICATIONS_FILE, default=[])
    notif = {
        "id": f"NOTIF-{len(notifications)+1:03d}",
        "student_id": student_id,
        "message": message,
        "created_at": datetime.now().isoformat(),
        "read": False
    }
    notifications.append(notif)
    save_json(NOTIFICATIONS_FILE, notifications)
    return notif


def mark_notification_read(notif_id: str) -> Optional[Dict[str, Any]]:
    """Mark a notification as read."""
    notifications = load_json(NOTIFICATIONS_FILE, default=[])
    for n in notifications:
        if n.get("id") == notif_id:
            n["read"] = True
            save_json(NOTIFICATIONS_FILE, notifications)
            return n
    return None


# ==========================================
# SYSTEM STATISTICS
# ==========================================

def get_stats() -> Dict[str, int]:
    """Calculate summary statistics for dashboard (backward compatible)."""
    complaints = get_complaints()
    incidents = get_incidents()

    stats = {
        "total": len(complaints),
        "pending": 0,
        "in_progress": 0,
        "resolved": 0,
        "escalated": 0,
        "assigned": 0,
        "seen": 0,
        "submitted": 0,
        "action_started": 0,
        "incidents": len(incidents)
    }

    for c in complaints:
        status = (c.get("status") or "").strip().lower()
        if status in ["pending", "submitted", "seen"]:
            stats["pending"] += 1
        if status == "submitted":
            stats["submitted"] += 1
        elif status == "seen":
            stats["seen"] += 1
        elif status in ["in progress", "in_progress", "inprogress"]:
            stats["in_progress"] += 1
        elif status in ["action started", "action_started"]:
            stats["action_started"] += 1
        elif status == "resolved":
            stats["resolved"] += 1
        elif status == "escalated":
            stats["escalated"] += 1
        elif status == "assigned":
            stats["assigned"] += 1

    return stats


def get_dashboard_analytics() -> Dict[str, Any]:
    """
    Dynamically calculate comprehensive statistics from actual complaint data:
    - Total complaints received today
    - Date-wise complaint counts (received & resolved)
    - Time-wise complaint counts (hourly & periods)
    - Department-wise complaint distribution
    - Resolved & pending complaint counts
    - Average resolution time
    """
    complaints = get_complaints()
    today_str = datetime.now().strftime("%Y-%m-%d")

    today_received = 0
    total_resolved = 0
    total_pending = 0

    dept_counts: Dict[str, int] = {}
    date_wise_map: Dict[str, Dict[str, int]] = {}
    hourly_counts = {f"{h:02d}:00": 0 for h in range(24)}
    period_counts = {"Morning (6AM-12PM)": 0, "Afternoon (12PM-5PM)": 0, "Evening (5PM-9PM)": 0, "Night (9PM-6AM)": 0}

    resolution_durations: List[float] = []

    for c in complaints:
        status = (c.get("status") or "Pending").strip()
        dept = c.get("department") or "General Administration"
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

        timeline = c.get("timeline") or {}
        submitted_at = timeline.get("submitted_at") or c.get("created_at") or ""
        resolved_at = timeline.get("resolved_at")

        sub_date = None
        sub_hour = None
        if submitted_at:
            try:
                dt_sub = datetime.fromisoformat(submitted_at)
                sub_date = dt_sub.strftime("%Y-%m-%d")
                sub_hour = dt_sub.hour

                # Today count
                if sub_date == today_str:
                    today_received += 1

                # Date-wise bucket for received
                if sub_date not in date_wise_map:
                    date_wise_map[sub_date] = {"date": sub_date, "received": 0, "resolved": 0}
                date_wise_map[sub_date]["received"] += 1

                # Hourly bucket
                h_key = f"{sub_hour:02d}:00"
                if h_key in hourly_counts:
                    hourly_counts[h_key] += 1

                # Time period bucket
                if 6 <= sub_hour < 12:
                    period_counts["Morning (6AM-12PM)"] += 1
                elif 12 <= sub_hour < 17:
                    period_counts["Afternoon (12PM-5PM)"] += 1
                elif 17 <= sub_hour < 21:
                    period_counts["Evening (5PM-9PM)"] += 1
                else:
                    period_counts["Night (9PM-6AM)"] += 1

            except Exception:
                pass

        # Check resolution
        if status.lower() == "resolved":
            total_resolved += 1
            if resolved_at:
                try:
                    dt_res = datetime.fromisoformat(resolved_at)
                    res_date = dt_res.strftime("%Y-%m-%d")
                    if res_date not in date_wise_map:
                        date_wise_map[res_date] = {"date": res_date, "received": 0, "resolved": 0}
                    date_wise_map[res_date]["resolved"] += 1
                except Exception:
                    pass

            dur = timeline.get("resolution_duration_seconds")
            if dur is not None and dur >= 0:
                resolution_durations.append(dur)
        else:
            total_pending += 1

    # Date-wise list sorted chronologically
    sorted_dates = sorted(date_wise_map.keys())
    date_wise_list = [
        {
            "date": d,
            "received": date_wise_map[d]["received"],
            "resolved": date_wise_map[d]["resolved"],
            "pending": max(0, date_wise_map[d]["received"] - date_wise_map[d]["resolved"])
        }
        for d in sorted_dates
    ]

    # Time-wise hourly list (filtering non-zero or presenting active hours)
    time_wise_list = [{"hour": h, "count": count} for h, count in hourly_counts.items()]

    # Average resolution time
    if resolution_durations:
        avg_seconds = sum(resolution_durations) / len(resolution_durations)
        avg_res_formatted = format_duration(avg_seconds)
    else:
        avg_seconds = 0
        avg_res_formatted = "N/A"

    return {
        "today_received": today_received,
        "total_complaints": len(complaints),
        "total_resolved": total_resolved,
        "total_pending": total_pending,
        "avg_resolution_seconds": round(avg_seconds, 1),
        "avg_resolution_time": avg_res_formatted,
        "department_wise": dept_counts,
        "date_wise": date_wise_list,
        "time_wise": {
            "hourly": time_wise_list,
            "periods": period_counts
        },
        "status_summary": get_stats()
    }
