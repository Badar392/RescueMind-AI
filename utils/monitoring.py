"""Continuous incident monitoring and event handlers for RescueMind v2.2."""
from __future__ import annotations

from datetime import datetime, timezone
from utils.database import SessionLocal
from utils.models import Incident, Resource, AgentExecution, AuditLog, ResourceOptimizationRun
from utils.resource_matcher import rank_resources
from utils.resource_optimizer import optimize_resources
from utils.response_planner import build_response_plan


def _run_monitor_agent(db, incident, output):
    db.add(AgentExecution(
        incident_id=incident.id,
        agent_name="Continuous Monitoring Agent",
        status="success",
        output_json=output,
        duration_ms=0,
    ))


def process_event(event: dict) -> None:
    """React to an event without dispatching resources automatically."""
    db = SessionLocal()
    try:
        event_type = event["event_type"]
        incident_id = event.get("incident_id")
        incident = db.get(Incident, incident_id) if incident_id else None

        if event_type == "incident.created" and incident:
            _run_monitor_agent(db, incident, {
                "decision": "monitoring_started",
                "reason": "New incident entered the live monitoring stream.",
                "human_approval_required": True,
            })

        elif event_type in {"incident.updated", "resource.updated", "monitor.tick"}:
            incidents = [incident] if incident else db.query(Incident).filter(
                Incident.status.in_(["Pending", "Under Review", "Approved", "Assigned", "In Progress"])
            ).all()
            resources = db.query(Resource).all()
            optimization = optimize_resources(incidents, resources, 3)
            db.add(ResourceOptimizationRun(trigger=event_type, summary={"recommendations": len(optimization)}))
            for current in incidents:
                if not current:
                    continue
                recommendations = rank_resources(current, resources)
                plan = build_response_plan(
                    current,
                    {"severity": current.severity, "supporting_evidence": [], "missing_information": []},
                    {"normalized": current.location_text, "needs_verification": current.latitude is None, "confidence": 0.0},
                    [],
                    recommendations,
                )
                alert = current.severity in {"High", "Critical"} and not current.human_approved
                output = {
                    "decision": "escalate_for_human_review" if alert else "continue_monitoring",
                    "severity": current.severity,
                    "severity_score": current.severity_score,
                    "top_resource_candidates": recommendations[:3],
                    "optimized_resource_candidates": [x for x in optimization if x["incident_id"] == current.id][:3],
                    "response_plan": plan,
                    "alert": alert,
                    "automatic_dispatch": False,
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                }
                _run_monitor_agent(db, current, output)
                db.add(AuditLog(
                    action="continuous_monitoring_check",
                    actor="system",
                    entity_type="incident",
                    entity_id=str(current.id),
                    details={"event_type": event_type, "alert": alert},
                ))
        db.commit()
    finally:
        db.close()
