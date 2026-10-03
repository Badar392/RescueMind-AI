"""RescueMind AI multi-agent orchestration engine.

The agents are intentionally explainable and human-controlled. They enrich a
shared IncidentContext, rank evidence/resources, and never dispatch anything
on their own.
"""
import re
import time
from math import sqrt

from utils.models import AgentExecution, IncidentLocation, Resource
from utils.ai import explain_incident
from utils.agent_context import IncidentContext
from utils.location_service import extract_location
from utils.resource_matcher import rank_resources
from utils.response_planner import build_response_plan


CATEGORY_RULES = {
    "Flood": ["flood", "water", "flooded", "overflow", "rising water", "water level"],
    "Earthquake": ["earthquake", "tremor", "building shaking", "shaking ground"],
    "Fire": ["fire", "burning", "smoke", "flames", "blaze"],
    "Road Accident": ["accident", "crash", "collision", "vehicle", "motorcycle"],
    "Medical Emergency": ["injury", "injured", "unconscious", "bleeding", "medical", "ambulance"],
}


def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def similarity(a, b):
    left, right = _tokens(a), _tokens(b)
    if not left or not right:
        return 0.0
    return len(left & right) / sqrt(len(left) * len(right))


def intake_agent(description, selected_category):
    text = (description or "").lower()
    category = selected_category
    evidence = []

    if category == "Auto Detect":
        scores = {}
        for name, words in CATEGORY_RULES.items():
            hits = [word for word in words if word in text]
            if hits:
                scores[name] = len(hits)
        if scores:
            category = max(scores, key=scores.get)
            evidence = [f"Matched category indicators: {', '.join([w for w in CATEGORY_RULES[category] if w in text][:4])}"]
        else:
            category = "Other"
    else:
        evidence = [f"Category supplied by reporter/coordinator: {category}"]

    missing = []
    if len(description.strip()) < 30:
        missing.append("More detailed incident description")
    if not any(x in text for x in ["near ", "at ", "in ", "on ", "location", "road", "street"]):
        missing.append("Location details")

    confidence = 0.90 if selected_category != "Auto Detect" else (0.82 if category != "Other" else 0.42)
    return {
        "category": category,
        "missing_information": missing,
        "confidence": confidence,
        "evidence": evidence,
        "decision": category,
    }


def location_agent(location):
    return extract_location(location)


def severity_agent(description, category):
    text = (description or "").lower()
    score = 25
    evidence = []
    rules = [
        (["death", "dead", "fatal", "killed"], 45, "Reported fatality"),
        (["trapped", "stranded"], 30, "Reported trapped/stranded people"),
        (["injured", "injury", "bleeding", "wounded"], 25, "Reported injury"),
        (["unconscious", "not breathing"], 30, "Reported unconscious/non-responsive person"),
        (["collapsed", "collapse"], 25, "Reported structural collapse"),
        (["rising water", "flooded", "water level"], 20, "Reported water hazard"),
        (["large fire", "spreading", "explosion", "gas leak"], 25, "Reported escalation/hazard"),
    ]
    for words, points, reason in rules:
        if any(word in text for word in words):
            score += points
            evidence.append(reason)
    if category in {"Fire", "Earthquake"}:
        score += 5
    score = min(score, 100)
    severity = "Critical" if score >= 80 else "High" if score >= 60 else "Medium" if score >= 35 else "Low"
    missing = ["Exact number of people affected"]
    if severity in {"Critical", "High"}:
        missing.append("Current immediate hazards")
    return {
        "score": score,
        "severity": severity,
        "confidence": min(0.95, 0.62 + len(evidence) * 0.08),
        "supporting_evidence": evidence,
        "missing_information": missing,
        "human_verification_required": True,
    }


def duplicate_agent(description, incidents, location=None, category=None, threshold=0.42):
    matches = []
    new_lat = (location or {}).get("latitude")
    new_lon = (location or {}).get("longitude")

    for incident in incidents:
        text_score = similarity(description, incident.description)
        category_score = 1.0 if category and incident.category == category else 0.0
        distance_km = None
        location_score = 0.0
        if None not in (new_lat, new_lon, incident.latitude, incident.longitude):
            dlat = new_lat - incident.latitude
            dlon = new_lon - incident.longitude
            # Small-distance approximation is enough for duplicate triage.
            distance_km = sqrt(dlat * dlat + dlon * dlon) * 111.0
            location_score = max(0.0, 1.0 - min(distance_km / 10.0, 1.0))

        combined = text_score * 0.65 + category_score * 0.15 + location_score * 0.20
        if combined >= threshold:
            matches.append({
                "incident_id": incident.id,
                "incident_code": incident.incident_code,
                "score": round(combined, 3),
                "text_similarity": round(text_score, 3),
                "category_similarity": round(category_score, 3),
                "location_similarity": round(location_score, 3),
                "distance_km": round(distance_km, 2) if distance_km is not None else None,
                "description": incident.description,
            })
    return sorted(matches, key=lambda x: x["score"], reverse=True)


def resource_agent(incident, resources):
    """Backward-compatible wrapper around the ranked resource matcher."""
    return rank_resources(incident, resources)


def response_planning_agent(incident, recommendations, severity=None, location=None, duplicates=None):
    severity = severity or {
        "severity": incident.severity,
        "supporting_evidence": [],
        "missing_information": [],
    }
    location = location or {
        "needs_verification": incident.latitude is None or incident.longitude is None,
        "confidence": 0,
    }
    return build_response_plan(incident, severity, location, duplicates or [], recommendations)


