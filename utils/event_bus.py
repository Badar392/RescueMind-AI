"""Lightweight event-driven runtime for RescueMind v2.2.

This is intentionally dependency-light: a process-local queue handles live
work while EventRecord persists an auditable copy in the database.
"""
from __future__ import annotations

from queue import Empty, Queue
from threading import Event, Lock, Thread
from typing import Any

from utils.database import SessionLocal
from utils.models import EventRecord

_QUEUE: Queue[dict[str, Any]] = Queue()
_STOP = Event()
_STARTED = False
_LOCK = Lock()
_HANDLER = None


def publish_event(event_type: str, incident_id: int | None = None, payload: dict | None = None) -> dict:
    db = SessionLocal()
    try:
        record = EventRecord(
            event_type=event_type,
            incident_id=incident_id,
            status="queued",
            payload=payload or {},
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        event = {"id": record.id, "event_type": event_type, "incident_id": incident_id, "payload": payload or {}}
        _QUEUE.put(event)
        return event
    finally:
        db.close()


def start_worker(handler) -> None:
    global _STARTED, _HANDLER
    with _LOCK:
        if _STARTED:
            return
        _HANDLER = handler
        _STOP.clear()
        Thread(target=_worker, name="rescuemind-event-worker", daemon=True).start()
        _STARTED = True


def stop_worker() -> None:
    _STOP.set()


def _worker() -> None:
    while not _STOP.is_set():
        try:
            event = _QUEUE.get(timeout=1.0)
        except Empty:
            continue
        db = SessionLocal()
        try:
            record = db.get(EventRecord, event["id"])
            if record:
                record.status = "processing"
                db.commit()
            if _HANDLER:
                _HANDLER(event)
            if record:
                record.status = "completed"
                db.commit()
        except Exception as exc:
            if record:
                record.status = "failed"
                record.error = str(exc)[:1000]
                db.commit()
        finally:
            db.close()
            _QUEUE.task_done()
