"""RescueMind AI FastAPI backend.

The API is the service boundary between citizen/report clients and the
AI orchestration + database layer. Streamlit remains the human approval UI.
"""
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import desc

from utils.database import SessionLocal, init_db
from utils.models import Incident, Resource
from utils.seed import seed_database
from utils.services import change_status, create_incident, propose_resource
from utils.agents import orchestrate

app = FastAPI(
    title="RescueMind AI API",
    version="1.0.0",
    description="Emergency intelligence and human-controlled resource coordination API.",
)


@app.on_event("startup")
def startup() -> None:
    init_db()
    seed_database()


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


def _process_report(db, description: str, category: str, location: Optional[str], image_name: Optional[str]):
    if len(description.strip()) < 10:
        raise HTTPException(status_code=422, detail="Description must contain at least 10 characters.")

    incident, report = create_incident(
        db,
        description.strip(),
        "Other" if category == "Auto Detect" else category,
        location,
        image_name,
    )
    result = orchestrate(db, incident, category)
    db.commit()
    db.refresh(incident)
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
        return {"status": "Proposed", "incident_id": incident.id, "resource_id": resource.id, "rationale": rationale}
    finally:
        db.close()
