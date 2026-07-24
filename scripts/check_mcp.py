from __future__ import annotations

import asyncio
import json
import os
import sys

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    api_url = os.getenv("ROOMPULSE_API_URL", "http://127.0.0.1:8000")
    expected_payload = httpx.get(
        f"{api_url.rstrip('/')}/v1/rooms/room-philip/latest", timeout=10
    ).json()
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_server.server"],
        env={
            **os.environ,
                "ROOMPULSE_API_URL": api_url,
        },
        cwd=os.getcwd(),
    )
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [tool.name for tool in tools.tools]
            expected = {
                "get_current_room_conditions",
                "get_room_trend",
                "explain_room_change",
            }
            if set(names) != expected:
                raise RuntimeError(f"Unexpected MCP tools: {names}")

            result = await session.call_tool("get_current_room_conditions", {})
            if result.isError:
                raise RuntimeError(str(result.content))
            payload = json.loads(result.content[0].text)
            stable_fields = (
                "id",
                "device_id",
                "room_id",
                "temperature_c",
                "humidity_pct",
                "measured_at",
            )
            if any(payload[field] != expected_payload[field] for field in stable_fields):
                raise RuntimeError(f"Unexpected sensor payload: {payload}")

            print(f"MCP tools OK: {', '.join(sorted(names))}")
            print(
                "MCP current conditions: "
                f"{payload['temperature_c']:.1f} °C / "
                f"{payload['humidity_pct']:.1f} % RH"
            )


if __name__ == "__main__":
    asyncio.run(main())
