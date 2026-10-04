from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from utils.config import settings

class Base(DeclarativeBase):
    pass

connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine_kwargs = {
    "connect_args": connect_args,
    "pool_pre_ping": True,
}
if settings.database_url.startswith("sqlite"):
    # The API accepts concurrent reports; the default SQLAlchemy SQLite pool
    # can exhaust at modest concurrency under TestClient/worker load.
    engine_kwargs.update({"pool_size": 20, "max_overflow": 20, "pool_timeout": 30})

engine = create_engine(settings.database_url, **engine_kwargs)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)

def init_db():
    from utils.models import (
        User, EmergencyReport, Incident, IncidentLocation,
        IncidentEvidence, Resource, ResourceAssignment,
        AgentExecution, IncidentHistory, AuditLog, EventRecord, ResourceOptimizationRun
    )
    Base.metadata.create_all(engine)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
