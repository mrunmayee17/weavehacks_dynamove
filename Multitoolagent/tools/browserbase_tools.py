import os
import json
from google.adk.tools import FunctionTool
import httpx
import re

# Check if optional dependencies are available
try:
    from playwright.sync_api import sync_playwright, Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from browserbase import Browserbase
    BROWSERBASE_AVAILABLE = True
except ImportError:
    BROWSERBASE_AVAILABLE = False

def navigate_and_extract(url: str, instruction: str) -> str:
    """
    Open a URL and extract content according to instruction.
    """
    try:
        response = httpx.get(url, timeout=10)
        content = response.text[:2000]
        return f"Content from {url}:\n{content}"
    except Exception as e:
        return f"Error accessing {url}: {str(e)}"

def extract_contact_info(text: str) -> dict:
    contact = {}
    # Email extraction (must contain @ and .)
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text)
    contact["email"] = email_match.group() if email_match else ""
    # Name extraction
    name_match = re.search(r"(?:my name is|i am|i'm)\s+([A-Za-z\s]+)", text, re.IGNORECASE)
    contact["name"] = name_match.group(1).strip().title() if name_match else ""
    # Phone extraction (US-style)
    phone_match = re.search(r"(\d{3})[^\d]?(\d{3})[^\d]?(\d{4})", text)
    contact["phone"] = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}" if phone_match else ""
    return contact

def book_restaurant_reservation_real(
    restaurant_name: str,
    date: str,
    time: str,
    party_size: int,
    contact_info: str
) -> str:
    """
    Book a restaurant reservation using browser automation. Requires restaurant name, date, time, party size, and contact info.
    
    Args:
        restaurant_name: Name of the restaurant
        date: Date of the reservation (e.g. 'July 21, 2025')
        time: Time of the reservation (e.g. '7:00 PM')
        party_size: Number of people for the reservation
        contact_info: User's contact info (email or phone)
    
    Returns:
        String with booking status and confirmation details
    """
    print(f"DEBUG: Called with restaurant_name={restaurant_name}, date={date}, time={time}, party_size={party_size}, contact_info={contact_info}")
    # Check for missing info
    missing = []
    if not restaurant_name: missing.append("restaurant name")
    if not date: missing.append("date")
    if not time: missing.append("time")
    if not party_size: missing.append("party size")
    if not contact_info or "@" not in contact_info: missing.append("valid email in contact info")
    if missing:
        return (
            f"❌ Missing required information: {', '.join(missing)}. "
            "Please provide all details to book your reservation."
        )

    api_key = os.getenv('BROWSERBASE_API_KEY')
    project_id = os.getenv('BROWSERBASE_PROJECT_ID')
    if not api_key or not project_id:
        return "❌ BROWSERBASE CREDENTIALS MISSING"

    if not PLAYWRIGHT_AVAILABLE or not BROWSERBASE_AVAILABLE:
        return "❌ MISSING DEPENDENCIES: playwright and browserbase required"

    try:
        search_url = f"https://www.google.com/search?q={restaurant_name.replace(' ', '+')}+restaurant+reservation"
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"wss://connect.browserbase.com?apiKey={api_key}&projectId={project_id}")
            page = browser.new_page()
            try:
                page.goto(search_url, wait_until="networkidle")
                page.wait_for_timeout(3000)
                # Try to find reservation links on Google results
                reservation_links = page.locator(
                    'a[href*="opentable.com"], a[href*="resy.com"], a[href*="yelp.com"], a[href*="reservation"], a:has-text("Reserve"), button:has-text("Reserve")'
                )
                print(f"DEBUG: Reservation links found: {reservation_links.count()}")
                if reservation_links.count() > 0:
                    reservation_links.first.click()
                    page.wait_for_timeout(5000)
                    print("DEBUG: Clicked reservation link, waiting for form...")
                    # Try to fill OpenTable/Resy form (example for OpenTable)
                    # You may need to adjust selectors for different platforms
                    try:
                        # Example: OpenTable selectors (may need to update for real site)
                        if "opentable" in page.url:
                            # Fill party size
                            if party_size:
                                try:
                                    page.select_option('select[name="PartySize"]', str(party_size))
                                except Exception as e:
                                    print(f"DEBUG: Party size select failed: {e}")
                            # Fill date
                            if date:
                                try:
                                    page.fill('input[name="Date"]', date)
                                except Exception as e:
                                    print(f"DEBUG: Date fill failed: {e}")
                            # Fill time
                            if time:
                                try:
                                    page.fill('input[name="Time"]', time)
                                except Exception as e:
                                    print(f"DEBUG: Time fill failed: {e}")
                            # Fill contact info (if possible)
                            if contact_info:
                                try:
                                    page.fill('input[type="email"]', contact_info)
                                except Exception as e:
                                    print(f"DEBUG: Email fill failed: {e}")
                            # Click submit/reserve
                            try:
                                page.click('button:has-text("Find a Table"), button:has-text("Reserve"), button[type="submit"]')
                                page.wait_for_timeout(5000)
                            except Exception as e:
                                print(f"DEBUG: Submit click failed: {e}")
                            # Try to get confirmation number
                            confirmation = None
                            try:
                                confirmation = page.text_content('text=Confirmation') or page.text_content('text=Confirmed')
                            except Exception as e:
                                print(f"DEBUG: Confirmation extract failed: {e}")
                            session_url = f"https://browserbase.com/sessions/{page.context.browser.contexts[0].pages[0].url}"
                            return f"""
✅ **RESERVATION BOOKING ATTEMPTED**

**Restaurant:** {restaurant_name}
**Date:** {date}
**Time:** {time}
**Party Size:** {party_size}
**Contact:** {contact_info}

**Status:** {'✅ Confirmed' if confirmation else '⚠️ Submitted, please verify manually'}
**Confirmation:** {confirmation or 'N/A'}
**Session Replay:** {session_url}
"""
                        else:
                            # Not OpenTable, just return session replay
                            session_url = f"https://browserbase.com/sessions/{page.context.browser.contexts[0].pages[0].url}"
                            return f"""
⚠️ **RESERVATION PLATFORM NOT FULLY SUPPORTED**

**Restaurant:** {restaurant_name}
**Status:** Reservation page opened, but automation for this platform is not implemented.
**Session Replay:** {session_url}
"""
                    except Exception as e:
                        print(f"DEBUG: Form fill/submit failed: {e}")
                        session_url = f"https://browserbase.com/sessions/{page.context.browser.contexts[0].pages[0].url}"
                        return f"""
❌ **FORM FILL ERROR**

**Error:** {e}
**Session Replay:** {session_url}
"""
                else:
                    return f"""
⚠️ **RESERVATION PLATFORM NOT FOUND**

**Restaurant:** {restaurant_name}
**Status:** ❌ No reservation platform found
**Searched:** Google search completed
**Confirmation:** None

Please try booking manually or provide a direct reservation link.
"""
            finally:
                page.close()
                browser.close()
    except Exception as e:
        return f"""
❌ **BROWSER AUTOMATION ERROR**

**Error:** {str(e)}
**Restaurant:** {restaurant_name}
**Status:** FAILED - Technical error
**Confirmation:** None

Please try again or book manually.
"""

# Create the FunctionTool
book_restaurant_reservation_real = FunctionTool(book_restaurant_reservation_real)
navigate_and_extract = FunctionTool(navigate_and_extract)