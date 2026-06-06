import pytest
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.database import init_db, SessionLocal, Equipment
from server.tools import get_equipment_status, get_maintenance_history, flag_anomaly

def setup_module(module):
    init_db()

def test_get_equipment_status_not_found():
    result = asyncio.run(get_equipment_status("INVALID"))
    assert "error" in result

def test_get_equipment_status_anomaly():
    result = asyncio.run(get_equipment_status("E004"))
    assert result["equipment_id"] == "E004"
    assert result["has_anomaly"] == True

def test_get_maintenance_history_overdue():
    result = asyncio.run(get_maintenance_history("E007"))
    assert result["overdue"] == True
    assert result["days_since_last_maintenance"] >= 90

def test_flag_anomaly_success():
    result = asyncio.run(flag_anomaly("E004", "temperature", 95.0))
    assert result["success"] == True
    assert "anomaly_id" in result