# RescueMind AI — Version 2.2

## Event-Driven Incident Monitoring

Version 2.2 extends v2.1 with a lightweight event-driven runtime. New reports and operational updates are published to a durable event stream, processed by a background worker, and recorded for auditability.

### What is new
- Event bus with a durable `event_records` table.
- Background event worker for asynchronous agent reactions.
- Continuous Monitoring Agent that re-checks severity, resource candidates and response plans.
- Event-driven incident refresh endpoint.
- External event endpoint for integration with mobile/IoT/dispatch systems.
- Monitoring status endpoint.
- Streamlit **Live Monitoring** page showing the event stream.
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

### Test v2.2

1. Submit an emergency report.
2. Open **Live Monitoring** in Streamlit.
3. Watch the `incident.created` event move through the stream.
4. Call the incident refresh endpoint to create an `incident.updated` event.
5. Observe a new Continuous Monitoring Agent execution in **AI Activity**.
6. Review the recommendation; no resource is dispatched automatically.

### Important
The event worker is intentionally in-process for a student/demo deployment. For production, replace it with Redis Streams, RabbitMQ, Kafka, or another durable message broker and run workers as separate services.
