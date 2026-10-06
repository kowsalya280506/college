import unittest
import base64
from unittest.mock import patch
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.memory.data_manager import (
    get_complaints,
    get_complaint_by_id,
    mark_complaint_seen,
    update_complaint,
    get_dashboard_analytics,
    format_duration
)


class TestNewFeatures(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_student_login_success(self):
        """Test student login with valid credentials VCET26 / velalar."""
        res = self.client.post("/api/auth/student-login", json={
            "username": "VCET26",
            "password": "velalar"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["student"]["username"], "VCET26")
        self.assertIn("token", data)

    def test_student_login_invalid(self):
        """Test student login with invalid password."""
        res = self.client.post("/api/auth/student-login", json={
            "username": "VCET26",
            "password": "wrongpassword"
        })
        self.assertEqual(res.status_code, 401)

    def test_base64_photo_upload(self):
        """Test optional base64 photo upload."""
        # 1x1 transparent PNG base64
        dummy_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        res = self.client.post("/api/upload", json={
            "image_data": f"data:image/png;base64,{dummy_png}",
            "filename": "proof.png"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertTrue(data.get("photo_url").startswith("/uploads/"))

    @patch("app.agent.core.is_ollama_available", return_value=False)
    @patch("app.services.duplicate.is_ollama_available", return_value=False)
    def test_complaint_submission_with_and_without_photo(self, mock_dup, mock_core):
        """Test that complaint submits successfully both with and without photo."""
        # 1. Without photo (photo is completely optional)
        res_no_photo = self.client.post("/api/complaints", json={
            "student": "VCET26",
            "location": "Mechanical Block Lab 3",
            "complaint": "Lathe machine power switch is broken and sparking"
        })
        self.assertEqual(res_no_photo.status_code, 200)
        c_no_photo = res_no_photo.json()["data"]["complaint"]
        self.assertIsNone(c_no_photo.get("photo_url"))
        self.assertIsNotNone(c_no_photo.get("timeline"))
        self.assertIsNotNone(c_no_photo["timeline"].get("submitted_at"))

        # 2. With optional photo
        dummy_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        res_with_photo = self.client.post("/api/complaints", json={
            "student": "VCET26",
            "location": "Hostel Block A",
            "complaint": "Water tap leaking heavily in bathroom 2",
            "photo_data": f"data:image/png;base64,{dummy_png}"
        })
        self.assertEqual(res_with_photo.status_code, 200)
        c_with_photo = res_with_photo.json()["data"]["complaint"]
        self.assertIsNotNone(c_with_photo.get("photo_url"))
        self.assertTrue(c_with_photo["photo_url"].startswith("/uploads/"))

    def test_complete_timeline_lifecycle(self):
        """Test complete 5-stage timeline and resolution duration."""
        # Create a fresh ticket directly
        now = datetime.now().isoformat()
        ticket_id = f"CMP_TEST_{int(datetime.now().timestamp())}"
        from app.memory.data_manager import add_complaint
        added = add_complaint({
            "id": ticket_id,
            "student": "VCET26",
            "location": "Physics Lab",
            "complaint": "Galvanometer needle stuck",
            "department": "Maintenance Department",
            "status": "Submitted"
        })

        # 1. Submitted stage
        self.assertIsNotNone(added["timeline"]["submitted_at"])

        # 2. Department Seen
        res_dept_seen = self.client.post(f"/api/complaints/{ticket_id}/seen", json={"role": "department"})
        self.assertEqual(res_dept_seen.status_code, 200)
        self.assertIsNotNone(res_dept_seen.json()["complaint"]["timeline"]["department_seen_at"])

        # 3. Management Seen
        res_mgmt_seen = self.client.post(f"/api/complaints/{ticket_id}/seen", json={"role": "management"})
        self.assertEqual(res_mgmt_seen.status_code, 200)
        self.assertIsNotNone(res_mgmt_seen.json()["complaint"]["timeline"]["management_seen_at"])

        # 4. Action Started
        res_action = self.client.patch(f"/api/complaints/{ticket_id}/status", json={"status": "Action Started"})
        self.assertEqual(res_action.status_code, 200)
        self.assertIsNotNone(res_action.json()["complaint"]["timeline"]["action_started_at"])

        # 5. Resolved & Duration
        res_resolve = self.client.patch(f"/api/complaints/{ticket_id}/status", json={
            "status": "Resolved",
            "resolution_notes": "Galvanometer recalibrated and tested"
        })
        self.assertEqual(res_resolve.status_code, 200)
        resolved_c = res_resolve.json()["complaint"]
        self.assertIsNotNone(resolved_c["timeline"]["resolved_at"])
        self.assertIsNotNone(resolved_c["timeline"]["resolution_duration_seconds"])
        self.assertIsNotNone(resolved_c["timeline"]["resolution_duration_formatted"])

    def test_dashboard_analytics_dynamic(self):
        """Test dynamic dashboard analytics endpoint."""
        res = self.client.get("/api/stats/dashboard")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        analytics = data.get("analytics", {})

        # Verify all dynamic fields exist
        self.assertIn("today_received", analytics)
        self.assertIn("total_complaints", analytics)
        self.assertIn("total_resolved", analytics)
        self.assertIn("total_pending", analytics)
        self.assertIn("avg_resolution_time", analytics)
        self.assertIn("department_wise", analytics)
        self.assertIn("date_wise", analytics)
        self.assertIn("time_wise", analytics)

        self.assertIsInstance(analytics["department_wise"], dict)
        self.assertIsInstance(analytics["date_wise"], list)
        self.assertIsInstance(analytics["time_wise"]["hourly"], list)

    def test_student_and_department_filtering(self):
        """Test filtering complaints for student tracking and department views."""
        # Filter by student VCET26
        res_student = self.client.get("/api/complaints?student_id=VCET26")
        self.assertEqual(res_student.status_code, 200)
        c_list = res_student.json()["complaints"]
        for c in c_list:
            self.assertIn("vcet26", (c.get("student") or "").lower())

        # Filter by department
        res_dept = self.client.get("/api/complaints?department=Maintenance")
        self.assertEqual(res_dept.status_code, 200)
        dept_list = res_dept.json()["complaints"]
        for c in dept_list:
            self.assertIn("maintenance", (c.get("department") or "").lower())


if __name__ == "__main__":
    unittest.main()
