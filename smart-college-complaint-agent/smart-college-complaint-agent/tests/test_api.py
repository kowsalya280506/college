import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app


class TestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_get_stats(self):
        response = self.client.get("/api/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIn("stats", data)

    def test_list_complaints(self):
        response = self.client.get("/api/complaints")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIsInstance(data.get("complaints"), list)

    @patch("app.agent.core.is_ollama_available", return_value=False)
    @patch("app.services.duplicate.is_ollama_available", return_value=False)
    def test_submit_complaint(self, mock_ollama_dup, mock_ollama_core):
        payload = {
            "student": "Aakash",
            "location": "Library 1st Floor",
            "complaint": "AC is leaking water on the study tables"
        }
        response = self.client.post("/api/complaints", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        res_data = data.get("data", {})
        self.assertIn("complaint", res_data)
        self.assertIn("agent_trace", res_data)

    def test_incidents_endpoint(self):
        response = self.client.get("/api/incidents")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIsInstance(data.get("incidents"), list)


if __name__ == "__main__":
    unittest.main()
