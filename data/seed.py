import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.database import SessionLocal, Equipment, SensorReading, MaintenanceEvent, FlaggedAnomaly
from datetime import datetime, timedelta
import random
import uuid

def seed():
    db = SessionLocal()

    # Clear existing data
    db.query(FlaggedAnomaly).delete()
    db.query(MaintenanceEvent).delete()
    db.query(SensorReading).delete()
    db.query(Equipment).delete()
    db.commit()

    # 10 machines
    machines = [
        Equipment(equipment_id="E001", name="CNC Mill A",        location="Floor 1", status="active"),
        Equipment(equipment_id="E002", name="Conveyor Belt B",   location="Floor 1", status="active"),
        Equipment(equipment_id="E003", name="Hydraulic Press C", location="Floor 2", status="active"),
        Equipment(equipment_id="E004", name="Lathe Machine D",   location="Floor 2", status="active"),
        Equipment(equipment_id="E005", name="Welding Robot E",   location="Floor 3", status="active"),
        Equipment(equipment_id="E006", name="Pump Station F",    location="Floor 3", status="active"),
        Equipment(equipment_id="E007", name="Compressor G",      location="Floor 1", status="maintenance"),
        Equipment(equipment_id="E008", name="Cutting Machine H", location="Floor 2", status="active"),
        Equipment(equipment_id="E009", name="Drill Press I",     location="Floor 3", status="active"),
        Equipment(equipment_id="E010", name="Grinder J",         location="Floor 1", status="active"),
    ]
    db.add_all(machines)
    db.commit()
    print(f"Inserted {len(machines)} machines")

    # Thresholds — E004 and E007 will have anomalous readings
    thresholds = {
        "temperature": 80.0,
        "vibration":   5.0,
        "pressure":    100.0,
    }

    readings = []
    now = datetime.utcnow()

    for machine in machines:
        for day_offset in range(30):
            timestamp = now - timedelta(days=day_offset)
            for reading_type in ["temperature", "vibration", "pressure"]:

                # E004 — high temperature (anomalous)
                if machine.equipment_id == "E004" and reading_type == "temperature":
                    value = round(random.uniform(88.0, 97.0), 2)

                # E007 — high vibration (anomalous)
                elif machine.equipment_id == "E007" and reading_type == "vibration":
                    value = round(random.uniform(6.5, 9.0), 2)

                # All others — normal range
                else:
                    base = {"temperature": 65.0, "vibration": 2.5, "pressure": 75.0}
                    value = round(random.uniform(base[reading_type] * 0.85, base[reading_type] * 1.1), 2)

                readings.append(SensorReading(
                    reading_id=str(uuid.uuid4()),
                    equipment_id=machine.equipment_id,
                    reading_type=reading_type,
                    value=value,
                    timestamp=timestamp,
                ))

    db.add_all(readings)
    db.commit()
    print(f"Inserted {len(readings)} sensor readings")

    # Maintenance history — E007 last serviced 90 days ago (overdue)
    events = [
        MaintenanceEvent(event_id=str(uuid.uuid4()), equipment_id="E001", event_type="inspection",   description="Routine inspection, all systems normal",          technician="John Smith",  timestamp=now - timedelta(days=15)),
        MaintenanceEvent(event_id=str(uuid.uuid4()), equipment_id="E002", event_type="repair",       description="Replaced worn conveyor belt segment",             technician="Maria Lopez", timestamp=now - timedelta(days=8)),
        MaintenanceEvent(event_id=str(uuid.uuid4()), equipment_id="E003", event_type="inspection",   description="Hydraulic fluid topped up, seals checked",        technician="John Smith",  timestamp=now - timedelta(days=20)),
        MaintenanceEvent(event_id=str(uuid.uuid4()), equipment_id="E004", event_type="inspection",   description="Cooling system checked — minor blockage found",   technician="Tom Davis",   timestamp=now - timedelta(days=5)),
        MaintenanceEvent(event_id=str(uuid.uuid4()), equipment_id="E005", event_type="replacement",  description="Welding tip replaced, calibration done",          technician="Maria Lopez", timestamp=now - timedelta(days=12)),
        MaintenanceEvent(event_id=str(uuid.uuid4()), equipment_id="E006", event_type="inspection",   description="Pump seals inspected, no issues found",           technician="Tom Davis",   timestamp=now - timedelta(days=3)),
        MaintenanceEvent(event_id=str(uuid.uuid4()), equipment_id="E007", event_type="repair",       description="Bearing replacement — vibration issue unresolved", technician="John Smith",  timestamp=now - timedelta(days=90)),
        MaintenanceEvent(event_id=str(uuid.uuid4()), equipment_id="E008", event_type="inspection",   description="Blade sharpness checked, within tolerance",       technician="Maria Lopez", timestamp=now - timedelta(days=18)),
        MaintenanceEvent(event_id=str(uuid.uuid4()), equipment_id="E009", event_type="replacement",  description="Drill bit replaced, alignment recalibrated",      technician="Tom Davis",   timestamp=now - timedelta(days=7)),
        MaintenanceEvent(event_id=str(uuid.uuid4()), equipment_id="E010", event_type="inspection",   description="Grinding wheel inspected, no cracks found",       technician="John Smith",  timestamp=now - timedelta(days=25)),
    ]
    db.add_all(events)
    db.commit()
    print(f"Inserted {len(events)} maintenance events")

    db.close()
    print("Seed complete.")

if __name__ == "__main__":
    seed()