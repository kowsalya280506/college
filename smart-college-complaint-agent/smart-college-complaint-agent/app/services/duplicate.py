import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import ollama
from app.config import OLLAMA_MODEL, is_ollama_available
from app.memory.data_manager import get_incidents, save_incidents


def normalize_complaint(text: str) -> set:
    """
    Normalize complaint text for semantic comparison by standardizing keywords
    and stripping common filler/stop words.
    """
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)

    replacements = {
        "wi-fi": "network",
        "wifi": "network",
        "internet": "network",
        "lan": "network",
        "router": "network",
        "not working": "broken",
        "down": "broken",
        "damaged": "broken",
        "leaking": "leak",
        "leakage": "leak",
        "ac": "airconditioner",
        "light": "lamp",
        "blackout": "powercut",
        "no power": "powercut"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    words = set(text.split())
    stop_words = {
        "is", "the", "a", "an", "my", "i", "we", "in", "on", "of",
        "to", "and", "not", "have", "there", "it", "our", "at", "for", "please"
    }

    return words - stop_words


def keyword_similarity(text1: str, text2: str) -> float:
    """Compute Jaccard similarity on normalized token sets."""
    words1 = normalize_complaint(text1)
    words2 = normalize_complaint(text2)

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    return len(intersection) / len(union)


def ai_duplicate_check(new_complaint: str, existing_complaint: str) -> bool:
    """
    Check if two complaints describe the same underlying issue using Ollama LLM
    with automatic fast heuristic fallback.
    """
    # 1. Quick exact/high similarity fast path
    sim = keyword_similarity(new_complaint, existing_complaint)
    if sim >= 0.4:
        return True

    # 2. Heuristic check: check significant overlap
    words1 = normalize_complaint(new_complaint)
    words2 = normalize_complaint(existing_complaint)
    common = words1.intersection(words2)
    if len(common) >= 2:
        return True

    # 3. Attempt LLM Classification only if Ollama daemon is reachable
    if is_ollama_available():
        try:
            prompt = f"""You are a smart complaint analyzer for a college.
Determine whether these two complaints describe the SAME underlying physical/technical incident.

Existing complaint: "{existing_complaint}"
New complaint: "{new_complaint}"

Examples:
"WiFi not working in Lab 2" and "Internet is down in CSE Lab" -> YES
"Water leakage in 2nd floor bathroom" and "WiFi not working" -> NO
"Hostel fan is not spinning" and "Room 204 fan broken" -> YES

Answer with ONLY one word: YES or NO."""

            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            answer = response.get("message", {}).get("content", "").strip().upper()
            if answer.startswith("YES"):
                return True
        except Exception:
            pass

    return False


def detect_duplicate(new_complaint_text: str, existing_complaints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Compare new complaint description against all active complaints to find duplicates.
    """
    matches = []
    for complaint in existing_complaints:
        desc = complaint.get("complaint") or complaint.get("description") or ""
        if not desc:
            continue
        if ai_duplicate_check(new_complaint_text, desc):
            matches.append(complaint)
    return matches


class IncidentManager:
    """Manages grouping of related complaints into unified incident tickets."""

    def __init__(self):
        self._load()

    def _load(self):
        self.incidents = get_incidents()

    def _save(self):
        save_incidents(self.incidents)

    def get_all_incidents(self) -> List[Dict[str, Any]]:
        self._load()
        return self.incidents

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        self._load()
        for inc in self.incidents:
            if inc.get("incident_id") == incident_id:
                return inc
        return None

    def create_incident(self, complaint: Dict[str, Any], category: str = "General") -> Dict[str, Any]:
        """Create a new incident ticket cluster."""
        self._load()
        next_num = len(self.incidents) + 1
        incident_id = f"INCIDENT-{next_num:03d}"

        student_name = complaint.get("student") or complaint.get("student_id") or "Unknown Student"
        complaint_id = complaint.get("id")

        incident = {
            "incident_id": incident_id,
            "category": category,
            "complaints": [complaint_id] if complaint_id else [],
            "affected_students": [student_name],
            "status": "Open",
            "created_at": datetime.now().isoformat()
        }

        self.incidents.append(incident)
        self._save()
        return incident

    def add_to_incident(self, incident_id: str, complaint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add duplicate complaint to existing incident cluster."""
        self._load()
        student_name = complaint.get("student") or complaint.get("student_id") or "Unknown Student"
        complaint_id = complaint.get("id")

        for inc in self.incidents:
            if inc.get("incident_id") == incident_id:
                if complaint_id and complaint_id not in inc["complaints"]:
                    inc["complaints"].append(complaint_id)
                if student_name and student_name not in inc["affected_students"]:
                    inc["affected_students"].append(student_name)
                inc["updated_at"] = datetime.now().isoformat()
                self._save()
                return inc
        return None

    def find_incident_for_complaints(self, duplicate_complaints: List[Dict[str, Any]]) -> Optional[str]:
        """Find an existing incident ID that contains any of the duplicate complaints."""
        self._load()
        dup_ids = {d.get("id") for d in duplicate_complaints if d.get("id")}
        for inc in self.incidents:
            for c_id in inc.get("complaints", []):
                if c_id in dup_ids:
                    return inc.get("incident_id")
        return None

    def process_complaint_incident(self, complaint: Dict[str, Any], duplicate_complaints: List[Dict[str, Any]], category: str = "General") -> Dict[str, Any]:
        """Automatically create a new incident or attach to an existing incident cluster."""
        if duplicate_complaints:
            existing_incident_id = self.find_incident_for_complaints(duplicate_complaints)
            if existing_incident_id:
                return self.add_to_incident(existing_incident_id, complaint)

        return self.create_incident(complaint, category=category)
