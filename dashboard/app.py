import streamlit as st
import pandas as pd
import json
from pathlib import Path

st.set_page_config(page_title="MCP Tool Monitor", layout="wide")
st.title("MCP Tool Call Monitor")
st.caption("Live observability dashboard for Equipment Health MCP Server")

log_path = Path("logs/tool_calls.jsonl")

if not log_path.exists():
    st.warning("No logs yet — run the agent first.")
    st.stop()

logs = []
with open(log_path) as f:
    for line in f:
        if line.strip():
            logs.append(json.loads(line))

if not logs:
    st.warning("Log file is empty.")
    st.stop()

df = pd.DataFrame(logs)
df["timestamp"] = pd.to_datetime(df["timestamp"])

# ── Summary metrics ──────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Tool Calls", len(df))
col2.metric("Successful", int(df["success"].sum()))
col3.metric("Failed", int((~df["success"]).sum()))
col4.metric("Avg Response Time", f"{df['duration_ms'].mean():.0f}ms")

st.divider()

# ── Calls per tool bar chart ──────────────────────────────
st.subheader("Calls per tool")
tool_counts = df.groupby("tool_name").size().reset_index(name="calls")
st.bar_chart(tool_counts.set_index("tool_name"))

st.divider()

# ── Success rate per tool ─────────────────────────────────
st.subheader("Success rate per tool")
success_rate = df.groupby("tool_name")["success"].mean().reset_index()
success_rate["success_pct"] = (success_rate["success"] * 100).round(1)
st.dataframe(
    success_rate[["tool_name", "success_pct"]].rename(columns={
        "tool_name": "Tool",
        "success_pct": "Success %"
    }),
    use_container_width=True,
    hide_index=True
)

st.divider()

# ── Recent calls log ──────────────────────────────────────
st.subheader("Recent tool calls (last 20)")
recent = df.sort_values("timestamp", ascending=False).head(20)
st.dataframe(
    recent[["timestamp", "tool_name", "success", "duration_ms", "error"]].rename(columns={
        "timestamp": "Time",
        "tool_name": "Tool",
        "success": "Success",
        "duration_ms": "Duration (ms)",
        "error": "Error"
    }),
    use_container_width=True,
    hide_index=True
)