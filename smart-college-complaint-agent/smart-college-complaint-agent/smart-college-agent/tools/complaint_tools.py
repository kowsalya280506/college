import sys
import os


# Find project root folder
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.append(PROJECT_ROOT)


from memory.data_manager import (
    get_departments,
    get_staff,
    get_history,
    update_complaint
)


# -------------------------------------------------
# TOOL 1: Find Department
# -------------------------------------------------

def find_department(issue):

    departments = get_departments()

    issue = issue.lower()

    for department in departments:

        for keyword in department["handles"]:

            if keyword.lower() in issue:

                return department["department"]

    return "General Administration"


# -------------------------------------------------
# TOOL 2: Find Available Staff
# -------------------------------------------------

def find_staff(department):

    staff = get_staff()

    for person in staff:

        if person["department"].lower() == department.lower():

            if person["available"]:

                return person

    return None


# -------------------------------------------------
# TOOL 3: Search Complaint History
# -------------------------------------------------

def search_history(issue):

    history = get_history()

    issue = issue.lower()

    results = []

    for record in history:

        old_issue = record.get("issue", "").lower()

        if issue in old_issue or old_issue in issue:

            results.append(record)

    return results


# -------------------------------------------------
# TOOL 4: Change Complaint Status
# -------------------------------------------------

def change_complaint_status(complaint_id, new_status):

    result = update_complaint(
        complaint_id,
        {
            "status": new_status
        }
    )

    return result


# -------------------------------------------------
# TOOL 5: Escalate Complaint
# -------------------------------------------------

def escalate_complaint(complaint_id):

    result = update_complaint(
        complaint_id,
        {
            "status": "Escalated",
            "priority": "Critical"
        }
    )

    return result