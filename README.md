# RescueMind AI — Version 2.3

## Modern UI / UX (dashboard redesign)

The Streamlit front end has a new design system and a rebuilt Command Center.

### Highlights
- Bright navy / indigo theme (high contrast, vivid accents) with Inter typography and an indigo / red accent gradient.
- Sidebar with logo, icon navigation, active-page highlight and live system status card.
- Gradient hero header on every page.
- Command Center: five KPI cards, interactive dark incident map colored by severity,
  severity donut, incidents-by-category and workflow-status charts, resource readiness bar.
- Consistent styling for forms, tabs, expanders, tables, inputs and buttons.

### UI files
| File | Purpose |
|---|---|
| `utils/ui.py` | Theme/CSS, `page_hero`, `kpi_row`, `section`, `style_fig`, badges, sidebar navigation |
| `utils/pages.py` | Page layouts (`dashboard_page` redesigned with KPI cards and Plotly charts) |
| `.streamlit/config.toml` | Base theme colors and font size |

### Changelog (latest)
- **Fixed:** resource status updates (Available/Busy/Maintenance/Offline) and incident coordinator decisions were not
  saved. `st.selectbox` returns a detached copy of ORM objects, so edits to it never reached the database. The pages now
  select by ID and re-fetch the row from the live session (`db.get(...)`). Keep this pattern for any new edit forms.
- **Added:** "Initial status" field when adding a resource; confirmation message after a status change.
- **Merged:** *AI Activity* and *Live Monitoring* into one **AI Monitoring** page (Agent Activity tab + Live Event Stream tab).

### UI developer notes
- CSS is injected through `st.markdown(..., unsafe_allow_html=True)`. Streamlit's markdown parser
  ends an HTML block at a blank line, so `inject_css()` strips blank lines first. Do not remove that step,
  or the CSS will appear as text on the page.
- Charts use Plotly (`plotly>=6`); the map uses `px.scatter_map` with the `carto-darkmatter` style (no API token needed).
- Backend logic (agents, database, event bus, API) is unchanged.

### Voice reports (troubleshooting)
Voice transcription uses Groq Whisper and requires `GROQ_API_KEY` (in `.env` or `.streamlit/secrets.toml`).
If it is missing or the call fails, the report page now shows the exact reason and asks you to type the
description instead. Typed reports always work without any API key.

---

## Backend overview (v2.2)

## Event-Driven Incident Monitoring

Version 2.2 extends v2.1 with a lightweight event-driven runtime. New reports and operational updates are published to a durable event stream, processed by a background worker, and recorded for auditability.

### What is new
- Event bus with a durable `event_records` table.
- Background event worker for asynchronous agent reactions.
- Continuous Monitoring Agent that re-checks severity, resource candidates and response plans.
- Event-driven incident refresh endpoint.
- External event endpoint for integration with mobile/IoT/dispatch systems.
- Monitoring status endpoint.
- Streamlit **AI Monitoring** page: live event stream and AI agent activity in one place (two tabs).
- Automatic escalation signals for high/critical incidents that have not received human approval.
- Resource updates can trigger re-analysis without re-running the original citizen intake.
- Human approval remains mandatory; the system never dispatches a resource automatically.

### Architecture

```text
Citizen / Mobile / Voice / Image
              |
          FastAPI API
              |
       Event Publisher
              |
       Durable Event Stream
              |
      Background Event Worker
              |
     Continuous Monitoring Agent
       /          |           \
 Severity     Resource      Response
 Re-check      Re-rank       Re-plan
       \          |           /
        Human Review Gate
              |
      Coordinator Dashboard
              |
       Approved Operations
```

### New API endpoints
- `GET /api/v1/events`
- `POST /api/v1/events?event_type=incident.updated&incident_id=1`
- `POST /api/v1/incidents/{id}/refresh`
- `GET /api/v1/monitoring/status`

Existing v2.1 endpoints remain available.

### Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

In another terminal:

```bash
uvicorn backend.main:app --reload
```

FastAPI docs: `http://127.0.0.1:8000/docs`

### Test v2.3

1. Submit an emergency report.
2. Open **AI Monitoring → Live Event Stream** in Streamlit.
3. Watch the `incident.created` event move through the stream.
4. Call the incident refresh endpoint to create an `incident.updated` event.
5. Observe a new Continuous Monitoring Agent execution in **AI Monitoring → Agent Activity**.
6. Review the recommendation; no resource is dispatched automatically.

### Important
The event worker is intentionally in-process for a student/demo deployment. For production, replace it with Redis Streams, RabbitMQ, Kafka, or another durable message broker and run workers as separate services.


## v2.3 — Advanced Resource Optimization

v2.3 adds an explainable resource optimizer that considers capability, availability, capacity, geospatial proximity, incident severity, and competition between active incidents. Resource status changes trigger the event-driven monitoring layer so recommendations can be recalculated. The optimizer only produces recommendations; dispatch still requires coordinator approval.

### New endpoints
- `GET /api/v1/resources/optimization?incident_id=<id>`
- `POST /api/v1/resources/{resource_id}/status?status=Available`

### New component
- `utils/resource_optimizer.py` — explainable multi-incident resource allocation logic.
