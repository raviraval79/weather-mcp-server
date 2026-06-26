"""
Async client for the Open-Meteo API.
No API key required — Open-Meteo is free and open.
Docs: https://open-meteo.com/en/docs
"""

import httpx
from typing import Any

BASE_URL = "https://api.open-meteo.com/v1"

# Human-readable labels for WMO weather interpretation codes
WMO_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


async def get_current_weather(latitude: float, longitude: float) -> dict[str, Any]:
    """Fetch current weather conditions for a given lat/lon."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m",
        ],
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BASE_URL}/forecast", params=params)
        response.raise_for_status()
        data = response.json()

    current = data.get("current", {})
    weather_code = current.get("weather_code")
    return {
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "timezone": data.get("timezone"),
        "time": current.get("time"),
        "temperature_celsius": current.get("temperature_2m"),
        "feels_like_celsius": current.get("apparent_temperature"),
        "humidity_percent": current.get("relative_humidity_2m"),
        "precipitation_mm": current.get("precipitation"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "wind_direction_degrees": current.get("wind_direction_10m"),
        "weather_code": weather_code,
        "condition": WMO_CODES.get(weather_code, "Unknown"),
    }


async def get_forecast(
    latitude: float,
    longitude: float,
    days: int = 7,
    hourly: bool = False,
) -> dict[str, Any]:
    """Fetch a daily (or hourly) forecast for up to 16 days."""
    days = max(1, min(days, 16))

    daily_vars = [
        "weather_code",
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "wind_speed_10m_max",
        "sunrise",
        "sunset",
    ]
    hourly_vars = [
        "temperature_2m",
        "precipitation",
        "weather_code",
        "wind_speed_10m",
        "relative_humidity_2m",
    ]

    params: dict[str, Any] = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": daily_vars,
        "forecast_days": days,
        "timezone": "auto",
    }
    if hourly:
        params["hourly"] = hourly_vars

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{BASE_URL}/forecast", params=params)
        response.raise_for_status()
        data = response.json()

    # Annotate daily weather codes with human-readable labels
    daily = data.get("daily", {})
    codes = daily.get("weather_code", [])
    daily["condition"] = [WMO_CODES.get(c, "Unknown") for c in codes]

    result: dict[str, Any] = {
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "timezone": data.get("timezone"),
        "forecast_days": days,
        "daily": daily,
    }
    if hourly:
        hourly_data = data.get("hourly", {})
        h_codes = hourly_data.get("weather_code", [])
        hourly_data["condition"] = [WMO_CODES.get(c, "Unknown") for c in h_codes]
        result["hourly"] = hourly_data

    return result


async def get_historical_weather(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """Fetch historical daily weather for a date range (YYYY-MM-DD)."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
        ],
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(f"{BASE_URL}/archive", params=params)
        response.raise_for_status()
        data = response.json()

    daily = data.get("daily", {})
    codes = daily.get("weather_code", [])
    daily["condition"] = [WMO_CODES.get(c, "Unknown") for c in codes]

    return {
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "timezone": data.get("timezone"),
        "start_date": start_date,
        "end_date": end_date,
        "daily": daily,
    }
