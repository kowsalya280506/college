from ollama import chat
from agent.complaint_tools import (
    change_complaint_status,
    escalate_complaint
)


# ============================================================
# TOOL 1: ASSIGN COMPLAINT
# ============================================================
    """Assign a complaint to the responsible college department."""

    return {
        "status": "assigned",
        "department": department,
        "complaint": complaint,
        "message": f"Complaint successfully assigned to {department}."
    }


# ============================================================
# TOOL 2: ESCALATE COMPLAINT
# ============================================================

    """Escalate a critical or urgent complaint."""

    return {
        "status": "escalated",
        "department": department,
        "complaint": complaint,
        "reason": reason,
        "message": (
            f"Complaint escalated to {department} "
            f"because it requires urgent attention."
        )
    }


# ============================================================
# TOOL DEFINITIONS FOR QWEN
# ============================================================

tools = [

    {
        "type": "function",
        "function": {
            "name": "change_complaint_status",
            "description": (
                "Change the status of an existing college complaint."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "complaint_id": {
                        "type": "string",
                        "description": "The complaint ID."
                    },
                    "new_status": {
                        "type": "string",
                        "description": (
                            "The new status of the complaint, "
                            "such as Assigned, In Progress, or Resolved."
                        )
                    }
                },
                "required": [
                    "complaint_id",
                    "new_status"
                ]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "escalate_complaint",
            "description": (
                "Escalate a critical or urgent complaint. "
                "This changes the complaint status to Escalated "
                "and priority to Critical."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "complaint_id": {
                        "type": "string",
                        "description": "The complaint ID to escalate."
                    }
                },
                "required": [
                    "complaint_id"
                ]
            }
        }
    }
]
# ============================================================
# COMPLAINT
# ============================================================

complaint = (
    "Wi-Fi is not working in the CSE lab "
    "and we have an exam in 1 hour."
)


# ============================================================
# AGENT MESSAGES
# ============================================================

{
    "role": "system",
    "content": """
You are a Smart College Complaint Resolution Agent.

Your job is to analyze student complaints and take the
appropriate action using the available tools.

You have two tools:

1. change_complaint_status
   Use this to update the status of an existing complaint.

2. escalate_complaint
   Use this for critical or urgent complaints.
   It changes the complaint status to Escalated
   and priority to Critical.

If a complaint affects an exam, safety, or another
urgent college activity, use escalate_complaint.

You must use the complaint ID when modifying a complaint.

After the tool executes, use the tool result to
generate a short final response to the student.
"""
}

    {
        "role": "user",
        "content": complaint
    }
]


# ============================================================
# FIRST AGENT CALL
# ============================================================

response = chat(
    model="qwen3:latest",
    messages=messages,
    tools=tools
)


# ============================================================
# CHECK TOOL CALL
# ============================================================

if response.message.tool_calls:

    print("Agent decided to call a tool.")

    # Add Qwen's tool-call message to conversation
    messages.append(response.message)

    for call in response.message.tool_calls:

        tool_name = call.function.name
        arguments = call.function.arguments

        print("Tool selected:", tool_name)
        print("Arguments:", arguments)

        # ====================================================
        # EXECUTE THE TOOL CHOSEN BY QWEN
        # ====================================================

        if tool_name == "change_complaint_status":

    tool_result = change_complaint_status(
        complaint_id=arguments["complaint_id"],
        new_status=arguments["new_status"]
    )

elif tool_name == "escalate_complaint":

    tool_result = escalate_complaint(
        complaint_id=arguments["complaint_id"]
    )

else:

    tool_result = {
        "status": "error",
        "message": "Unknown tool requested."
    }

        # ====================================================
        # PRINT TOOL RESULT
        # ====================================================

        print("\nTool result:")
        print(tool_result)

        # ====================================================
        # SEND TOOL RESULT BACK TO QWEN
        # ====================================================

        messages.append(
            {
                "role": "tool",
                "tool_name": tool_name,
                "content": str(tool_result)
            }
        )

    # ========================================================
    # SECOND AGENT CALL
    # ========================================================

    final_response = chat(
        model="qwen3:latest",
        messages=messages,
        tools=tools
    )

    print("\nFinal Agent Response:")
    print(final_response.message.content)


else:

    print("Agent did not call any tool.")

    print("\nAgent Response:")
    print(response.message.content)