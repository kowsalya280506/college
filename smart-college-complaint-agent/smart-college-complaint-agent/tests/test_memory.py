import unittest
from app.memory.data_manager import (
    get_complaints,
    add_complaint,
    update_complaint,
    get_departments,
    get_staff,
    get_history,
    get_notifications,
    add_notification,
    mark_notification_read,
    get_stats
)


class TestMemory(unittest.TestCase):

    def test_departments_and_staff_load(self):
        depts = get_departments()
        self.assertIsInstance(depts, list)
        self.assertTrue(len(depts) > 0)

        staff = get_staff()
        self.assertIsInstance(staff, list)
        self.assertTrue(len(staff) > 0)

    def test_complaint_crud(self):
        # Create test complaint
        new_c = {
            "student": "Test Student",
            "location": "Test Room",
            "complaint": "Testing memory manager persistence",
            "department": "IT Support",
            "priority": "Low",
            "status": "Pending"
        }
        saved = add_complaint(new_c)
        self.assertIn("id", saved)
        cid = saved["id"]

        # Update
        updated = update_complaint(cid, {"status": "Resolved"})
        self.assertIsNotNone(updated)
        self.assertEqual(updated["status"], "Resolved")

    def test_notifications(self):
        notif = add_notification("StudentTest", "Test notification message")
        self.assertIn("id", notif)
        self.assertFalse(notif["read"])

        # Mark read
        read_notif = mark_notification_read(notif["id"])
        self.assertIsNotNone(read_notif)
        self.assertTrue(read_notif["read"])

    def test_stats(self):
        stats = get_stats()
        self.assertIn("total", stats)
        self.assertIn("pending", stats)
        self.assertIn("resolved", stats)
        self.assertIn("incidents", stats)


if __name__ == "__main__":
    unittest.main()
