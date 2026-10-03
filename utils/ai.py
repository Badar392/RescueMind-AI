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
