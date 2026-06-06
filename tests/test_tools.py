import pytest
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.index_manuals import index_manuals
from server.database import init_db
from server.tools import get_equipment_status, get_maintenance_history, flag_anomaly, query_knowledge_base

def setup_module(module):
    init_db()
    index_manuals()

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

def test_query_knowledge_base_returns_manual_sources():
    result = asyncio.run(query_knowledge_base("high vibration on compressor"))
    assert result["sources_found"] > 0
    assert any(source["source"] == "compressor.txt" for source in result["results"])