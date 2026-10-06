import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
from app.services.priority import calculate_priority
from app.services.routing import find_department, find_staff
from app.services.duplicate import (
    normalize_complaint,
    keyword_similarity,
    detect_duplicate,
    IncidentManager
)
from app.services.escalation import check_pending_complaints


class TestServices(unittest.TestCase):

    def test_priority_calculation(self):
        # Critical priority tests
        prio1, _ = calculate_priority("WiFi down and we have exam in 30 mins")
        self.assertEqual(prio1, "Critical")

        prio_fire, _ = calculate_priority("Fire hazard in chemistry lab")
        self.assertEqual(prio_fire, "Critical")

        # High priority tests
        prio_water, _ = calculate_priority("Heavy water leak in 2nd floor bathroom")
        self.assertEqual(prio_water, "High")

        # Medium priority tests
        prio_fan, _ = calculate_priority("Fan is making noise in room 204")
        self.assertEqual(prio_fan, "Medium")

        # Low priority tests
        prio_low, _ = calculate_priority("Suggestion for library books")
        self.assertEqual(prio_low, "Low")

    def test_routing(self):
        dept_wifi = find_department("WiFi connection is dropping frequently")
        self.assertEqual(dept_wifi, "Network Department")

        dept_water = find_department("Water tap broken in restroom")
        self.assertEqual(dept_water, "Maintenance Department")

        dept_pc = find_department("Projector display is flickering in seminar hall")
        self.assertEqual(dept_pc, "IT Support")

        dept_exam = find_department("Registration issue for semester end exam")
        self.assertEqual(dept_exam, "Academic Office")

    def test_staff_lookup(self):
        staff = find_staff("Network Department")
        self.assertIsNotNone(staff)
        self.assertIn("name", staff)
        self.assertEqual(staff.get("department"), "Network Department")

    @patch("app.services.duplicate.is_ollama_available", return_value=False)
    def test_duplicate_and_incident(self, mock_ollama):
        words = normalize_complaint("The WiFi is not working in CSE lab")
        self.assertIn("network", words)
        self.assertIn("broken", words)

        comp1 = {
            "id": "CMP001",
            "student_id": "STU001",
            "student": "STU001",
            "complaint": "WiFi is not working in CSE lab"
        }
        
        # Exact/similar issue
        dups = detect_duplicate("Internet broken in CSE lab", [comp1])
        self.assertTrue(len(dups) > 0)

        # Different issue
        no_dups = detect_duplicate("Bathroom door is jammed", [comp1])
        self.assertEqual(len(no_dups), 0)

    def test_incident_manager(self):
        manager = IncidentManager()
        comp1 = {"id": "TEST_CMP1", "student": "Student1"}
        comp2 = {"id": "TEST_CMP2", "student": "Student2"}

        inc = manager.create_incident(comp1, category="Network")
        self.assertIn("INCIDENT-", inc["incident_id"])
        self.assertIn("TEST_CMP1", inc["complaints"])

        updated_inc = manager.add_to_incident(inc["incident_id"], comp2)
        self.assertIn("TEST_CMP2", updated_inc["complaints"])
        self.assertIn("Student2", updated_inc["affected_students"])

    def test_escalation_detection(self):
        old_time = (datetime.now() - timedelta(hours=30)).isoformat()
        recent_time = datetime.now().isoformat()

        complaints = [
            {"id": "CMP_OLD", "status": "Pending", "created_at": old_time},
            {"id": "CMP_NEW", "status": "Pending", "created_at": recent_time},
            {"id": "CMP_RES", "status": "Resolved", "created_at": old_time}
        ]

        overdue = check_pending_complaints(complaints, hours_threshold=24)
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0]["id"], "CMP_OLD")


if __name__ == "__main__":
    unittest.main()
