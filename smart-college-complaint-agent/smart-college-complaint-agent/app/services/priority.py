from typing import Tuple, Dict, Any


def calculate_priority(complaint_text: str) -> Tuple[str, str]:
    """
    Calculate the priority level and rationale for a given complaint.
    
    Priority Levels:
    - Critical: Immediate safety hazards, emergencies, exams impacted imminently
    - High: Essential service breakdowns, security concerns, class disruptions
    - Medium: Routine utility disruptions (WiFi, fans, lights, mess food)
    - Low: General suggestions, minor cosmetic issues
    
    Returns:
        (priority_level, reason_string)
    """
    text = complaint_text.lower()

    # 1. Critical Priority Check
    critical_triggers = [
        "fire", "gas leak", "electrical shock", "danger", "emergency",
        "exam in", "exam start", "exam today", "medical", "injury", "short circuit"
    ]
    for trigger in critical_triggers:
        if trigger in text:
            return "Critical", f"Critical priority assigned due to urgent trigger: '{trigger}'"

    # 2. High Priority Check
    high_triggers = [
        "water leak", "electricity", "power cut", "power outage", "blackout",
        "security", "unsafe", "theft", "harassment", "projector", "lab down", "urgent"
    ]
    for trigger in high_triggers:
        if trigger in text:
            return "High", f"High priority assigned due to operational impact: '{trigger}'"

    # 3. Medium Priority Check
    medium_triggers = [
        "wifi", "wi-fi", "internet", "network", "lan", "fan", "light",
        "food", "mess", "canteen", "cleanliness", "ac", "air conditioner"
    ]
    for trigger in medium_triggers:
        if trigger in text:
            return "Medium", f"Medium priority assigned for standard facility issue: '{trigger}'"

    # 4. Default: Low Priority
    return "Low", "Standard low priority assigned for general complaint/inquiry"
