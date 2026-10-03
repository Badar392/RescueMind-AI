"""Resource optimization for RescueMind AI v2.3.

Produces explainable recommendations only. It never dispatches a resource.
"""
from __future__ import annotations
from collections import defaultdict
from utils.resource_matcher import _distance_km, REQUIRED_TYPES


def _demand_score(incident) -> float:
    return {"Critical": 1.0, "High": 0.85, "Medium": 0.55, "Low": 0.3}.get(incident.severity, 0.5)


def _resource_fit(incident, resource) -> tuple[float, list[str]]:
    required = REQUIRED_TYPES.get(incident.category, REQUIRED_TYPES["Other"])
    reasons = []
    if resource.resource_type in required:
        reasons.append("capability match")
        capability = 1.0
    else:
        capability = 0.0
    if resource.status == "Available":
        availability = 1.0
        reasons.append("currently available")
    else:
        availability = 0.0
    distance = _distance_km(incident.latitude, incident.longitude, resource.latitude, resource.longitude)
    proximity = 0.5 if distance is None else max(0.0, 1.0 - min(distance / 50.0, 1.0))
    if distance is not None:
        reasons.append(f"{distance:.1f} km away")
    else:
        reasons.append("distance unavailable")
    capacity = min(max(resource.capacity, 1) / 10.0, 1.0)
    score = (capability * 0.45 + availability * 0.20 + proximity * 0.20 + capacity * 0.15) * 100
    return score, reasons


def optimize_resources(incidents, resources, max_per_incident: int = 3) -> list[dict]:
    """Greedy, explainable allocation proposal with competition awareness."""
    open_incidents = [i for i in incidents if i.status in {"Pending", "Under Review", "Approved", "Assigned", "In Progress"}]
    available = [r for r in resources if r.status == "Available"]
    demand = sorted(open_incidents, key=lambda i: (-_demand_score(i), -i.severity_score, i.id))
    competition = defaultdict(int)
    results = []

    for incident in demand:
        candidates = []
        for resource in available:
            score, reasons = _resource_fit(incident, resource)
            if score <= 0:
                continue
            adjusted = score - competition[resource.id] * 8
            candidates.append((adjusted, resource, reasons))
        candidates.sort(key=lambda x: (-x[0], x[1].id))
        chosen = candidates[:max_per_incident]
        for adjusted, resource, reasons in chosen:
            competition[resource.id] += 1
            results.append({
                "incident_id": incident.id,
                "incident_code": incident.incident_code,
                "severity": incident.severity,
                "resource_id": resource.id,
                "resource_code": resource.resource_code,
                "resource_name": resource.name,
                "resource_type": resource.resource_type,
                "distance_km": _distance_km(incident.latitude, incident.longitude, resource.latitude, resource.longitude),
                "base_score": round(adjusted + competition[resource.id] * 8, 2),
                "optimized_score": round(adjusted, 2),
                "competition_penalty": (competition[resource.id] - 1) * 8,
                "reasons": reasons,
                "decision": "recommend_for_human_review",
                "automatic_dispatch": False,
            })
    return results
