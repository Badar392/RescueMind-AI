"""Safe location extraction helpers.

This module deliberately never invents coordinates. Explicit coordinates are
accepted; text is normalized into useful location metadata and flagged for
verification. A real geocoder can be plugged in later without changing the
agent contract.
"""
import re


COORDINATE_RE = re.compile(
    r"(?P<lat>-?\d{1,2}(?:\.\d+)?)\s*,\s*(?P<lon>-?\d{1,3}(?:\.\d+)?)"
)


def extract_location(location: str | None) -> dict:
    raw = (location or "").strip()
    if not raw:
        return {
            "raw": None,
            "normalized": None,
            "latitude": None,
            "longitude": None,
            "confidence": 0.0,
            "verified": False,
            "source": "missing",
            "needs_verification": True,
            "note": "No location supplied.",
        }

    match = COORDINATE_RE.search(raw)
    if match:
        lat = float(match.group("lat"))
        lon = float(match.group("lon"))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return {
                "raw": raw,
                "normalized": f"{lat:.6f}, {lon:.6f}",
                "latitude": lat,
                "longitude": lon,
                "confidence": 1.0,
                "verified": False,
                "source": "reporter_coordinates",
                "needs_verification": False,
                "note": "Coordinates were explicitly supplied by the reporter.",
            }

    normalized = re.sub(r"\s+", " ", raw).strip(" ,")
    return {
        "raw": raw,
        "normalized": normalized,
        "latitude": None,
        "longitude": None,
        "confidence": 0.45,
        "verified": False,
        "source": "reporter_text",
        "needs_verification": True,
        "note": "Text location extracted; coordinates were not invented.",
    }
