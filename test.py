import asyncio
import os
from dotenv import load_dotenv
from tools.exa_tools import ExaSearchTool
from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content

async def main():
    # Load environment variables from .env.prod
    load_dotenv('.env.prod')
    
    # Set your API key as environment variable
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
    
    # Create the agent with Exa search tool  
    agent = Agent(
        name="researcher",
        model="gemini-2.5-flash",
        tools=[ExaSearchTool],
    )

    # Create session service and create a session
    session_service = InMemorySessionService()
    user_id = "user123"
    session_id = "session456"

    # Create a session first (this is async)
    await session_service.create_session(app_name="research_app", user_id=user_id, session_id=session_id)

    # Create a runner with required services
    runner = Runner(
        app_name="research_app",
        agent=agent,
        session_service=session_service,
    )

    # Create a message with the user's query
    query = "Can you tell me the best authentic Japanese ramen in the south Bay Area? Specifically from Yelp reviews."
    message = Content(
        role="user",
        parts=[{"text": query}]
    )

    print(f"🔍 Searching for: {query}")
    print("=" * 50)
    
    # Run the agent and collect only the final text responses
    final_response = ""
    try:
        for event in runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=message
        ):
            # Only print the final AI text response, skip debug info
            if hasattr(event, 'content') and hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        final_response = part.text
                    elif hasattr(part, 'function_response') and part.function_response is not None:
                        # Check if function_response exists and has response attribute
                        if hasattr(part.function_response, 'response') and part.function_response.response:
                            result = part.function_response.response.get('result', '')
                            if result:
                                print("📊 Search Results:")
                                print(result)
                                print("\n" + "=" * 50)
    
        if final_response:
            print("🤖 AI Response:")
            print(final_response)
    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())