from datetime import datetime, timezone
from sqlalchemy import (
    String, Text, Integer, Float, DateTime, ForeignKey,
    Boolean, JSON, Index
)
from sqlalchemy.orm import Mapped, mapped_column
from utils.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(40), default="coordinator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class EmergencyReport(Base):
    __tablename__ = "emergency_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    report_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(40))
    reported_location: Mapped[str | None] = mapped_column(String(255))
    image_name: Mapped[str | None] = mapped_column(String(255))
    incident_id: Mapped[int | None] = mapped_column(ForeignKey("incidents.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[int] = mapped_column(primary_key=True)
    incident_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(180))
    category: Mapped[str] = mapped_column(String(40), index=True)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="Pending", index=True)
    severity: Mapped[str] = mapped_column(String(20), default="Medium", index=True)
    severity_score: Mapped[int] = mapped_column(Integer, default=25)
    location_text: Mapped[str | None] = mapped_column(String(255))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_explanation: Mapped[dict | None] = mapped_column(JSON)
    human_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class IncidentLocation(Base):
    __tablename__ = "incident_locations"
    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    address: Mapped[str | None] = mapped_column(String(255))
    landmark: Mapped[str | None] = mapped_column(String(255))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)

class IncidentEvidence(Base):
    __tablename__ = "incident_evidence"
    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    evidence_type: Mapped[str] = mapped_column(String(30))
    file_name: Mapped[str | None] = mapped_column(String(255))
    extracted_text: Mapped[str | None] = mapped_column(Text)

class Resource(Base):
    __tablename__ = "resources"
    id: Mapped[int] = mapped_column(primary_key=True)
    resource_code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    resource_type: Mapped[str] = mapped_column(String(50), index=True)
    capacity: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default="Available", index=True)
    location: Mapped[str] = mapped_column(String(150))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ResourceAssignment(Base):
    __tablename__ = "resource_assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="Proposed")
    approved_by: Mapped[str | None] = mapped_column(String(120))
    rationale: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class AgentExecution(Base):
    __tablename__ = "agent_executions"
    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int | None] = mapped_column(ForeignKey("incidents.id"), index=True)
    agent_name: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(30))
    output_json: Mapped[dict | None] = mapped_column(JSON)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class IncidentHistory(Base):
    __tablename__ = "incident_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    old_status: Mapped[str | None] = mapped_column(String(40))
    new_status: Mapped[str] = mapped_column(String(40))
    actor: Mapped[str] = mapped_column(String(120))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    actor: Mapped[str] = mapped_column(String(120))
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[str | None] = mapped_column(String(50))
    details: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

Index("ix_incident_coordinates", Incident.latitude, Incident.longitude)

class EventRecord(Base):
    """Durable event envelope used by the v2.2 event-driven monitor."""
    __tablename__ = "event_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    incident_id: Mapped[int | None] = mapped_column(ForeignKey("incidents.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    payload: Mapped[dict | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
