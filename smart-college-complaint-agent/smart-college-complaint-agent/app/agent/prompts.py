SYSTEM_PROMPT = """You are the Smart College Complaint Resolution AI Agent.

Your primary objective is to autonomously analyze student complaints, determine the affected department, assess priority based on safety and academic urgency, assign available staff, check past resolution history, cluster related incidents, and take corrective actions using available tools.

Guidelines:
1. If a complaint impacts an ongoing or imminent exam, health/safety hazard, or major campus infrastructure, mark/escalate it as Critical priority.
2. Route issues accurately: Network (WiFi/LAN/Internet), Maintenance (Electricity/Water/Fan/Light/Plumbing), IT Support (Computers/Projectors/Lab PCs), Academic Office (Exams/Marks/Registration), Accounts (Fees/Dues).
3. Check previous complaint history to provide actionable suggestions or estimated resolution times when possible.
4. Always provide a clear, supportive, and professional final response for the student.
"""

AGENT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "route_complaint",
            "description": "Determine the responsible college department based on the complaint text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "complaint": {
                        "type": "string",
                        "description": "The complaint text to analyze."
                    }
                },
                "required": ["complaint"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "assign_staff",
            "description": "Find an available staff member in the assigned department.",
            "parameters": {
                "type": "object",
                "properties": {
                    "department": {
                        "type": "string",
                        "description": "Department name, e.g. Network Department, Maintenance Department"
                    }
                },
                "required": ["department"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "assess_priority",
            "description": "Assess the urgency and priority level of the issue (Critical, High, Medium, Low).",
            "parameters": {
                "type": "object",
                "properties": {
                    "complaint": {
                        "type": "string",
                        "description": "Complaint description."
                    }
                },
                "required": ["complaint"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_history",
            "description": "Search past resolved complaint records for similar issues and solutions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Keywords or phrase describing the issue."
                    }
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "change_complaint_status",
            "description": "Change the status of an existing complaint (e.g. Assigned, In Progress, Resolved).",
            "parameters": {
                "type": "object",
                "properties": {
                    "complaint_id": {
                        "type": "string",
                        "description": "The complaint ID."
                    },
                    "new_status": {
                        "type": "string",
                        "description": "New status value."
                    }
                },
                "required": ["complaint_id", "new_status"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_complaint",
            "description": "Escalate a critical complaint to leadership with a reason.",
            "parameters": {
                "type": "object",
                "properties": {
                    "complaint_id": {
                        "type": "string",
                        "description": "The complaint ID to escalate."
                    },
                    "reason": {
                        "type": "string",
                        "description": "The reason for escalation."
                    }
                },
                "required": ["complaint_id"]
            }
        }
    }
]
