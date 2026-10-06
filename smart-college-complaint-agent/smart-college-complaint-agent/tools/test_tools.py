from complaint_tools import (
    find_department,
    find_staff,
    search_history,
    change_complaint_status,
    escalate_complaint
)


print("======================================")
print("SMART COLLEGE COMPLAINT AGENT")
print("FULL TOOL TEST")
print("======================================")


# --------------------------------------
# STEP 1: Find Department
# --------------------------------------

print("\n1. FINDING DEPARTMENT")

issue = "WiFi is not working"

department = find_department(issue)

print("Issue:", issue)
print("Department:", department)


# --------------------------------------
# STEP 2: Find Staff
# --------------------------------------

print("\n2. FINDING STAFF")

staff = find_staff(department)

print("Assigned Staff:", staff)


# --------------------------------------
# STEP 3: Search History
# --------------------------------------

print("\n3. SEARCHING HISTORY")

history = search_history(issue)

print("Previous Complaints:", history)


# --------------------------------------
# STEP 4: Change Status
# --------------------------------------

print("\n4. CHANGING STATUS")

updated = change_complaint_status(
    "CMP001",
    "In Progress"
)

print("Updated Complaint:", updated)


# --------------------------------------
# STEP 5: Escalate
# --------------------------------------

print("\n5. ESCALATING COMPLAINT")

escalated = escalate_complaint("CMP001")

print("Escalated Complaint:", escalated)


# --------------------------------------
# COMPLETE
# --------------------------------------

print("\n======================================")
print("FULL TOOL TEST COMPLETED")
print("======================================")