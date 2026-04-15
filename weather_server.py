"""Custom MCP server that wraps the Open-Meteo weather API.

Run directly: python weather_server.py
Or connect via MCP client with stdio transport.
"""

import json
import urllib.request
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather")


@mcp.tool()
def get_current_weather(latitude: float, longitude: float) -> str:
    """Get the current temperature for a location.

    Args:
        latitude: The latitude of the location (e.g., 48.8566 for Paris).
        longitude: The longitude of the location (e.g., 2.3522 for Paris).

    Returns:
        A JSON string with the current temperature and weather conditions.
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        f"&current=temperature_2m,wind_speed_10m"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        current = data.get("current", {})
        return json.dumps({
            "temperature_celsius": current.get("temperature_2m"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "location": f"{latitude}, {longitude}",
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run(transport="stdio")
