import time
import uuid
from datetime import datetime, timedelta, timezone
from server.database import SessionLocal, Equipment, SensorReading, MaintenanceEvent, FlaggedAnomaly
from server.observability import log_tool_call


# ─── Tool 1: Get equipment status ────────────────────────────────────────────

async def get_equipment_status(equipment_id: str):
    start = time.time()
    try:
        db = SessionLocal()

        equipment = db.query(Equipment).filter(
            Equipment.equipment_id == equipment_id
        ).first()

        if not equipment:
            result = {"error": f"Equipment {equipment_id} not found"}
            log_tool_call("get_equipment_status", {"equipment_id": equipment_id}, result, (time.time()-start)*1000)
            db.close()
            return result

        readings = {}
        thresholds = {"temperature": 80.0, "vibration": 5.0, "pressure": 100.0}

        for reading_type in ["temperature", "vibration", "pressure"]:
            latest = db.query(SensorReading).filter(
                SensorReading.equipment_id == equipment_id,
                SensorReading.reading_type == reading_type
            ).order_by(SensorReading.timestamp.desc()).first()

            if latest:
                value = latest.value
                threshold = thresholds[reading_type]
                readings[reading_type] = {
                    "value": value,
                    "threshold": threshold,
                    "status": "ANOMALY" if value > threshold else "normal",
                    "timestamp": latest.timestamp.isoformat()
                }

        result = {
            "equipment_id": equipment_id,
            "name": equipment.name,
            "location": equipment.location,
            "status": equipment.status,
            "sensor_readings": readings,
            "has_anomaly": any(
                r["status"] == "ANOMALY" for r in readings.values()
            )
        }

        db.close()
        log_tool_call("get_equipment_status", {"equipment_id": equipment_id}, result, (time.time()-start)*1000)
        return result

    except Exception as e:
        log_tool_call("get_equipment_status", {"equipment_id": equipment_id}, None, (time.time()-start)*1000, error=e)
        raise


# ─── Tool 2: Get maintenance history ─────────────────────────────────────────

async def get_maintenance_history(equipment_id: str):
    start = time.time()
    try:
        db = SessionLocal()

        equipment = db.query(Equipment).filter(
            Equipment.equipment_id == equipment_id
        ).first()

        if not equipment:
            result = {"error": f"Equipment {equipment_id} not found"}
            log_tool_call("get_maintenance_history", {"equipment_id": equipment_id}, result, (time.time()-start)*1000)
            db.close()
            return result

        events = db.query(MaintenanceEvent).filter(
            MaintenanceEvent.equipment_id == equipment_id
        ).order_by(MaintenanceEvent.timestamp.desc()).limit(5).all()

        now = datetime.now(timezone.utc)
        last_event = events[0] if events else None

        if last_event:
            last_ts = last_event.timestamp
            if last_ts.tzinfo is None:
                last_ts = last_ts.replace(tzinfo=timezone.utc)
            days_since = (now - last_ts).days
        else:
            days_since = None

        result = {
            "equipment_id": equipment_id,
            "name": equipment.name,
            "days_since_last_maintenance": days_since,
            "overdue": days_since is not None and days_since > 30,
            "history": [
                {
                    "event_type": e.event_type,
                    "description": e.description,
                    "technician": e.technician,
                    "date": e.timestamp.isoformat()
                }
                for e in events
            ]
        }

        db.close()
        log_tool_call("get_maintenance_history", {"equipment_id": equipment_id}, result, (time.time()-start)*1000)
        return result

    except Exception as e:
        log_tool_call("get_maintenance_history", {"equipment_id": equipment_id}, None, (time.time()-start)*1000, error=e)
        raise


# ─── Tool 3: Flag anomaly ─────────────────────────────────────────────────────

async def flag_anomaly(equipment_id: str, reading_type: str, value: float):
    start = time.time()
    try:
        db = SessionLocal()

        thresholds = {"temperature": 80.0, "vibration": 5.0, "pressure": 100.0}
        threshold = thresholds.get(reading_type, 0)

        anomaly_id = str(uuid.uuid4())

        anomaly = FlaggedAnomaly(
            anomaly_id=anomaly_id,
            equipment_id=equipment_id,
            reading_type=reading_type,
            value=value,
            threshold=threshold,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(anomaly)
        db.commit()

        result = {
            "success": True,
            "message": f"Anomaly flagged for {equipment_id}: {reading_type} = {value} (threshold: {threshold})",
            "anomaly_id": anomaly_id
        }

        db.close()
        log_tool_call("flag_anomaly", {"equipment_id": equipment_id, "reading_type": reading_type, "value": value}, result, (time.time()-start)*1000)
        return result

    except Exception as e:
        log_tool_call("flag_anomaly", {"equipment_id": equipment_id, "reading_type": reading_type, "value": value}, None, (time.time()-start)*1000, error=e)
        raise

# ─── Tool 4: Get production metrics ──────────────────────────────────────────

async def get_production_metrics(start_date: str, end_date: str):
    start = time.time()
    try:
        db = SessionLocal()

        start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        end_dt   = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)

        equipment_list = db.query(Equipment).all()
        metrics = []

        for eq in equipment_list:
            readings = db.query(SensorReading).filter(
                SensorReading.equipment_id == eq.equipment_id,
                SensorReading.timestamp >= start_dt,
                SensorReading.timestamp <= end_dt
            ).all()

            if not readings:
                continue

            by_type = {}
            for r in readings:
                by_type.setdefault(r.reading_type, []).append(r.value)

            summary = {}
            for rtype, values in by_type.items():
                summary[rtype] = {
                    "avg": round(sum(values) / len(values), 2),
                    "max": round(max(values), 2),
                    "min": round(min(values), 2)
                }

            metrics.append({
                "equipment_id": eq.equipment_id,
                "name": eq.name,
                "location": eq.location,
                "reading_count": len(readings),
                "metrics": summary
            })

        db.close()

        result = {
            "period": {"start": start_date, "end": end_date},
            "equipment_count": len(metrics),
            "data": metrics
        }

        log_tool_call("get_production_metrics", {"start_date": start_date, "end_date": end_date}, result, (time.time()-start)*1000)
        return result

    except Exception as e:
        log_tool_call("get_production_metrics", {"start_date": start_date, "end_date": end_date}, None, (time.time()-start)*1000, error=e)
        raise


# ─── Tool 5: Query knowledge base (RAG) ──────────────────────────────────────

async def query_knowledge_base(question: str):
    start = time.time()
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        ef = embedding_functions.DefaultEmbeddingFunction()

        try:
            collection = chroma_client.get_collection(
                name="equipment_manuals",
                embedding_function=ef
            )
        except Exception:
            result = {
                "answer": "Knowledge base not yet populated. Add .txt files to data/manuals/ and run the indexing script.",
                "sources": []
            }
            log_tool_call("query_knowledge_base", {"question": question}, result, (time.time()-start)*1000)
            return result

        results = collection.query(query_texts=[question], n_results=3)

        sources = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                sources.append({
                    "content": doc,
                    "source": results["metadatas"][0][i].get("source", "unknown") if results["metadatas"] else "unknown"
                })

        result = {
            "question": question,
            "sources_found": len(sources),
            "results": sources
        }

        log_tool_call("query_knowledge_base", {"question": question}, result, (time.time()-start)*1000)
        return result

    except Exception as e:
        log_tool_call("query_knowledge_base", {"question": question}, None, (time.time()-start)*1000, error=e)
        raise