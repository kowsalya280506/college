import unittest
from unittest.mock import patch
from app.agent.core import ComplaintAgent
from app.agent.tools import execute_agent_tool


class TestAgent(unittest.TestCase):

    def setUp(self):
        self.agent = ComplaintAgent()

    def test_tool_execution(self):
        # Route tool
        r_res = execute_agent_tool("route_complaint", {"complaint": "WiFi not connecting"})
        self.assertEqual(r_res["status"], "success")
        self.assertEqual(r_res["department"], "Network Department")

        # Assign staff tool
        s_res = execute_agent_tool("assign_staff", {"department": "Network Department"})
        self.assertEqual(s_res["status"], "success")
        self.assertIsNotNone(s_res["staff"])

        # Assess priority tool
        p_res = execute_agent_tool("assess_priority", {"complaint": "Exam in 10 minutes and projector dead"})
        self.assertEqual(p_res["status"], "success")
        self.assertEqual(p_res["priority"], "Critical")

        # Search history tool
        h_res = execute_agent_tool("search_history", {"keyword": "wifi"})
        self.assertEqual(h_res["status"], "success")

    @patch("app.agent.core.is_ollama_available", return_value=False)
    @patch("app.services.duplicate.is_ollama_available", return_value=False)
    def test_agent_end_to_end_pipeline(self, mock_ollama_dup, mock_ollama_core):
        result = self.agent.process_complaint(
            student="Rohan",
            location="Room 301",
            complaint_text="Fan speed is very slow and switch is loose"
        )

        self.assertIn("complaint", result)
        self.assertIn("incident", result)
        self.assertIn("agent_trace", result)
        self.assertIn("response_message", result)
        self.assertEqual(result["department"], "Maintenance Department")
        self.assertTrue(len(result["agent_trace"]) >= 4)


if __name__ == "__main__":
    unittest.main()