def _run_agent(db, incident, name, fn, context):
    started = time.perf_counter()
    try:
        output = fn()
        duration_ms = int((time.perf_counter() - started) * 1000)
        context.agent_trace.append({
            "agent": name,
            "status": "success",
            "duration_ms": duration_ms,
            "confidence": output.get("confidence") if isinstance(output, dict) else None,
        })
        db.add(AgentExecution(
            incident_id=incident.id,
            agent_name=name,
            status="success",
            output_json=output if isinstance(output, dict) else {"output": output},
            duration_ms=duration_ms,
        ))
        return output
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        error = {"error": type(exc).__name__, "message": str(exc)}
        context.warn(f"{name} failed; fallback information was used.")
        context.agent_trace.append({"agent": name, "status": "error", "duration_ms": duration_ms})
        db.add(AgentExecution(
            incident_id=incident.id,
            agent_name=name,
            status="error",
            output_json=error,
            duration_ms=duration_ms,
        ))
        return error


def orchestrate(db, incident, selected_category):
    """Run a stateful, explainable, human-controlled agent workflow.

    Agents communicate through IncidentContext. The orchestrator branches when
    the report is ambiguous, when a duplicate is likely, and when location data
    is missing. It never performs an operational dispatch.
    """
    context = IncidentContext(
        incident_id=incident.id,
        incident_code=incident.incident_code,
        description=incident.description,
        requested_category=selected_category,
        location_text=incident.location_text,
    )

    intake = _run_agent(
        db, incident, "Report Understanding Agent",
        lambda: intake_agent(incident.description, selected_category), context,
    )
    context.put("intake", intake)

    location = _run_agent(
        db, incident, "Location Extraction Agent",
        lambda: location_agent(incident.location_text), context,
    )
    context.put("location", location)

    if location.get("needs_verification"):
        context.warn("Location requires coordinator verification before field deployment.")

    incident.category = intake.get("category", "Other")
    incident.title = f"{incident.category} incident"
    incident.latitude = location.get("latitude")
    incident.longitude = location.get("longitude")

    # Persist normalized location intelligence for later map/geocoding upgrades.
    db.add(IncidentLocation(
        incident_id=incident.id,
        address=location.get("normalized"),
        landmark=location.get("normalized"),
        latitude=location.get("latitude"),
        longitude=location.get("longitude"),
        confidence=location.get("confidence", 0),
        verified=location.get("verified", False),
    ))

    severity = _run_agent(
        db, incident, "Severity Assessment Agent",
        lambda: severity_agent(incident.description, incident.category), context,
    )
    context.put("severity", severity)
    incident.severity = severity.get("severity", "Medium")
    incident.severity_score = severity.get("score", 25)

    incidents = db.query(type(incident)).filter(type(incident).id != incident.id).all()
    duplicates = _run_agent(
        db, incident, "Duplicate Detection Agent",
        lambda: {"matches": duplicate_agent(
            incident.description, incidents, location=location, category=incident.category
        )}, context,
    )
    duplicate_matches = duplicates.get("matches", [])
    context.put("duplicates", duplicate_matches)
    if duplicate_matches and duplicate_matches[0]["score"] >= 0.75:
        context.warn("A strong duplicate signal was detected; coordinator review is required before additional operational action.")

    explanation = _run_agent(
        db, incident, "AI Explanation Agent",
        lambda: explain_incident(
            category=incident.category,
            description=incident.description,
            severity=severity,
            intake=intake,
        ), context,
    )
    context.put("explanation", explanation)
    incident.ai_summary = explanation.get("summary", "")
    incident.ai_explanation = explanation

    # Resource matching is still performed for operationally relevant incidents;
    # low-severity incidents get a lighter plan without automatic dispatch.
    resources = db.query(Resource).all()
    recommendations = _run_agent(
        db, incident, "Resource Matching Agent",
        lambda: {"recommendations": rank_resources(incident, resources)}, context,
    )
    recommendations = recommendations.get("recommendations", [])
    context.put("resources", recommendations)

    response_plan = _run_agent(
        db, incident, "Response Planning Agent",
        lambda: response_planning_agent(
            incident,
            recommendations,
            severity=severity,
            location=location,
            duplicates=duplicate_matches,
        ), context,
    )
    context.put("response_plan", response_plan)

    # Dynamic escalation agent: only appears when the evidence warrants it.
    if incident.severity in {"Critical", "High"} or duplicate_matches:
        escalation = {
            "decision": "human_review_required",
            "reason": "High operational risk or duplicate uncertainty requires coordinator review.",
            "automatic_dispatch": False,
        }
        context.put("escalation", escalation)
        _run_agent(
            db, incident, "Human Review Gate Agent",
            lambda: escalation, context,
        )

    final_snapshot = context.snapshot()
    incident.ai_explanation = {
        **(incident.ai_explanation or {}),
        "agent_context": final_snapshot,
        "warnings": context.warnings,
    }

    return {
        "intake": intake,
        "location": location,
        "severity": severity,
        "duplicates": duplicate_matches,
        "explanation": explanation,
        "resource_recommendations": recommendations,
        "response_plan": response_plan,
        "warnings": context.warnings,
        "agent_trace": context.agent_trace,
    }
