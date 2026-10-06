import sys
import os
import argparse
import unittest

# Configure standard stdout to handle utf-8 safely
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

# Ensure project root is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import SERVER_HOST, SERVER_PORT
from app.agent.core import ComplaintAgent
from app.services.escalation import run_sla_escalation_sweep
from app.memory.data_manager import get_complaints, get_stats


def run_server():
    """Start the FastAPI Web Server with Uvicorn."""
    import uvicorn
    print("=" * 65)
    print("SMART COLLEGE COMPLAINT RESOLUTION AGENT - SERVER")
    print("=" * 65)
    print(f"Server running at: http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"Student Portal:    http://{SERVER_HOST}:{SERVER_PORT}/")
    print(f"Student Login:     http://{SERVER_HOST}:{SERVER_PORT}/student-login")
    print(f"Admin Dashboard:   http://{SERVER_HOST}:{SERVER_PORT}/admin")
    print(f"API Documentation: http://{SERVER_HOST}:{SERVER_PORT}/docs")
    print("=" * 65)
    uvicorn.run("app.main:app", host=SERVER_HOST, port=SERVER_PORT, reload=False)


def run_cli_interactive():
    """Run interactive terminal agent console."""
    agent = ComplaintAgent()
    print("=" * 65)
    print("SMART COLLEGE COMPLAINT AGENT - INTERACTIVE CLI")
    print("=" * 65)
    print("Type 'exit' or 'quit' to terminate.\n")

    while True:
        try:
            student = input("Enter Student Name / Roll (default: STU_DEMO): ").strip() or "STU_DEMO"
            if student.lower() in ["exit", "quit"]:
                break

            location = input("Enter Location (e.g. CSE Lab 2, Hostel B): ").strip() or "General Campus"
            complaint_text = input("Enter Complaint Description: ").strip()

            if not complaint_text:
                print("Complaint cannot be empty. Try again.\n")
                continue

            print("\n[AI Agent] Processing complaint...")
            result = agent.process_complaint(student, location, complaint_text)

            print("\n" + "-" * 50)
            print(f"Ticket ID:       {result['complaint']['id']}")
            print(f"Department:      {result['department']}")
            print(f"Assigned Staff:  {result['assigned_staff']['name'] if result['assigned_staff'] else 'Unassigned'}")
            print(f"Priority:        {result['priority']} ({result['priority_reason']})")
            print(f"Status:          {result['complaint']['status']}")
            print(f"Incident ID:     {result['incident']['incident_id']}")
            print(f"Agent Message:   {result['response_message']}")
            print("-" * 50)
            print("Execution Trace Steps:")
            for s in result["agent_trace"]:
                print(f"  * [{s['stage']}] {s['title']}: {s['detail']}")
            print("=" * 65 + "\n")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting CLI.")
            break


def run_tests():
    """Discover and execute all test suites."""
    print("=" * 65)
    print("RUNNING COMPLAINT AGENT TEST SUITE")
    print("=" * 65)
    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)


def run_sla():
    """Trigger SLA escalation sweep."""
    print("Scanning pending tickets for SLA escalation...")
    escalated = run_sla_escalation_sweep(hours_threshold=24)
    print(f"SLA Sweep completed. Total escalated: {len(escalated)}")
    for e in escalated:
        print(f"  - Escalated ticket {e['id']} for student {e.get('student')}")


def main():
    parser = argparse.ArgumentParser(description="Smart College Complaint Resolution Agent Runner")
    parser.add_argument("--cli", action="store_true", help="Launch interactive CLI agent session")
    parser.add_argument("--test", action="store_true", help="Run automated test suite")
    parser.add_argument("--sla", action="store_true", help="Run SLA escalation sweep")
    parser.add_argument("--port", type=int, default=SERVER_PORT, help="Port to run server on")

    args = parser.parse_args()

    if args.cli:
        run_cli_interactive()
    elif args.test:
        run_tests()
    elif args.sla:
        run_sla()
    else:
        run_server()


if __name__ == "__main__":
    main()
