import json, time, uuid
from datetime import datetime

def log_tool_call(tool_name, arguments, result, duration_ms, error=None):
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "tool_name": tool_name,
        "arguments": arguments,
        "success": error is None,
        "duration_ms": round(duration_ms, 2),
        "error": str(error) if error else None,
        "result_size_chars": len(str(result))
    }
    with open("logs/tool_calls.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")