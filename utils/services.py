from uuid import uuid4
from utils.models import (
    Incident, EmergencyReport, IncidentHistory,
    AuditLog, ResourceAssignment
)

def make_code(prefix):
    return f"{prefix}-{uuid4().hex[:8].upper()}"

def create_incident(db, description, category, location, image_name=None):
    incident = Incident(
        incident_code=make_code("INC"),
        title=f"{category} incident",
        category=category,
        description=description,
        location_text=location,
    )
    db.add(incident)
    db.flush()

    report = EmergencyReport(
        report_code=make_code("RPT"),
        description=description,
        category=category,
        reported_location=location,
        image_name=image_name,
        incident_id=incident.id,
    )
    db.add(report)
    db.add(IncidentHistory(
        incident_id=incident.id,
        new_status="Pending",
        actor="reporter",
        note="Emergency report received.",
    ))
    return incident, report

def change_status(db, incident, status, actor="coordinator", note=None):
    old = incident.status
    incident.status = status
    incident.human_approved = True
    db.add(IncidentHistory(
        incident_id=incident.id,
        old_status=old,
        new_status=status,
        actor=actor,
        note=note,
    ))
    db.add(AuditLog(
        action="incident_status_changed",
        actor=actor,
        entity_type="incident",
        entity_id=str(incident.id),
        details={"old_status": old, "new_status": status},
    ))

def propose_resource(db, incident_id, resource_id, rationale):
    db.add(ResourceAssignment(
        incident_id=incident_id,
        resource_id=resource_id,
        status="Proposed",
        rationale=rationale,
        approved_by="coordinator",
    ))
    db.add(AuditLog(
        action="resource_proposed",
        actor="coordinator",
        entity_type="incident",
        entity_id=str(incident_id),
        details={"resource_id": resource_id, "rationale": rationale},
    ))
