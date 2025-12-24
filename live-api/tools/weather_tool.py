"""
Weather tool for fetching real-time weather data.

Uses Open-Meteo API (free, no API key required) to get current weather.
"""

from typing import Dict, Any
import httpx


async def get_weather(city: str) -> str:
    """
    Get the current weather for a given city using Open-Meteo API.
    
    Args:
        city: The name of the city.
        
    Returns:
        A string describing the weather.
    """
    try:
        async with httpx.AsyncClient() as client:
            # 1. Geocoding - get coordinates for the city
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
            geo_response = await client.get(geo_url, timeout=10.0)
            geo_data = geo_response.json()
            
            if not geo_data.get("results"):
                return f"Could not find coordinates for city: {city}"
                
            location = geo_data["results"][0]
            lat = location["latitude"]
            lon = location["longitude"]
            name = location["name"]
            country = location.get("country", "")
            
            # 2. Weather - get current weather data
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
            weather_response = await client.get(weather_url, timeout=10.0)
            weather_data = weather_response.json()
            
            if "current" not in weather_data:
                return f"Could not fetch weather data for {name}."

            current = weather_data["current"]
            temp = current["temperature_2m"]
            humidity = current.get("relative_humidity_2m", "N/A")
            wind_speed = current.get("wind_speed_10m", "N/A")
            temp_unit = weather_data["current_units"]["temperature_2m"]
            
            # Weather code interpretation (simplified)
            weather_code = current.get("weather_code", 0)
            conditions = _interpret_weather_code(weather_code)
            
            return f"Weather in {name}, {country}: {temp}{temp_unit}, {conditions}. Humidity: {humidity}%, Wind: {wind_speed} km/h"
            
    except httpx.TimeoutException:
        return f"Weather API timeout for {city}"
    except Exception as e:
        return f"Error fetching weather: {e}"


async def get_forecast(city: str) -> str:
    """
    Get 7-day weather forecast for a given city using Open-Meteo API.
    
    Args:
        city: The name of the city.
        
    Returns:
        A string describing the forecast.
    """
    try:
        async with httpx.AsyncClient() as client:
            # 1. Geocoding
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
            geo_response = await client.get(geo_url, timeout=10.0)
            geo_data = geo_response.json()
            
            if not geo_data.get("results"):
                return f"Could not find coordinates for city: {city}"
                
            location = geo_data["results"][0]
            lat = location["latitude"]
            lon = location["longitude"]
            name = location["name"]
            country = location.get("country", "")
            
            # 2. Forecast
            forecast_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,weather_code&timezone=auto"
            forecast_response = await client.get(forecast_url, timeout=10.0)
            forecast_data = forecast_response.json()
            
            if "daily" not in forecast_data:
                return f"Could not fetch forecast data for {name}."
            
            daily = forecast_data["daily"]
            dates = daily["time"][:7]  # Next 7 days
            max_temps = daily["temperature_2m_max"][:7]
            min_temps = daily["temperature_2m_min"][:7]
            weather_codes = daily["weather_code"][:7]
            
            forecast_text = f"7-day forecast for {name}, {country}:\n"
            for i, date in enumerate(dates):
                conditions = _interpret_weather_code(weather_codes[i])
                forecast_text += f"{date}: {min_temps[i]}°C to {max_temps[i]}°C, {conditions}\n"
            
            return forecast_text.strip()
            
    except httpx.TimeoutException:
        return f"Weather API timeout for {city}"
    except Exception as e:
        return f"Error fetching forecast: {e}"


def _interpret_weather_code(code: int) -> str:
    """
    Interpret WMO weather codes.
    
    Args:
        code: WMO weather code
        
    Returns:
        Human-readable weather condition
    """
    # WMO Weather interpretation codes
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return weather_codes.get(code, "Unknown")


# Tool declarations for registration
WEATHER_TOOL_DECLARATIONS = [
    {
        "name": "get_weather",
        "description": "Get current weather conditions for a specific city. Returns temperature, humidity, wind speed, and weather conditions using Open-Meteo API (no API key required).",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name (e.g., 'London', 'Paris', 'New York')"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "get_forecast",
        "description": "Get 7-day weather forecast for a specific city. Returns daily temperature predictions and conditions using Open-Meteo API.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name (e.g., 'London', 'Paris', 'New York')"
                }
            },
            "required": ["city"]
        }
    }
]
