print("Testing BrowserBase setup...")

import os
from dotenv import load_dotenv
from tools.browserbase_tools import book_restaurant_reservation_real

# Load environment variables from .env.prod
load_dotenv('.env.prod')

# Check environment variables
os.environ["BROWSERBASE_API_KEY"] = os.getenv("BROWSERBASE_API_KEY")
os.environ["BROWSERBASE_PROJECT_ID"] = os.getenv("BROWSERBASE_PROJECT_ID")
api_key = os.getenv('BROWSERBASE_API_KEY')
project_id = os.getenv('BROWSERBASE_PROJECT_ID')

print(f"BROWSERBASE_API_KEY: {'Set' if api_key else 'Missing'}")
print(f"BROWSERBASE_PROJECT_ID: {'Set' if project_id else 'Missing'}")

if api_key and project_id:
    print(f"API Key: {api_key[:10]}...")
    print(f"Project ID: {project_id}")
    
    # Test the real booking function
    print("\n" + "="*50)
    print("Testing Real Booking Function...")
    
    result = book_restaurant_reservation_real.func(
        restaurant_name="Hinodeya San Jose",
        date="July 15, 2024",
        time="7:00 PM",
        party_size=2,
        contact_info="john.doe@email.com"
    )
    
    print("Result:")
    print(result)
    
    # Check if it worked
    if "REAL RESERVATION CONFIRMED" in result:
        print("\n✅ SUCCESS: Real browser automation worked!")
    elif "Session Replay" in result:
        print("\n🎥 BROWSER SESSION: Check the session replay link!")
    elif "FAILED" in result:
        print("\n❌ FAILED: Check the error details above")
    else:
        print("\n❓ UNCLEAR: Review the result above")
        
else:
    print("\n❌ Please set the environment variables first") 