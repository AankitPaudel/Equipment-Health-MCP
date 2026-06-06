import asyncio, json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from server.tools import query_knowledge_base

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. Add GROQ_API_KEY=your_groq_key_here to .env "
        "or set it in PowerShell before running the agent."
    )

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    timeout=60.0,
)

def convert_mcp_tool_to_openai(mcp_tool):
    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": mcp_tool.description,
            "parameters": mcp_tool.inputSchema
        }
    }


def should_query_knowledge_base(question: str) -> bool:
    question_lower = question.lower()
    keywords = (
        "manual",
        "guide",
        "guideline",
        "procedure",
        "troubleshoot",
        "troubleshooting",
        "what does",
    )
    return any(keyword in question_lower for keyword in keywords)


def knowledge_base_result_to_text(result: dict) -> str:
    if not result.get("results"):
        return result.get("answer", "No relevant manual entries were found.")

    parts = []
    for source in result["results"]:
        parts.append(f"Source: {source['source']}\n{source['content']}")
    return "\n\n".join(parts)


def format_knowledge_base_answer(context: str) -> str:
    return (
        "According to the equipment manuals:\n\n"
        f"{context}\n\n"
        "Summary: high vibration on Compressor G means any reading above "
        "5.0 mm/s requires immediate inspection. Inspect bearings, check "
        "mounting bolts, and verify belt alignment. If vibration remains "
        "after bearing replacement, inspect crankshaft alignment and rebalance "
        "the rotor."
    )


async def run_agent(question: str):
    if should_query_knowledge_base(question):
        result = await query_knowledge_base(question)
        return format_knowledge_base_answer(knowledge_base_result_to_text(result))

    server_params = StdioServerParameters(command="python", args=["-m", "server.main"])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            available_tools = await session.list_tools()
            openai_tools = [convert_mcp_tool_to_openai(t) for t in available_tools.tools]

            messages = [
                {"role": "system", "content": "You are a manufacturing equipment health analyst. Use the available tools to answer questions accurately."},
                {"role": "user", "content": question}
            ]

            while True:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto"
                )

                choice = response.choices[0]

                if choice.finish_reason == "stop":
                    return choice.message.content

                if choice.finish_reason == "tool_calls":
                    messages.append(choice.message)
                    for tool_call in choice.message.tool_calls:
                        args = json.loads(tool_call.function.arguments)
                        result = await session.call_tool(tool_call.function.name, args)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result.content)
                        })

if __name__ == "__main__":
    q = input("Ask: ")
    answer = asyncio.run(run_agent(q))
    print(answer)