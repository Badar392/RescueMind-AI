"""Transparent response planning. No autonomous dispatch is performed."""


def build_response_plan(incident, severity, location, duplicates, recommendations):
    priority = 1 if severity["severity"] == "Critical" else 2 if severity["severity"] == "High" else 3
    actions = []
    risks = []

    if severity["severity"] in {"Critical", "High"}:
        actions.append("Prioritize immediate coordinator review.")
    else:
        actions.append("Route for normal coordinator review.")

    if location.get("needs_verification"):
        actions.append("Verify the exact incident location before field deployment.")
        risks.append("Location is not GPS-verified.")

    if duplicates:
        actions.append("Review possible duplicate reports before creating additional operational work.")

    if recommendations:
        actions.append("Review ranked resource candidates and approve only appropriate resources.")
    else:
        actions.append("Identify additional available resources; no automatic dispatch is performed.")

    if severity["severity"] in {"Critical", "High"}:
        risks.append("Situation may escalate; reassess if new reports arrive.")

    if not severity.get("supporting_evidence"):
        risks.append("Severity evidence is limited; collect additional information.")

    missing = list(dict.fromkeys(
        severity.get("missing_information", [])
        + ([] if location.get("confidence", 0) >= 0.8 else ["Verified incident coordinates"])
    ))

    return {
        "priority": priority,
        "priority_label": {1: "Critical Review", 2: "Urgent Review", 3: "Standard Review"}[priority],
        "recommended_actions": actions,
        "risks": risks,
        "information_required": missing,
        "matched_resources": recommendations,
        "possible_duplicates": duplicates[:3],
        "human_approval_required": True,
        "automatic_dispatch": False,
    }
