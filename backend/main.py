"""RescueMind AI FastAPI backend.

The API is the service boundary between citizen/report clients and the
AI orchestration + database layer. Streamlit remains the human approval UI.
"""
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import desc
from datetime import datetime, timezone

from utils.database import SessionLocal, init_db
from utils.models import Incident, Resource, AgentExecution
from utils.seed import seed_database
from utils.services import change_status, create_incident, propose_resource
from utils.agents import orchestrate
from utils.ai import transcribe_audio
from utils.location_service import extract_location
from utils.event_bus import start_worker, publish_event
from utils.monitoring import process_event
from utils.resource_optimizer import optimize_resources
from utils.models import EventRecord, ResourceOptimizationRun

app = FastAPI(
    title="RescueMind AI API",
    version="2.3.0",
    description="Emergency intelligence and human-controlled resource coordination API.",
)


@app.on_event("startup")
def startup() -> None:
    init_db()
    seed_database()
    start_worker(process_event)


class ReportRequest(BaseModel):
    description: str = Field(min_length=10)
    category: str = "Auto Detect"
    location: Optional[str] = None
    image_name: Optional[str] = None


class StatusRequest(BaseModel):
    status: str
    actor: str = "coordinator"
    note: Optional[str] = None
    reviewed: bool = False


class ResourceProposalRequest(BaseModel):
    resource_id: int
    rationale: Optional[str] = None


def _incident_dict(incident: Incident) -> dict:
    return {
        "id": incident.id,
        "incident_code": incident.incident_code,
        "title": incident.title,
        "category": incident.category,
        "description": incident.description,
        "status": incident.status,
        "severity": incident.severity,
        "severity_score": incident.severity_score,
        "location": incident.location_text,
        "latitude": incident.latitude,
        "longitude": incident.longitude,
        "human_approved": incident.human_approved,
        "ai_summary": incident.ai_summary,
        "ai_explanation": incident.ai_explanation,
        "created_at": incident.created_at,
        "updated_at": incident.updated_at,
    }


def _process_report(db, description: str, category: str, location: Optional[str], image_name: Optional[str], image_bytes: bytes | None = None):
    if len(description.strip()) < 10:
        raise HTTPException(status_code=422, detail="Description must contain at least 10 characters.")

    incident, report = create_incident(
        db,
        description.strip(),
        "Other" if category == "Auto Detect" else category,
        location,
        image_name,
    )
    result = orchestrate(db, incident, category, image_bytes=image_bytes, image_name=image_name)
    db.commit()
    db.refresh(incident)
    publish_event("incident.created", incident.id, {"source": "citizen_report"})
    return incident, report, result


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok", "service": "RescueMind AI API"}


