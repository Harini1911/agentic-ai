"""
DateTime tool for getting current time in different timezones.

Provides real-time timezone information without requiring external APIs.
"""

from datetime import datetime
from typing import Dict, Any
import pytz


async def get_current_time(timezone: str = "UTC") -> str:
    """
    Get the current time in a specific timezone.
    
    Args:
        timezone: Timezone name (e.g., 'America/New_York', 'Asia/Tokyo', 'UTC')
        
    Returns:
        A string with the current time in the specified timezone.
    """
    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        
        return f"Current time in {timezone}: {formatted_time}"
        
    except pytz.exceptions.UnknownTimeZoneError:
        # Provide helpful suggestions
        common_timezones = [
            "UTC", "America/New_York", "America/Los_Angeles", 
            "Europe/London", "Europe/Paris", "Asia/Tokyo", 
            "Asia/Shanghai", "Australia/Sydney"
        ]
        return f"Unknown timezone: {timezone}. Try one of these: {', '.join(common_timezones)}"
    except Exception as e:
        return f"Error getting time: {str(e)}"


async def get_time_difference(timezone1: str, timezone2: str) -> str:
    """
    Calculate the time difference between two timezones.
    
    Args:
        timezone1: First timezone name
        timezone2: Second timezone name
        
    Returns:
        A string describing the time difference.
    """
    try:
        tz1 = pytz.timezone(timezone1)
        tz2 = pytz.timezone(timezone2)
        
        now = datetime.now(pytz.UTC)
        time1 = now.astimezone(tz1)
        time2 = now.astimezone(tz2)
        
        # Calculate offset difference in hours
        offset1 = time1.utcoffset().total_seconds() / 3600
        offset2 = time2.utcoffset().total_seconds() / 3600
        difference = offset1 - offset2
        
        if difference == 0:
            return f"{timezone1} and {timezone2} are in the same timezone (no difference)."
        elif difference > 0:
            return f"{timezone1} is {abs(difference):.1f} hours ahead of {timezone2}."
        else:
            return f"{timezone1} is {abs(difference):.1f} hours behind {timezone2}."
            
    except pytz.exceptions.UnknownTimeZoneError as e:
        return f"Unknown timezone in request: {str(e)}"
    except Exception as e:
        return f"Error calculating time difference: {str(e)}"


# Tool declarations for registration
DATETIME_TOOL_DECLARATIONS = [
    {
        "name": "get_current_time",
        "description": "Get the current date and time in a specific timezone. Supports all standard timezone names like 'America/New_York', 'Europe/London', 'Asia/Tokyo', etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Timezone name (e.g., 'America/New_York', 'Asia/Tokyo', 'UTC'). Defaults to UTC if not specified."
                }
            },
            "required": []
        }
    },
    {
        "name": "get_time_difference",
        "description": "Calculate the time difference between two timezones. Useful for scheduling across time zones.",
        "parameters": {
            "type": "object",
            "properties": {
                "timezone1": {
                    "type": "string",
                    "description": "First timezone name"
                },
                "timezone2": {
                    "type": "string",
                    "description": "Second timezone name"
                }
            },
            "required": ["timezone1", "timezone2"]
        }
    }
]
