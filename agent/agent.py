import asyncio, json
from dotenv import load_dotenv
load_dotenv()
import os
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
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

async def run_agent(question: str):
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
                    model="llama-3.3-70b-versatile",
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