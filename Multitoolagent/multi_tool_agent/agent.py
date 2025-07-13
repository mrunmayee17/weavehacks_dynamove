from google.adk.agents import Agent
from tools.exa_tools import ExaSearchTool
from tools.browserbase_tools import book_restaurant_reservation_real, navigate_and_extract

root_agent = Agent(
    # A unique name for the agent.
    name="restaurant_booking_agent",
    # The Large Language Model (LLM) that agent will use.
    model="gemini-2.0-flash",
    # A short description of the agent's purpose.
    description="AI agent that can search for restaurants and make real reservations using browser automation.",
    # Instructions to set the agent's behavior.
    instruction="""
    You are a restaurant booking assistant with the following capabilities:
    
    1. **Search for restaurants** using Exa search - find reviews, information, and booking platforms
    2. **Make real reservations** using BrowserBase browser automation - actually book tables at restaurants
    3. **Navigate websites** to extract information about restaurants
    
    When a user wants to book a restaurant:
    1. First search for the restaurant using Exa to find reviews and information
    2. Then use the real browser automation to make the actual reservation
    3. Provide the user with confirmation details and session replay links as proof
    
    Always be helpful, provide detailed information, and confirm bookings with real confirmation numbers.
    """,
    # Add both tools for complete restaurant booking functionality
    tools=[ExaSearchTool, book_restaurant_reservation_real, navigate_and_extract]
) 