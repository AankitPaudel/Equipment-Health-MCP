# Equipment Health MCP Server

An AI agent system that monitors manufacturing equipment health using the **Model Context Protocol (MCP)**. An LLM agent answers natural language questions about equipment by calling tools exposed through an MCP server — backed by real PostgreSQL data, RAG over equipment manuals, and a live observability dashboard.

## Architecture

```text
User Question
↓
AI Agent (LLaMA 3.3 70B via Groq)
↓
MCP Client
↓
MCP Server (Python MCP SDK)
↓
5 Tools
↓
PostgreSQL + ChromaDB
↓
Observability Layer → Streamlit Dashboard
```

## Example agent conversations

Ask: Is equipment E004 showing any anomalies right now?
→ Yes, E004 (Lathe Machine D) has a temperature reading of 89.72C
which exceeds the threshold of 80.0C. Anomaly detected.

Ask: Is E007 overdue for maintenance?
→ Yes, Compressor G has not been serviced in 90 days.
Last event was a bearing replacement — vibration issue unresolved.

Ask: Which equipment has the highest average temperature this week?
→ E004 has the highest average temperature at 91.2C,
significantly above the 80C safety threshold.

Ask: Flag an anomaly for E004 temperature reading of 91.5
→ Anomaly successfully flagged for E004:
temperature = 91.5 (threshold: 80.0)

## 5 MCP Tools

| Tool | Description |
|---|---|
| `get_equipment_status` | Latest sensor readings with anomaly detection for temperature, vibration, and pressure |
| `get_maintenance_history` | Last 5 maintenance events plus days since last service and overdue flag |
| `flag_anomaly` | Log anomalous sensor readings to the database |
| `get_production_metrics` | Aggregated min, max, and average metrics over a date range |
| `query_knowledge_base` | RAG search over equipment manuals using ChromaDB |

## Tech Stack

| Layer | Technology |
|---|---|
| MCP Server | Python MCP SDK |
| AI Agent | LLaMA 3.3 70B via Groq API |
| REST API | FastAPI with Swagger UI |
| Database | PostgreSQL via SQLAlchemy |
| RAG | ChromaDB + sentence-transformers |
| Observability | JSONL logging + Streamlit dashboard |
| CI/CD | GitHub Actions |
| Deployment | Docker Compose |

## Project Structure

```text
equipment-health-mcp/
├── server/
│   ├── main.py           # MCP server — registers and routes all 5 tools
│   ├── tools.py          # Tool implementations — all database queries
│   ├── database.py       # SQLAlchemy models and session management
│   ├── observability.py  # Logs every tool call to JSONL
│   ├── rag.py            # ChromaDB indexing for equipment manuals
│   └── api.py            # FastAPI REST layer on top of MCP tools
├── agent/
│   └── agent.py          # LLM agent that connects to MCP server
├── data/
│   ├── seed.py           # Populates 10 machines with 30 days of sensor data
│   └── manuals/          # Equipment manual text files for RAG
├── dashboard/
│   └── app.py            # Streamlit observability dashboard
├── tests/
│   └── test_tools.py     # Unit tests for all 5 tools
├── logs/
│   └── tool_calls.jsonl  # Auto-generated observability log
├── .github/
│   └── workflows/
│       └── ci.yml        # GitHub Actions CI pipeline
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/AankitPaudel/Equipment-Health-MCP
cd Equipment-Health-MCP
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:

```env
GROQ_API_KEY=your_groq_key_here
DATABASE_URL=postgresql://postgres:password@localhost:5432/equipment_db
```

### 3. Start the database and seed data

```bash
docker-compose up postgres -d
python -c "from server.database import init_db; init_db()"
python data/seed.py
```

### 4. Run the AI agent

```bash
python agent/agent.py
```

### 5. Run the REST API

```bash
uvicorn server.api:app --reload
# Swagger UI available at http://localhost:8000/docs
```

### 6. Run the observability dashboard

```bash
streamlit run dashboard/app.py
# Dashboard available at http://localhost:8501
```

### 7. Run with Docker Compose

```bash
docker-compose up
```

## REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/equipment/{id}/status` | Get current sensor readings |
| GET | `/equipment/{id}/maintenance` | Get maintenance history |
| POST | `/equipment/{id}/anomaly` | Flag an anomaly |
| GET | `/metrics` | Get production metrics over date range |
| GET | `/knowledge` | Search equipment manuals |
| GET | `/health` | Health check |

## Observability

Every tool call is logged automatically to `logs/tool_calls.jsonl` with:
- Timestamp
- Tool name
- Input arguments
- Response time in milliseconds
- Success or failure status
- Error message if failed

The Streamlit dashboard reads this log and displays live metrics including total calls, success rate, average response time, and a bar chart of calls per tool.

## CI/CD

GitHub Actions runs on every push to main:
- Spins up a real PostgreSQL instance
- Installs all dependencies
- Seeds the database
- Runs all unit tests with pytest

## Running Tests

```bash
python -m pytest tests/ -v
```

## Why This Project

Many semiconductor manufacturers are implementing MCP to connect AI agents to production data, quality control systems, and maintenance records. This project demonstrates that architecture at a personal scale — showing how MCP enables AI agents to answer real operational questions using live manufacturing data without custom one-off integrations.
