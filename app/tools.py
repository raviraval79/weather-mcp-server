"""
MCP tool definitions for the weather server.
Each function maps directly to one Open-Meteo API call.
"""

from mcp.server import Server
from mcp.types import Tool, TextContent
from app.openmeteo import get_current_weather, get_forecast, get_historical_weather
import json


def register_tools(server: Server) -> None:
    """Register all weather tools on the MCP server instance."""

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="get_current_weather",
                description=(
                    "Get current weather conditions for a location specified by "
                    "latitude and longitude. Returns temperature, humidity, wind, "
                    "precipitation, and a human-readable condition description."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "Latitude of the location (e.g. 19.076 for Mumbai)",
                        },
                        "longitude": {
                            "type": "number",
                            "description": "Longitude of the location (e.g. 72.877 for Mumbai)",
                        },
                    },
                    "required": ["latitude", "longitude"],
                },
            ),
            Tool(
                name="get_forecast",
                description=(
                    "Get a weather forecast for a location for up to 16 days. "
                    "Returns daily summaries (max/min temperature, precipitation, wind, "
                    "sunrise/sunset). Optionally include hourly data."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "Latitude of the location",
                        },
                        "longitude": {
                            "type": "number",
                            "description": "Longitude of the location",
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of forecast days (1–16). Defaults to 7.",
                            "minimum": 1,
                            "maximum": 16,
                            "default": 7,
                        },
                        "hourly": {
                            "type": "boolean",
                            "description": "Include hourly breakdown in addition to daily summary. Defaults to false.",
                            "default": False,
                        },
                    },
                    "required": ["latitude", "longitude"],
                },
            ),
            Tool(
                name="get_historical_weather",
                description=(
                    "Get historical daily weather data for a location between two dates. "
                    "Returns temperature, precipitation, and wind for each day in the range."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "Latitude of the location",
                        },
                        "longitude": {
                            "type": "number",
                            "description": "Longitude of the location",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format (e.g. 2024-01-01)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format (e.g. 2024-01-31)",
                        },
                    },
                    "required": ["latitude", "longitude", "start_date", "end_date"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            if name == "get_current_weather":
                result = await get_current_weather(
                    latitude=arguments["latitude"],
                    longitude=arguments["longitude"],
                )
            elif name == "get_forecast":
                result = await get_forecast(
                    latitude=arguments["latitude"],
                    longitude=arguments["longitude"],
                    days=arguments.get("days", 7),
                    hourly=arguments.get("hourly", False),
                )
            elif name == "get_historical_weather":
                result = await get_historical_weather(
                    latitude=arguments["latitude"],
                    longitude=arguments["longitude"],
                    start_date=arguments["start_date"],
                    end_date=arguments["end_date"],
                )
            else:
                result = {"error": f"Unknown tool: {name}"}

        except Exception as exc:
            result = {"error": str(exc)}

        return [TextContent(type="text", text=json.dumps(result, indent=2))]
