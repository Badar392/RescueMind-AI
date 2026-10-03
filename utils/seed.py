from utils.database import SessionLocal
from utils.models import User, Resource

def seed_database():
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            db.add(User(name="Command Coordinator", role="coordinator"))

        if db.query(Resource).count() == 0:
            db.add_all([
                Resource(resource_code="AMB-001", name="Ambulance Alpha", resource_type="Ambulance", capacity=2, status="Available", location="Lahore", latitude=31.5204, longitude=74.3587),
                Resource(resource_code="RES-001", name="Rescue Team Alpha", resource_type="Rescue Team", capacity=8, status="Available", location="Lahore", latitude=31.5497, longitude=74.3436),
                Resource(resource_code="BOAT-001", name="Rescue Boat One", resource_type="Rescue Boat", capacity=10, status="Available", location="Sheikhupura", latitude=31.7131, longitude=73.9783),
                Resource(resource_code="MED-001", name="Mobile Medical Unit", resource_type="Medical Unit", capacity=12, status="Available", location="Lahore", latitude=31.4952, longitude=74.3152),
                Resource(resource_code="SUP-001", name="Emergency Supply Kit", resource_type="Supplies", capacity=100, status="Available", location="Lahore", latitude=31.5700, longitude=74.3250),
            ])
        db.commit()
    finally:
        db.close()
