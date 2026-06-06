from sqlalchemy import create_engine, Column, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()
Base = declarative_base()
engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(bind=engine)

class Equipment(Base):
    __tablename__ = "equipment"
    equipment_id = Column(String, primary_key=True)  # E001, E002...
    name = Column(String)
    location = Column(String)
    status = Column(String)   # "active", "maintenance", "offline"

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    reading_id = Column(String, primary_key=True)
    equipment_id = Column(String)
    reading_type = Column(String)  # "temperature", "vibration", "pressure"
    value = Column(Float)
    timestamp = Column(DateTime)

class MaintenanceEvent(Base):
    __tablename__ = "maintenance_history"
    event_id = Column(String, primary_key=True)
    equipment_id = Column(String)
    event_type = Column(String)   # "inspection", "repair", "replacement"
    description = Column(Text)
    technician = Column(String)
    timestamp = Column(DateTime)

class FlaggedAnomaly(Base):
    __tablename__ = "flagged_anomalies"
    anomaly_id = Column(String, primary_key=True)
    equipment_id = Column(String)
    reading_type = Column(String)
    value = Column(Float)
    threshold = Column(Float)
    timestamp = Column(DateTime)

def init_db():
    Base.metadata.create_all(engine)