import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import ollama

from app.config import OLLAMA_MODEL, is_ollama_available
from app.agent.prompts import SYSTEM_PROMPT, AGENT_TOOLS_SCHEMA
from app.agent.tools import (
    execute_agent_tool,
    tool_route_complaint,
    tool_assess_priority,
    tool_assign_staff,
    tool_search_history
)
from app.services.duplicate import detect_duplicate, IncidentManager
from app.services.notification import notify_complaint_registered
from app.memory.data_manager import add_complaint, get_complaints, get_history


class ComplaintAgent:
    """
    Intelligent Agent for Smart College Complaint Processing.
    Supports autonomous tool calling with Ollama models and features
    a built-in resilient heuristic reasoning engine fallback.
    """

    def __init__(self, model_name: str = OLLAMA_MODEL):
        self.model_name = model_name
        self.incident_manager = IncidentManager()

    def process_complaint(
        self,
        student: str,
        location: str,
        complaint_text: str,
        category: Optional[str] = None,
        photo_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Full Agentic processing lifecycle for an incoming complaint.
        """
        agent_trace: List[Dict[str, Any]] = []
        start_time = datetime.now()

        # Step 0: Ingestion
        agent_trace.append({
            "stage": "INGESTION",
            "title": "Complaint Ingestion",
            "detail": f"Received complaint from {student} at {location}."
        })

        # Step 1: Duplicate & Incident Detection
        existing_complaints = get_complaints()
        duplicate_matches = detect_duplicate(complaint_text, existing_complaints)
        
        if duplicate_matches:
            dup_ids = [d.get("id") for d in duplicate_matches]
            agent_trace.append({
                "stage": "DUPLICATE_CHECK",
                "title": "Duplicate Issue Detected",
                "detail": f"Found {len(duplicate_matches)} matching complaint(s): {', '.join(dup_ids)}. Clustering into common incident."
            })
        else:
            agent_trace.append({
                "stage": "DUPLICATE_CHECK",
                "title": "Unique Issue",
                "detail": "No duplicate complaints detected. Creating unique incident cluster."
            })

        # Step 2: Agent Reasoning (Ollama LLM or Heuristic Pipeline)
        llm_success = False
        department = None
        priority = None
        priority_reason = ""
        assigned_staff = None
        historical_matches = []
        final_message = ""

        # Probe Ollama availability first
        if is_ollama_available():
            try:
                # Try Ollama Tool-Calling Agent Loop
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Student '{student}' reported: '{complaint_text}' at location '{location}'."
                    }
                ]

                response = ollama.chat(
                    model=self.model_name,
                    messages=messages,
                    tools=AGENT_TOOLS_SCHEMA
                )

                # Process tool calls if requested by LLM
                if response.get("message", {}).get("tool_calls"):
                    agent_trace.append({
                        "stage": "AI_REASONING",
                        "title": "LLM Autonomous Decision",
                        "detail": f"Model {self.model_name} invoked {len(response['message']['tool_calls'])} tools."
                    })

                    messages.append(response["message"])

                    for call in response["message"]["tool_calls"]:
                        t_name = call.get("function", {}).get("name")
                        t_args = call.get("function", {}).get("arguments", {})
                        t_res = execute_agent_tool(t_name, t_args)

                        agent_trace.append({
                            "stage": "TOOL_EXECUTION",
                            "title": f"Tool: {t_name}",
                            "detail": f"Arguments: {t_args} -> Result: {t_res}"
                        })

                        if t_name == "route_complaint" and t_res.get("department"):
                            department = t_res["department"]
                        elif t_name == "assess_priority" and t_res.get("priority"):
                            priority = t_res["priority"]
                            priority_reason = t_res.get("reason", "")
                        elif t_name == "assign_staff" and t_res.get("staff"):
                            assigned_staff = t_res["staff"]
                        elif t_name == "search_history" and t_res.get("matches"):
                            historical_matches = t_res["matches"]

                        messages.append({
                            "role": "tool",
                            "tool_name": t_name,
                            "content": json.dumps(t_res)
                        })

                    # Second LLM call for synthesis
                    final_res = ollama.chat(
                        model=self.model_name,
                        messages=messages,
                        tools=AGENT_TOOLS_SCHEMA
                    )
                    final_message = final_res.get("message", {}).get("content", "").strip()
                    llm_success = True

            except Exception as e:
                agent_trace.append({
                    "stage": "AI_REASONING",
                    "title": "Heuristic Engine Activated",
                    "detail": f"Ollama execution exception ({type(e).__name__}). Switching to heuristic agent pipeline."
                })
        else:
            agent_trace.append({
                "stage": "AI_REASONING",
                "title": "Autonomous Agent Engine Active",
                "detail": "Running built-in high-performance multi-step reasoning agent pipeline."
            })

        # Step 3: Heuristic Agent Pipeline fallback if LLM did not fill all fields
        if not department:
            route_res = tool_route_complaint(complaint_text)
            department = route_res.get("department", "General Administration")
            agent_trace.append({
                "stage": "ROUTING",
                "title": "Department Routing",
                "detail": f"Complaint categorized under '{department}' based on issue keywords."
            })

        if not priority:
            prio_res = tool_assess_priority(complaint_text)
            priority = prio_res.get("priority", "Medium")
            priority_reason = prio_res.get("reason", "Calculated standard priority")
            agent_trace.append({
                "stage": "PRIORITY",
                "title": f"Priority Level: {priority}",
                "detail": priority_reason
            })

        if not assigned_staff:
            staff_res = tool_assign_staff(department)
            assigned_staff = staff_res.get("staff")
            staff_msg = f"Assigned to {assigned_staff['name']} ({assigned_staff['role']})" if assigned_staff else "Queued for department head"
            agent_trace.append({
                "stage": "ASSIGNMENT",
                "title": "Staff Allocation",
                "detail": staff_msg
            })

        if not historical_matches:
            hist_res = tool_search_history(complaint_text)
            historical_matches = hist_res.get("matches", [])
            if historical_matches:
                agent_trace.append({
                    "stage": "KNOWLEDGE_BASE",
                    "title": "Historical Resolution Match",
                    "detail": f"Found {len(historical_matches)} past similar ticket(s). Previous fix: '{historical_matches[0].get('resolution')}'"
                })

        # Step 4: Determine initial ticket status
        status = "Assigned"
        if priority == "Critical":
            status = "Escalated"
        elif not assigned_staff:
            status = "Pending"

        now_iso = datetime.now().isoformat()
        new_complaint_data = {
            "student": student,
            "location": location,
            "complaint": complaint_text,
            "category": category or department.replace(" Department", ""),
            "priority": priority,
            "priority_reason": priority_reason,
            "department": department,
            "assigned_staff": assigned_staff.get("name") if assigned_staff else "Unassigned",
            "status": status,
            "photo_url": photo_url,
            "created_at": now_iso,
            "timeline": {
                "submitted_at": now_iso,
                "department_seen_at": None,
                "management_seen_at": None,
                "action_started_at": None,
                "resolved_at": None,
                "resolution_duration_seconds": None,
                "resolution_duration_formatted": None
            }
        }

        saved_complaint = add_complaint(new_complaint_data)
        complaint_id = saved_complaint.get("id", "CMP999")

        # Step 6: Link to Incident Cluster
        incident = self.incident_manager.process_complaint_incident(
            saved_complaint,
            duplicate_matches,
            category=new_complaint_data["category"]
        )

        agent_trace.append({
            "stage": "INCIDENT_TRACKING",
            "title": f"Incident Cluster: {incident.get('incident_id')}",
            "detail": f"Linked to incident ticket {incident.get('incident_id')} with {len(incident.get('affected_students', []))} affected student(s)."
        })

        # Step 7: Push Notification to Student
        notify_complaint_registered(student, complaint_id, department, priority)
        agent_trace.append({
            "stage": "NOTIFICATION",
            "title": "Notification Dispatched",
            "detail": f"Real-time update sent to student {student} for ticket {complaint_id}."
        })

        if not final_message:
            staff_info = f"assigned to {assigned_staff['name']} from {department}" if assigned_staff else f"forwarded to {department}"
            hist_info = f" (Past resolution: {historical_matches[0]['resolution']})" if historical_matches else ""
            final_message = (
                f"Your complaint ({complaint_id}) has been recorded with [{priority}] priority and {staff_info}.{hist_info} "
                f"Linked Incident: {incident.get('incident_id')}."
            )

        return {
            "complaint": saved_complaint,
            "incident": incident,
            "assigned_staff": assigned_staff,
            "priority": priority,
            "priority_reason": priority_reason,
            "department": department,
            "historical_matches": historical_matches,
            "agent_trace": agent_trace,
            "response_message": final_message,
            "processed_at": datetime.now().isoformat(),
            "duration_ms": int((datetime.now() - start_time).total_seconds() * 1000)
        }
