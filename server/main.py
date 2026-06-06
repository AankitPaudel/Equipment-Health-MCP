import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types
from server import tools

server = Server("equipment-health-server")


@server.list_tools()
async def handle_list_tools():
    return [
        types.Tool(
            name="get_equipment_status",
            description="Get the latest sensor readings for a specific piece of equipment. Returns temperature, vibration, and pressure values with anomaly status flags.",
            inputSchema={
                "type": "object",
                "properties": {
                    "equipment_id": {"type": "string", "description": "Equipment ID, e.g. E001"}
                },
                "required": ["equipment_id"]
            }
        ),
        types.Tool(
            name="get_maintenance_history",
            description="Get the last 5 maintenance events for a specific piece of equipment. Also returns days since last maintenance and whether it is overdue.",
            inputSchema={
                "type": "object",
                "properties": {
                    "equipment_id": {"type": "string", "description": "Equipment ID, e.g. E001"}
                },
                "required": ["equipment_id"]
            }
        ),
        types.Tool(
            name="flag_anomaly",
            description="Log an anomaly when a sensor reading exceeds its threshold. Call this when you detect an abnormal reading.",
            inputSchema={
                "type": "object",
                "properties": {
                    "equipment_id":  {"type": "string", "description": "Equipment ID"},
                    "reading_type":  {"type": "string", "description": "One of: temperature, vibration, pressure"},
                    "value":         {"type": "number", "description": "The anomalous sensor value"}
                },
                "required": ["equipment_id", "reading_type", "value"]
            }
        ),
        types.Tool(
            name="get_production_metrics",
            description="Get aggregated sensor metrics for all equipment over a date range. Returns average, max, and min readings per equipment per sensor type.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "Start date in ISO format, e.g. 2026-05-01"},
                    "end_date":   {"type": "string", "description": "End date in ISO format, e.g. 2026-06-05"}
                },
                "required": ["start_date", "end_date"]
            }
        ),
        types.Tool(
            name="query_knowledge_base",
            description="Search the equipment manuals knowledge base to answer questions about maintenance procedures, thresholds, and troubleshooting.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The question to search for in the manuals"}
                },
                "required": ["question"]
            }
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "get_equipment_status":
        return await tools.get_equipment_status(arguments["equipment_id"])
    elif name == "get_maintenance_history":
        return await tools.get_maintenance_history(arguments["equipment_id"])
    elif name == "flag_anomaly":
        return await tools.flag_anomaly(
            arguments["equipment_id"],
            arguments["reading_type"],
            arguments["value"]
        )
    elif name == "get_production_metrics":
        return await tools.get_production_metrics(
            arguments["start_date"],
            arguments["end_date"]
        )
    elif name == "query_knowledge_base":
        return await tools.query_knowledge_base(arguments["question"])
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())