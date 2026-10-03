"""Explainable resource matching and ranking."""
from math import radians, sin, cos, sqrt, atan2


REQUIRED_TYPES = {
    "Flood": ["Rescue Boat", "Rescue Team", "Medical Unit"],
    "Earthquake": ["Rescue Team", "Medical Unit", "Supplies"],
    "Fire": ["Rescue Team", "Ambulance"],
    "Road Accident": ["Ambulance", "Rescue Team"],
    "Medical Emergency": ["Ambulance", "Medical Unit"],
    "Other": ["Rescue Team"],
}


def _distance_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None
    earth_radius = 6371.0
    p1, p2 = radians(lat1), radians(lat2)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(p1) * cos(p2) * sin(dlon / 2) ** 2
    return earth_radius * 2 * atan2(sqrt(a), sqrt(1 - a))


def rank_resources(incident, resources):
    required = REQUIRED_TYPES.get(incident.category, REQUIRED_TYPES["Other"])
    candidates = []

    for resource in resources:
        if resource.status != "Available" or resource.resource_type not in required:
            continue

        distance = _distance_km(
            incident.latitude, incident.longitude,
            resource.latitude, resource.longitude,
        )
        capability = 1.0
        availability = 1.0
        capacity_bonus = min(max(resource.capacity, 1) / 10.0, 1.0)
        distance_score = 0.5 if distance is None else max(0.0, 1.0 - min(distance / 50.0, 1.0))

        score = round((capability * 0.55 + availability * 0.20 + capacity_bonus * 0.10 + distance_score * 0.15) * 100)
        reason_parts = [f"{resource.resource_type} matches the incident category"]
        if distance is not None:
            reason_parts.append(f"approximately {distance:.1f} km from incident")
        else:
            reason_parts.append("distance unavailable; coordinator should verify proximity")

        candidates.append({
            "resource_id": resource.id,
            "resource_code": resource.resource_code,
            "name": resource.name,
            "type": resource.resource_type,
            "capacity": resource.capacity,
            "status": resource.status,
            "distance_km": round(distance, 2) if distance is not None else None,
            "match_score": score,
            "reason": "; ".join(reason_parts) + ".",
        })

    candidates.sort(key=lambda x: (-x["match_score"], x["distance_km"] is None, x["distance_km"] or 999999))

    # Keep the best candidate per required capability, plus any extra high-scoring options.
    selected = []
    seen_types = set()
    for candidate in candidates:
        if candidate["type"] not in seen_types or len(selected) < min(5, len(candidates)):
            selected.append(candidate)
            seen_types.add(candidate["type"])
        if len(selected) >= 5:
            break
    return selected
