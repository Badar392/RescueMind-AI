# 🚨 RescueMind AI

RescueMind AI is a human-controlled emergency intelligence and simulated resource coordination prototype.

The current architecture uses a FastAPI service boundary, a stateful multi-agent orchestrator, a shared incident context, explainable resource ranking, response planning, and a Streamlit coordinator dashboard.

> **Safety:** This is a prototype. AI output is unverified decision support. The system never automatically dispatches real emergency resources.

## Architecture

```text
Citizen / Web / Mobile
        │
        ▼
FastAPI Backend (backend/main.py)
        │
        ▼
AI Orchestrator (utils/agents.py)
        │
        ▼
Shared Incident Context (utils/agent_context.py)
        │
 ┌──────┼─────────┬───────────────┐
 ▼      ▼         ▼               ▼
Report Location Duplicate      Severity
Agent  Agent     Agent           Agent
 │       │         │               │
 └───────┴─────────┴───────────────┘
                 │
                 ▼
          AI Explanation Agent
                 │
                 ▼
        Resource Matching Agent
                 │
                 ▼
        Response Planning Agent
                 │
          ┌──────┴──────┐
          ▼             ▼
   Human Review Gate   Audit/Trace
          │
          ▼
 Streamlit Coordinator UI
          │
          ▼
 Status + Resource Tracking
```

## What changed in the intelligent-agent upgrade

- **Shared Incident Context:** agents now communicate through a common structured state instead of isolated function results.
- **Agent execution trace:** every agent records its status, duration, confidence where available, and JSON output.
- **Dynamic human-review gate:** high/critical incidents and strong duplicate signals receive an explicit review-gate step.
- **Improved duplicate detection:** combines text similarity, category similarity, and geographic proximity when coordinates are available.
- **Ranked resource matching:** available resources are scored using capability, availability, capacity, and distance when known.
- **Response planning:** generates actions, risks, missing information, candidate resources, and an explicit no-auto-dispatch rule.
- **Safe location extraction:** accepts reporter coordinates but never invents coordinates from text. Text locations are marked for verification.
- **Incident location records:** normalized location intelligence is stored in `IncidentLocation`.
- **Agent Timeline UI:** the Incident Management page now exposes the agent execution sequence and each agent's output.
- **Agent Timeline API:** `GET /api/v1/incidents/{incident_id}/agents` exposes the same trace to other clients.
- **Backend-safe AI module:** `utils/ai.py` can run without importing Streamlit, so FastAPI can use the same intelligence layer.

## Project structure

```text
RescueMind-AI/
├── app.py
├── backend/
│   ├── __init__.py
│   └── main.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── utils/
│   ├── __init__.py
│   ├── agents.py                 # multi-agent orchestrator
│   ├── agent_context.py          # NEW: shared agent state
│   ├── ai.py                     # optional Groq explanation layer
│   ├── config.py
│   ├── data.py
│   ├── database.py
│   ├── location_service.py       # NEW: safe location extraction
│   ├── models.py
│   ├── pages.py                  # updated incident intelligence UI
│   ├── resource_matcher.py       # NEW: ranked resource matching
│   ├── response_planner.py       # NEW: transparent response plans
│   ├── seed.py
│   ├── services.py
│   └── ui.py
└── data/
    └── simulated_emergencies.csv
```

## Run locally

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the coordinator UI:

```powershell
streamlit run app.py
```

Run the FastAPI backend in another terminal:

```powershell
uvicorn backend.main:app --reload
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET /api/v1/health
```

Agent timeline:

```text
GET /api/v1/incidents/{incident_id}/agents
```

## LLM configuration

The application works without an API key using deterministic fallback logic.

Optional Streamlit secrets:

```toml
GROQ_API_KEY = "your_real_groq_key"
GROQ_MODEL = "openai/gpt-oss-120b"
```

Never commit real API keys.