@app.post("/api/v1/reports")
async def create_report(
    description: str = Form(...),
    category: str = Form("Auto Detect"),
    location: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
):
    """Submit a citizen report using text plus optional image evidence."""
    db = SessionLocal()
    try:
        incident, report, result = _process_report(
            db,
            description,
            category,
            location,
            image.filename if image else None,
            await image.read() if image else None,
        )
        return {
            "report_code": report.report_code,
            "incident": _incident_dict(incident),
            "ai_result": result,
            "human_approval_required": True,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Report processing failed: {exc}") from exc
    finally:
        db.close()


@app.post("/api/v1/reports/json")
def create_json_report(request: ReportRequest):
    """Submit a report as JSON for web/mobile/integration clients."""
    db = SessionLocal()
    try:
        incident, report, result = _process_report(
            db,
            request.description,
            request.category,
            request.location,
            request.image_name,
        )
        return {
            "report_code": report.report_code,
            "incident": _incident_dict(incident),
            "ai_result": result,
            "human_approval_required": True,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Report processing failed: {exc}") from exc
    finally:
        db.close()


@app.post("/api/v1/reports/voice")
async def create_voice_report(
    audio: UploadFile = File(...),
    category: str = Form("Auto Detect"),
    location: Optional[str] = Form(None),
):
    """Transcribe citizen voice, then run the same agent workflow."""
    audio_bytes = await audio.read()
    transcription = transcribe_audio(audio_bytes, audio.filename)
    text = transcription.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="Voice transcription did not produce usable text.")
    db = SessionLocal()
    try:
        incident, report, result = _process_report(db, text, category, location, None)
        db.commit(); db.refresh(incident)
        return {"transcription": transcription, "report_code": report.report_code, "incident": _incident_dict(incident), "ai_result": result, "human_approval_required": True}
    except Exception as exc:
        db.rollback(); raise HTTPException(status_code=500, detail=f"Voice report processing failed: {exc}") from exc
    finally:
        db.close()


@app.get("/api/v1/incidents")
def list_incidents():
    db = SessionLocal()
    try:
        incidents = db.query(Incident).order_by(desc(Incident.id)).all()
        return {"incidents": [_incident_dict(i) for i in incidents]}
    finally:
        db.close()


@app.get("/api/v1/incidents/{incident_id}")
def get_incident(incident_id: int):
    db = SessionLocal()
    try:
        incident = db.get(Incident, incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found.")
        return _incident_dict(incident)
    finally:
        db.close()


@app.get("/api/v1/incidents/{incident_id}/agents")
def get_agent_timeline(incident_id: int):
    """Return the explainable agent execution timeline for an incident."""
    db = SessionLocal()
    try:
        incident = db.get(Incident, incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found.")
        executions = (
            db.query(AgentExecution)
            .filter(AgentExecution.incident_id == incident_id)
            .order_by(AgentExecution.id.asc())
            .all()
        )
        return {
            "incident_id": incident_id,
            "incident_code": incident.incident_code,
            "executions": [
                {
                    "id": execution.id,
                    "agent": execution.agent_name,
                    "status": execution.status,
                    "duration_ms": execution.duration_ms,
                    "output": execution.output_json,
                    "created_at": execution.created_at,
                }
                for execution in executions
            ],
        }
    finally:
        db.close()


@app.post("/api/v1/incidents/{incident_id}/status")
def update_incident_status(incident_id: int, request: StatusRequest):
    allowed = {"Pending", "Under Review", "Approved", "Assigned", "In Progress", "Resolved"}
    if request.status not in allowed:
        raise HTTPException(status_code=422, detail=f"Invalid status. Use one of: {sorted(allowed)}")
    if request.status in {"Approved", "Assigned", "In Progress", "Resolved"} and not request.reviewed:
        raise HTTPException(status_code=400, detail="Human review confirmation is required before operational status changes.")

    db = SessionLocal()
    try:
        incident = db.get(Incident, incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found.")
        change_status(db, incident, request.status, actor=request.actor, note=request.note)
        db.commit()
        db.refresh(incident)
        return {"incident": _incident_dict(incident)}
    finally:
        db.close()


@app.get("/api/v1/location/geocode")
def geocode_location(q: str):
    """Resolve a human-readable location for map display; result remains unverified."""
    if not q.strip():
        raise HTTPException(status_code=422, detail="q is required")
    return extract_location(q)



@app.get("/api/v1/events")
def list_events(limit: int = 100):
    """Return the durable event stream for observability and audit."""
    limit = max(1, min(limit, 500))
    db = SessionLocal()
    try:
        events = db.query(EventRecord).order_by(EventRecord.id.desc()).limit(limit).all()
        return {"events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "incident_id": e.incident_id,
                "status": e.status,
                "payload": e.payload or {},
                "error": e.error,
                "created_at": e.created_at,
            } for e in events
        ]}
    finally:
        db.close()


@app.post("/api/v1/events")
def create_event(event_type: str, incident_id: Optional[int] = None, payload: Optional[dict] = None):
    """Publish an external update into the event-driven orchestration layer."""
    allowed = {"incident.updated", "resource.updated", "monitor.tick"}
    if event_type not in allowed:
        raise HTTPException(status_code=422, detail=f"Unsupported event type. Use one of: {sorted(allowed)}")
    if incident_id:
        db = SessionLocal()
        try:
            if not db.get(Incident, incident_id):
                raise HTTPException(status_code=404, detail="Incident not found.")
        finally:
            db.close()
    return {"queued": True, "event": publish_event(event_type, incident_id, payload or {})}


@app.post("/api/v1/incidents/{incident_id}/refresh")
def refresh_incident_monitoring(incident_id: int):
    db = SessionLocal()
    try:
        if not db.get(Incident, incident_id):
            raise HTTPException(status_code=404, detail="Incident not found.")
    finally:
        db.close()
    return {"queued": True, "event": publish_event("incident.updated", incident_id, {"source": "coordinator_refresh"})}


@app.get("/api/v1/monitoring/status")
def monitoring_status():
    db = SessionLocal()
    try:
        queued = db.query(EventRecord).filter(EventRecord.status == "queued").count()
        processing = db.query(EventRecord).filter(EventRecord.status == "processing").count()
        completed = db.query(EventRecord).filter(EventRecord.status == "completed").count()
        failed = db.query(EventRecord).filter(EventRecord.status == "failed").count()
        return {
            "event_driven_monitoring": "online",
            "queued": queued,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "human_approval_required": True,
            "automatic_dispatch": False,
            "checked_at": datetime.now(timezone.utc),
        }
    finally:
        db.close()

@app.get("/api/v1/resources/optimization")
def resource_optimization(incident_id: Optional[int] = None, max_per_incident: int = 3):
    """Return explainable resource-allocation recommendations. No dispatch occurs."""
    db = SessionLocal()
    try:
        if incident_id:
            incident = db.get(Incident, incident_id)
            if not incident:
                raise HTTPException(status_code=404, detail="Incident not found.")
            incidents = [incident]
        else:
            incidents = db.query(Incident).filter(Incident.status.in_(["Pending", "Under Review", "Approved", "Assigned", "In Progress"])).all()
        resources = db.query(Resource).all()
        recommendations = optimize_resources(incidents, resources, max(1, min(max_per_incident, 10)))
        run = ResourceOptimizationRun(trigger="api", summary={"incident_id": incident_id, "recommendation_count": len(recommendations)})
        db.add(run); db.commit()
        return {"algorithm": "capability + availability + proximity + capacity + competition", "human_approval_required": True, "automatic_dispatch": False, "recommendations": recommendations}
    finally:
        db.close()

@app.post("/api/v1/resources/{resource_id}/status")
def update_resource_status(resource_id: int, status: str, actor: str = "coordinator"):
    allowed = {"Available", "Busy", "Maintenance", "Offline"}
    if status not in allowed:
        raise HTTPException(status_code=422, detail=f"Invalid resource status. Use one of: {sorted(allowed)}")
    db = SessionLocal()
    try:
        resource = db.get(Resource, resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found.")
        old = resource.status; resource.status = status
        db.add(AuditLog(action="resource_status_changed", actor=actor, entity_type="resource", entity_id=str(resource.id), details={"old": old, "new": status}))
        db.commit()
        publish_event("resource.updated", None, {"resource_id": resource.id, "old_status": old, "new_status": status})
        return {"resource_id": resource.id, "status": resource.status, "optimization_recheck_queued": True}
    finally:
        db.close()

@app.get("/api/v1/resources")
def list_resources():
    db = SessionLocal()
    try:
        resources = db.query(Resource).order_by(Resource.id).all()
        return {
            "resources": [
                {
                    "id": r.id,
                    "resource_code": r.resource_code,
                    "name": r.name,
                    "type": r.resource_type,
                    "capacity": r.capacity,
                    "status": r.status,
                    "location": r.location,
                    "latitude": r.latitude,
                    "longitude": r.longitude,
                }
                for r in resources
            ]
        }
    finally:
        db.close()


@app.post("/api/v1/incidents/{incident_id}/resource-proposals")
def create_resource_proposal(incident_id: int, request: ResourceProposalRequest):
    db = SessionLocal()
    try:
        incident = db.get(Incident, incident_id)
        resource = db.get(Resource, request.resource_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found.")
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found.")
        if resource.status != "Available":
            raise HTTPException(status_code=409, detail="Resource is not currently available.")

        rationale = request.rationale or f"{resource.resource_type} is relevant to the reported {incident.category.lower()} scenario."
        propose_resource(db, incident.id, resource.id, rationale)
        db.commit()
        publish_event("resource.updated", incident.id, {"resource_id": resource.id, "change": "proposal_created"})
        return {"status": "Proposed", "incident_id": incident.id, "resource_id": resource.id, "rationale": rationale}
    finally:
        db.close()
