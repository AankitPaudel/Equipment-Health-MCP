from fastapi import FastAPI
from server.tools import (
    get_equipment_status,
    get_maintenance_history,
    flag_anomaly,
    get_production_metrics,
    query_knowledge_base
)

app = FastAPI(title="Equipment Health API", version="1.0.0")

@app.get("/equipment/{equipment_id}/status")
async def equipment_status(equipment_id: str):
    return await get_equipment_status(equipment_id)

@app.get("/equipment/{equipment_id}/maintenance")
async def maintenance_history(equipment_id: str):
    return await get_maintenance_history(equipment_id)

@app.post("/equipment/{equipment_id}/anomaly")
async def flag_equipment_anomaly(equipment_id: str, reading_type: str, value: float):
    return await flag_anomaly(equipment_id, reading_type, value)

@app.get("/metrics")
async def production_metrics(start_date: str, end_date: str):
    return await get_production_metrics(start_date, end_date)

@app.get("/knowledge")
async def knowledge_base(question: str):
    return await query_knowledge_base(question)

@app.get("/health")
async def health():
    return {"status": "ok"}