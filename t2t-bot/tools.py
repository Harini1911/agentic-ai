import requests

from google.genai import types

get_weather_declaration = types.FunctionDeclaration(
    name="get_weather",
    description="Get the current weather for a given city using Open-Meteo API.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "city": types.Schema(
                type="STRING",
                description="The name of the city."
            )
        },
        required=["city"]
    )
)


def get_weather(city: str) -> str:
    """
    Get the current weather for a given city using Open-Meteo API.
    
    Args:
        city: The name of the city.
        
    Returns:
        A string describing the weather.
    """
    try:
        # 1. Geocoding
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_response = requests.get(geo_url).json()
        
        if not geo_response.get("results"):
            return f"Could not find coordinates for city: {city}"
            
        location = geo_response["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        name = location["name"]
        country = location.get("country", "")
        
        # 2. Weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code"
        weather_response = requests.get(weather_url).json()
        
        if "current" not in weather_response:
             return f"Could not fetch weather data for {name}."

        current = weather_response["current"]
        temp = current["temperature_2m"]
        unit = weather_response["current_units"]["temperature_2m"]
        
        return f"The current temperature in {name}, {country} is {temp}{unit}."
        
    except Exception as e:
        return f"Error fetching weather: {e}"

tools_list = [get_weather]

