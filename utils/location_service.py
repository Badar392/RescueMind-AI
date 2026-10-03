"""Location extraction + optional real geocoding.

Coordinates are never invented by the model. Explicit coordinates are trusted
as reporter-provided; text locations are optionally resolved through the
OpenStreetMap Nominatim geocoder and are always marked unverified until a
coordinator confirms them.
"""
import re
from functools import lru_cache
import requests
from utils.config import settings

COORDINATE_RE = re.compile(r"(?P<lat>-?\d{1,2}(?:\.\d+)?)\s*,\s*(?P<lon>-?\d{1,3}(?:\.\d+)?)")

@lru_cache(maxsize=128)
def geocode_text(query: str):
    if not settings.geocoding_enabled or not query:
        return None
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
            return None
        row = rows[0]
        return {
            "latitude": float(row["lat"]),
            "longitude": float(row["lon"]),
            "display_name": row.get("display_name", query),
            "source": "OpenStreetMap Nominatim",
        }
    except Exception:
        return None

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
