import re
import time
from math import sqrt
from utils.models import AgentExecution, Resource
from utils.ai import explain_incident


def intake_agent(description, selected_category):
    text = description.lower()
    category = selected_category
    if category == "Auto Detect":
        rules = {
            "Flood": ["flood", "water", "flooded", "overflow", "rising water"],
            "Earthquake": ["earthquake", "tremor", "building shaking"],
            "Fire": ["fire", "burning", "smoke", "flames"],
            "Road Accident": ["accident", "crash", "collision", "vehicle"],
            "Medical Emergency": ["injury", "injured", "unconscious", "bleeding", "medical"],
        }
        category = next(
            (name for name, words in rules.items() if any(w in text for w in words)),
            "Other",
        )

    missing = []
    if len(description.strip()) < 30:
        missing.append("More detailed incident description")
    if not any(x in text for x in ["near ", "at ", "in ", "on "]):
        missing.append("Location details")

    return {
        "category": category,
        "missing_information": missing,
        "confidence": 0.85 if category != "Other" else 0.45,
    }


def location_agent(location):
    if not location:
        return {
            "latitude": None,
            "longitude": None,
            "confidence": 0,
            "verified": False,
            "note": "No coordinates supplied. Coordinates were not invented.",
        }

    parts = [x.strip() for x in location.split(",")]
    try:
        if len(parts) == 2:
            lat, lon = float(parts[0]), float(parts[1])
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return {
                    "latitude": lat,
                    "longitude": lon,
                    "confidence": 1,
                    "verified": False,
                    "note": "Coordinates were explicitly supplied by the reporter.",
                }
    except ValueError:
        pass

    return {
        "latitude": None,
        "longitude": None,
        "confidence": 0.3,
        "verified": False,
        "note": "Text location detected; no coordinates were invented.",
    }


def severity_agent(description, category):
    text = description.lower()
    score = 25
    evidence = []
    rules = [
        (["death", "dead", "fatal"], 45, "Reported fatality"),
        (["trapped"], 30, "Reported trapped people"),
        (["injured", "injury", "bleeding"], 25, "Reported injury"),
        (["unconscious"], 30, "Reported unconscious person"),
        (["collapsed"], 25, "Reported structural collapse"),
        (["rising water", "flooded"], 20, "Reported water hazard"),
        (["large fire", "spreading"], 25, "Reported escalation"),
    ]
    for words, points, reason in rules:
        if any(word in text for word in words):
            score += points
            evidence.append(reason)
    if category in {"Fire", "Earthquake"}:
        score += 5
    score = min(score, 100)
    severity = "Critical" if score >= 80 else "High" if score >= 60 else "Medium" if score >= 35 else "Low"
    return {
        "score": score,
        "severity": severity,
        "supporting_evidence": evidence,
        "missing_information": ["Exact number of people affected"],
        "human_verification_required": True,
    }


def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def similarity(a, b):
    left, right = _tokens(a), _tokens(b)
    if not left or not right:
        return 0
    return len(left & right) / sqrt(len(left) * len(right))


def duplicate_agent(description, incidents, threshold=0.42):
    matches = []
    for incident in incidents:
        score = similarity(description, incident.description)
        if score >= threshold:
            matches.append({
                "incident_id": incident.id,
                "incident_code": incident.incident_code,
                "score": round(score, 3),
                "description": incident.description,
            })
    return sorted(matches, key=lambda x: x["score"], reverse=True)


def resource_agent(incident, resources):
    """Match available simulated resources to the incident category."""
    required = {
        "Flood": ["Rescue Boat", "Rescue Team", "Medical Unit"],
        "Earthquake": ["Rescue Team", "Medical Unit", "Supplies"],
        "Fire": ["Rescue Team", "Ambulance"],
        "Road Accident": ["Ambulance", "Rescue Team"],
        "Medical Emergency": ["Ambulance", "Medical Unit"],
    }.get(incident.category, ["Rescue Team"])

    results = []
    for rtype in required:
        available = next(
            (r for r in resources if r.status == "Available" and r.resource_type == rtype),
            None,
        )
        if available:
            results.append({
                "resource_id": available.id,
                "resource_code": available.resource_code,
                "name": available.name,
                "type": available.resource_type,
                "reason": f"{rtype} is relevant to the reported {incident.category.lower()} scenario.",
            })
    return results


def response_planning_agent(incident, recommendations):
    """Create a transparent, non-dispatching response recommendation."""
    actions = []
    if incident.severity in {"Critical", "High"}:
        actions.append("Prioritize coordinator review and verify people-at-risk information.")
    if recommendations:
        actions.append("Review the matched resources and approve only the resources appropriate to the situation.")
    else:
        actions.append("Identify additional available resources; no automatic dispatch is performed.")
    if incident.latitude is None or incident.longitude is None:
        actions.append("Verify the incident location before any field deployment.")
    actions.append("Record the coordinator decision in the incident audit trail.")

    return {
        "priority": 1 if incident.severity == "Critical" else 2 if incident.severity == "High" else 3,
        "recommended_actions": actions,
        "matched_resources": recommendations,
        "human_approval_required": True,
        "automatic_dispatch": False,
    }


def orchestrate(db, incident, selected_category):
    """AI Orchestrator: runs specialized agents in a controlled workflow."""
    start = time.perf_counter()

    intake = intake_agent(incident.description, selected_category)
    location = location_agent(incident.location_text)
    severity = severity_agent(incident.description, intake["category"])

    incidents = db.query(type(incident)).filter(type(incident).id != incident.id).all()
    duplicates = duplicate_agent(incident.description, incidents)

    incident.category = intake["category"]
    incident.title = f"{incident.category} incident"
    incident.severity = severity["severity"]
    incident.severity_score = severity["score"]
    incident.latitude = location["latitude"]
    incident.longitude = location["longitude"]

    explanation = explain_incident(
        category=incident.category,
        description=incident.description,
        severity=severity,
        intake=intake,
    )
    incident.ai_summary = explanation["summary"]
    incident.ai_explanation = explanation

    resources = db.query(Resource).all()
    recommendations = resource_agent(incident, resources)
    response_plan = response_planning_agent(incident, recommendations)

    elapsed = int((time.perf_counter() - start) * 1000)
    outputs = [
        ("Report Understanding Agent", intake),
        ("Location Extraction Agent", location),
        ("Severity Assessment Agent", severity),
        ("Duplicate Detection Agent", {"matches": duplicates}),
        ("AI Explanation Agent", explanation),
        ("Resource Matching Agent", {"recommendations": recommendations}),
        ("Response Planning Agent", response_plan),
    ]
    for name, output in outputs:
        db.add(AgentExecution(
            incident_id=incident.id,
            agent_name=name,
            status="success",
            output_json=output,
            duration_ms=elapsed,
        ))

    return {
        "intake": intake,
        "location": location,
        "severity": severity,
        "duplicates": duplicates,
        "explanation": explanation,
        "resource_recommendations": recommendations,
        "response_plan": response_plan,
    }
