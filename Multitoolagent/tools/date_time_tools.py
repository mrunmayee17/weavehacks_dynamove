from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from google.adk.tools import FunctionTool

def get_current_date_time():
    """
    Get the current date and time in the user's timezone.
    
    Returns:
        String with formatted date and time
    """
    pacific_timezone = ZoneInfo("America/Los_Angeles")
    return datetime.now(pacific_timezone).strftime("%Y-%m-%d %H:%M:%S")

DateAndTimeTool = FunctionTool(get_current_date_time)