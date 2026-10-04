"""Optional LLM explanation/enrichment layer.

The backend can run without Streamlit or a configured LLM. When no provider is
available, transparent deterministic explanations are returned instead.
"""
import json
from functools import lru_cache

try:
    import streamlit as st
except ImportError:  # FastAPI/backend execution
    st = None

from utils.config import settings


@lru_cache(maxsize=4)
def _get_groq_client_cached(api_key):
    if not api_key:
        return None
    try:
        from groq import Groq
        return Groq(api_key=api_key)
    except Exception:
        return None


def get_groq_client(api_key):
    if st is not None:
        try:
            @st.cache_resource(show_spinner=False)
            def _client(key):
                return _get_groq_client_cached(key)
            return _client(api_key)
        except Exception:
            pass
    return _get_groq_client_cached(api_key)


def explain_incident(category, description, severity, intake):
    client = get_groq_client(settings.groq_api_key)

    if client is None:
        return {
            "summary": f"Reported {category.lower()} incident assessed as {severity['severity']} using transparent prototype rules.",
            "detected": severity["supporting_evidence"],
            "missing": list(dict.fromkeys(intake["missing_information"] + severity["missing_information"])),
            "reasoning": "The local deterministic assessment was used because no AI provider is configured.",
            "human_verification": True,
            "provider": "Local rules",
        }

    prompt = f"""
You are an explanation component in RescueMind AI, a simulated emergency coordination prototype.

Return JSON only with:
summary, detected, missing, reasoning, human_verification.

Never claim the report is verified.
Never dispatch resources.
Never give medical treatment instructions.
Keep the explanation concise and evidence-based.

Category: {category}
Description: {description}
Rule-based severity: {severity['severity']} ({severity['score']}/100)
Evidence: {severity['supporting_evidence']}
Missing: {severity['missing_information']}
"""

    try:
        response = client.chat.completions.create(
            model=settings.groq_model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Provide transparent explanations for an emergency operations prototype.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        data = json.loads(response.choices[0].message.content)
        data["human_verification"] = True
        data["provider"] = "Groq"
        return data
    except Exception as exc:
        return {
            "summary": "AI explanation failed; deterministic assessment remains available.",
            "detected": severity["supporting_evidence"],
            "missing": severity["missing_information"],
            "reasoning": f"Provider error: {type(exc).__name__}",
            "human_verification": True,
            "provider": "Fallback",
        }


def analyze_image(image_bytes, filename, incident_description=""):
    """Optional vision agent. Returns transparent fallback when no vision provider is configured."""
    client = get_groq_client(settings.groq_api_key)
    if client is None or not image_bytes:
        return {"status":"unavailable","confidence":0.0,"findings":[],"note":"Vision provider unavailable; image metadata can still be retained for human review."}
    import base64, json
    mime = "image/jpeg" if str(filename).lower().endswith(('.jpg','.jpeg')) else "image/png"
    data_url = f"data:{mime};base64,{base64.b64encode(image_bytes).decode('utf-8')}"
    prompt = f"""Analyze this emergency-scene image for RescueMind AI. Do not identify people. Return JSON only with findings (array), hazards (array), possible_category, confidence (0-1), and uncertainty (array). Never claim the scene is verified and never recommend medical treatment. Report only visible evidence. Text report: {incident_description}"""
    try:
        response = client.chat.completions.create(model=settings.groq_vision_model, temperature=0.1, response_format={"type":"json_object"}, messages=[{"role":"user","content":[{"type":"text","text":prompt},{"type":"image_url","image_url":{"url":data_url}}]}])
        data=json.loads(response.choices[0].message.content)
        data["status"]="success"; data["provider"]="Groq Vision"
        return data
    except Exception as exc:
        return {"status":"error","confidence":0.0,"findings":[],"uncertainty":[f"Vision analysis failed: {type(exc).__name__}"],"provider":"Fallback"}

def _friendly_voice_error(exc):
    code = getattr(exc, "status_code", None)
    text = str(exc)
    if code == 403 or "Access denied" in text:
        return "Groq blocked this network/region (HTTP 403). This is not an API-key problem; try another network or hosting region."
    if code == 401:
        return "GROQ_API_KEY was rejected (HTTP 401). Check the key."
    if code == 429:
        return "Groq rate limit reached (HTTP 429). Try again shortly."
    return text[:200]


def _transcribe_fallback(audio_bytes):
    """Key-free fallback (Google Web Speech via SpeechRecognition). Works for WAV audio only."""
    import io
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
        audio = recognizer.record(source)
    for lang in ("en-US", "ur-PK"):
        try:
            text = recognizer.recognize_google(audio, language=lang)
            if text:
                return text
        except sr.UnknownValueError:
            continue
    return ""


def transcribe_audio(audio_bytes, filename):
    """Voice transcription: Groq Whisper first, then a key-free fallback if Groq is unavailable/blocked."""
    if not audio_bytes:
        return {"status": "unavailable", "text": "", "confidence": 0.0, "note": "No audio data was received."}
    problem = ""
    client = get_groq_client(settings.groq_api_key)
    if client is None:
        problem = "GROQ_API_KEY is missing. Add it to .env or .streamlit/secrets.toml."
    else:
        try:
            result = client.audio.transcriptions.create(model=settings.groq_transcription_model, file=(filename or "report.wav", audio_bytes))
            text = getattr(result, "text", "") or ""
            return {"status": "success", "text": text, "confidence": 0.90 if text else 0.0, "provider": "Groq Whisper"}
        except Exception as exc:
            problem = _friendly_voice_error(exc)
    # Fallback path
    if audio_bytes[:4] == b"RIFF":
        try:
            text = _transcribe_fallback(audio_bytes)
            if text:
                return {"status": "success", "text": text, "confidence": 0.75, "provider": "Google Web Speech (fallback)",
                        "note": f"Primary provider unavailable: {problem}"}
            problem += " Fallback heard no clear speech."
        except Exception as exc:
            problem += f" Fallback also failed ({type(exc).__name__})."
    else:
        problem += " (Fallback supports WAV recordings only.)"
    return {"status": "error", "text": "", "confidence": 0.0, "error": "TranscriptionUnavailable", "note": problem}
