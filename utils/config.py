import os
from dataclasses import dataclass
from pathlib import Path
try:
    import streamlit as st
except ImportError:  # FastAPI can run without importing the Streamlit UI.
    st = None

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def get_setting(name: str, default=None):
    if st is not None:
        try:
            value = st.secrets.get(name)
            if value not in (None, ""):
                return value
        except Exception:
            pass
    return os.getenv(name, default)

@dataclass(frozen=True)
class Settings:
    database_url: str = get_setting(
        "DATABASE_URL",
        f"sqlite:///{DATA_DIR / 'rescuemind.db'}"
    )
    groq_api_key: str | None = get_setting("GROQ_API_KEY")
    groq_model: str = get_setting("GROQ_MODEL", "openai/gpt-oss-120b")
    groq_vision_model: str = get_setting("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
    groq_transcription_model: str = get_setting("GROQ_TRANSCRIPTION_MODEL", "whisper-large-v3-turbo")
    geocoding_enabled: bool = str(get_setting("GEOCODING_ENABLED", "true")).lower() == "true"
    geocoding_user_agent: str = get_setting("GEOCODING_USER_AGENT", "RescueMind-AI/2.1")

settings = Settings()
