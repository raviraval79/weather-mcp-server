"""
weather-mcp-server
SSE transport — confirmed to work on Cloud Run.
(Streamable HTTP has a known issue with Cloud Run's networking layer.)
MCP endpoint: GET /sse
"""

import logging
import os
from mcp.server.fastmcp import FastMCP
from app.openmeteo import get_current_weather, get_forecast, get_historical_weather

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

port = int(os.environ.get("PORT", 8080))

mcp = FastMCP(
    "weather-mcp-server",
    host="0.0.0.0",
    port=port,
)


@mcp.tool()
async def get_current_weather_tool(latitude: float, longitude: float) -> dict:
    """
    Get current weather conditions for a location.

    Args:
        latitude: Latitude of the location (e.g. 18.52 for Pune)
        longitude: Longitude of the location (e.g. 73.85 for Pune)

    Returns:
        Current temperature, humidity, wind speed, precipitation, and condition.
    """
    return await get_current_weather(latitude, longitude)


@mcp.tool()
async def get_forecast_tool(
    latitude: float,
    longitude: float,
    days: int = 7,
    hourly: bool = False,
) -> dict:
    """
    Get a weather forecast for a location for up to 16 days.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        days: Number of forecast days (1-16). Defaults to 7.
        hourly: Include hourly breakdown in addition to daily summary.

    Returns:
        Daily forecast with temperature, precipitation, wind, sunrise/sunset.
    """
    return await get_forecast(latitude, longitude, days, hourly)


@mcp.tool()
async def get_historical_weather_tool(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
) -> dict:
    """
    Get historical daily weather data for a location between two dates.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        start_date: Start date in YYYY-MM-DD format (e.g. 2024-01-01)
        end_date: End date in YYYY-MM-DD format (e.g. 2024-01-31)

    Returns:
        Daily historical weather including temperature, precipitation, and wind.
    """
    return await get_historical_weather(latitude, longitude, start_date, end_date)


if __name__ == "__main__":
    logger.info(f"Starting weather-mcp-server on port {port} with SSE transport")
    mcp.run(transport="sse")
