# 🚨 RescueMind AI

RescueMind AI is a Python-centric Streamlit prototype for emergency intelligence and simulated resource coordination.

It processes simulated emergency reports, extracts structured information, assesses urgency using transparent rules, detects potentially duplicate reports, recommends simulated rescue resources, and keeps a human coordinator in control of operational decisions.

> **Important:** This is a hackathon prototype. AI output is not verified emergency information. The application never automatically dispatches real emergency resources.

## 1. Architecture

```text
Citizen / Web / Mobile
        │
        ▼
FastAPI Backend (backend/main.py)
        │
        ▼
AI Orchestrator (utils/agents.py)
   ┌────┼──────────────┬───────────────┐
   ▼    ▼              ▼               ▼
Report Location    Duplicate       Severity
Agent  Agent       Agent            Agent
   │      │           │               │
   └──────┴───────────┴───────────────┘
                    │
                    ▼
             Incident Database
                    │
                    ▼
           Resource Matching Agent
                    │
                    ▼
           Response Planning Agent
                    │
                    ▼
         Streamlit Human Approval UI
                    │
                    ▼
        Status + Resource Tracking
```

The application intentionally uses deterministic Python logic for structured emergency triage and matching. The LLM is used for language-level explanation rather than every workflow step.

## 2. Project structure

```text
RescueMind-AI/
├── app.py                 # Streamlit human approval dashboard
├── backend/
│   ├── __init__.py
│   └── main.py             # FastAPI backend / API boundary
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── utils/
│   ├── __init__.py
│   ├── agents.py
│   ├── ai.py
│   ├── config.py
│   ├── data.py
│   ├── database.py
│   ├── models.py
│   ├── pages.py
│   ├── seed.py
│   ├── services.py
│   └── ui.py
└── data/
    └── simulated_emergencies.csv
```

## 3. Windows installation

Open PowerShell in this project folder:

```powershell
py -3.14 -m venv .venv
```

Activate:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run:

```powershell
streamlit run app.py
```

## 4. Local secrets

Create:

```text
.streamlit/secrets.toml
```

Use:

```toml
GROQ_API_KEY = "your_real_groq_key"
GROQ_MODEL = "openai/gpt-oss-120b"
```

The real `secrets.toml` is excluded by `.gitignore`.

**Never commit API keys to GitHub.**

The application also has a deterministic fallback, so it can run without a Groq key.

## 5. Database

Local development defaults to:

```text
SQLite → data/rescuemind.db
```

For a persistent cloud deployment, use PostgreSQL and configure:

```toml
DATABASE_URL = "postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE"
```

Do not put production database credentials into GitHub.

## 6. Streamlit Community Cloud

Push the repository to GitHub first.

Then:

1. Open Streamlit Community Cloud.
2. Choose **Create app**.
3. Select your GitHub repository.
4. Select branch `main`.
5. Set the main file to:

```text
app.py
```

6. Deploy.
7. Open the app's **Settings → Secrets**.
8. Paste:

```toml
GROQ_API_KEY = "your_real_groq_key"
GROQ_MODEL = "openai/gpt-oss-120b"
```

For production persistence, also add:

```toml
DATABASE_URL = "postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE"
```

**Never upload `.streamlit/secrets.toml` to GitHub.**

## 7. GitHub commands

From the project directory:

```powershell
git init
```

```powershell
git add .
```

```powershell
git commit -m "Initial RescueMind AI Streamlit application"
```

```powershell
git branch -M main
```

Create an empty GitHub repository named:

```text
RescueMind-AI
```

Then connect it:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/RescueMind-AI.git
```

Push:

```powershell
git push -u origin main
```

Future updates:

```powershell
git add .
git commit -m "Update RescueMind AI"
git push
```

## 8. Recommended demo

Use the flood scenario:

1. Open Report Emergency.
2. Submit five similar flood reports.
3. Show structured intake.
4. Show severity evidence.
5. Show potential duplicate reports.
6. Provide explicit coordinates to demonstrate the map.
7. Open Incidents.
8. Review AI explanation.
9. Review recommended rescue resources.
10. Confirm human review.
11. Propose a simulated resource.
12. Update incident status.
13. Open Audit Trail.

## 9. Production-readiness notes

This repository is designed for clean GitHub initialization and Streamlit deployment.

Before using it outside a hackathon:

- add real authentication/authorization;
- use managed PostgreSQL;
- add database migrations with Alembic;
- add automated tests;
- add structured application logging;
- add rate limits and API error handling;
- validate uploaded files;
- add stronger duplicate-detection embeddings if required;
- integrate only verified emergency-service systems through authorized APIs;
- conduct security and privacy review.

The prototype must remain clearly separated from real emergency dispatch systems.


## 6. Run the new FastAPI backend

Keep Streamlit for the coordinator dashboard:

```powershell
streamlit run app.py
```

In a second terminal, start the API:

```powershell
uvicorn backend.main:app --reload
```

API health check:

```text
GET http://127.0.0.1:8000/api/v1/health
```

Interactive API documentation is available at `/docs`.

### Main API endpoints

- `POST /api/v1/reports` — citizen report with optional image upload
- `POST /api/v1/reports/json` — JSON report for web/mobile clients
- `GET /api/v1/incidents` — incident list
- `GET /api/v1/incidents/{id}` — incident details
- `POST /api/v1/incidents/{id}/status` — human coordinator status decision
- `GET /api/v1/resources` — resource inventory
- `POST /api/v1/incidents/{id}/resource-proposals` — propose a resource

The API never performs automatic emergency dispatch. Resource proposals and operational status changes remain human-controlled.
