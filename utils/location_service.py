"""Location extraction + optional real geocoding.

Coordinates are never invented by the model. Explicit coordinates are trusted
as reporter-provided; text locations are optionally resolved through the
OpenStreetMap Nominatim geocoder and are always marked unverified until a
coordinator confirms them.
"""
import re
import requests
from utils.config import settings
from functools import lru_cache

COORDINATE_RE = re.compile(r"(?P<lat>-?\d{1,2}(?:\.\d+)?)\s*,\s*(?P<lon>-?\d{1,3}(?:\.\d+)?)")

class _GeocodeTransientFailure(Exception):
    pass


@lru_cache(maxsize=128)
def _geocode_cached(query: str):
    if not settings.geocoding_enabled or not query:
        raise _GeocodeTransientFailure()
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "jsonv2", "limit": 1},
            headers={"User-Agent": settings.geocoding_user_agent},
            timeout=5,
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            raise _GeocodeTransientFailure()
        row = rows[0]
        return {
            "latitude": float(row["lat"]),
            "longitude": float(row["lon"]),
            "display_name": row.get("display_name", query),
            "source": "OpenStreetMap Nominatim",
        }
    except _GeocodeTransientFailure:
        raise
    except Exception:
        # Exceptions are deliberately not cached by functools.lru_cache.
        raise _GeocodeTransientFailure()


def geocode_text(query: str):
    if not settings.geocoding_enabled or not query:
        return None
    try:
        return _geocode_cached(query)
    except _GeocodeTransientFailure:
        return None


# Preserve the familiar cache-control API for callers/tests while ensuring
# failed lookups never enter the cache.
geocode_text.cache_clear = _geocode_cached.cache_clear
geocode_text.cache_info = _geocode_cached.cache_info

def extract_location(location: str | None) -> dict:
    raw = (location or "").strip()
    if not raw:
        return {"raw": None,"normalized": None,"latitude": None,"longitude": None,"confidence": 0.0,"verified": False,"source":"missing","needs_verification":True,"geocoded":False,"note":"No location supplied."}
    match = COORDINATE_RE.search(raw)
    if match:
        lat, lon = float(match.group("lat")), float(match.group("lon"))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return {"raw":raw,"normalized":f"{lat:.6f}, {lon:.6f}","latitude":lat,"longitude":lon,"confidence":1.0,"verified":False,"source":"reporter_coordinates","geocoded":False,"needs_verification":False,"note":"Coordinates were explicitly supplied by the reporter; coordinator confirmation is still recommended."}
    normalized = re.sub(r"\s+", " ", raw).strip(" ,")
    geo = geocode_text(normalized)
    if geo:
        return {"raw":raw,"normalized":geo["display_name"],"latitude":geo["latitude"],"longitude":geo["longitude"],"confidence":0.78,"verified":False,"source":geo["source"],"geocoded":True,"needs_verification":True,"note":"Text location was geocoded; coordinator must verify the result before field deployment."}
    return {"raw":raw,"normalized":normalized,"latitude":None,"longitude":None,"confidence":0.45,"verified":False,"source":"reporter_text","geocoded":False,"needs_verification":True,"note":"Text location extracted; no coordinates were available."}
