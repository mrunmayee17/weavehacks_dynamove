import asyncio, io, os, wave, uuid
import streamlit as st
from google.adk.runners  import Runner
from google.adk.sessions import InMemorySessionService
from google.genai        import types
import openai, tempfile, os, io, wave
from gtts import gTTS
import io
import re
# import speech_recognition as sr

# ---- ① Load the agent ------------------------------------------------------
from multi_tool_agent.agent import root_agent
from dotenv import load_dotenv

import assemblyai as aai

# Load environment variables from .env.prod
load_dotenv('.env.prod')

# Set up API keys
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# Set BrowserBase credentials for real automation
os.environ["BROWSERBASE_API_KEY"] = os.getenv("BROWSERBASE_API_KEY")
os.environ["BROWSERBASE_PROJECT_ID"] = os.getenv("BROWSERBASE_PROJECT_ID")
os.environ["EXA_API_KEY"] = os.getenv("EXA_API_KEY")

@st.cache_resource
def init_services():
    sess_service = InMemorySessionService()

    runner = Runner(
        app_name        = "restaurant_booking_demo",
        agent           = root_agent,
        session_service = sess_service,
    )

    # NEW: synchronous wrapper added in ADK 1.0
    user_id  = str(uuid.uuid4())
    session  = sess_service.create_session_sync(
        app_name="restaurant_booking_demo",
        user_id=user_id,
    )

    return runner, session

runner, session = init_services()

def _transcribe(audio_bytes: bytes) -> str:
    """
    Uses AssemblyAI's /transcribe endpoint.
    Pass raw WAV/MP3 bytes; SDK uploads & blocks until done.
    """
    if not aai.settings.api_key:
        return "⚠️  ASSEMBLYAI_API_KEY missing"

    try:
        transcriber = aai.Transcriber()
        transcript  = transcriber.transcribe(audio_bytes)
        print("========================", transcript.text.strip())
        return transcript.text.strip()
    except Exception as err:
        return f"⚠️  STT error: {err}"

def _speak(text: str, lang: str = "en") -> bytes:
    """
    Return MP3 bytes for *text* using Google-Translate TTS.
    """
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception as err:
        st.warning(f"TTS error: {err}")
        return b""

def _ask_agent(message: str, user_contact: dict = None) -> str:
    """Send *message* to the ADK agent and return its final reply."""
    
    # Enhance message with user contact info if available
    if user_contact and any(user_contact.values()):
        contact_info = []
        if user_contact.get('name'):
            contact_info.append(f"User's name: {user_contact['name']}")
        if user_contact.get('email'):
            contact_info.append(f"User's email: {user_contact['email']}")
        if user_contact.get('phone'):
            contact_info.append(f"User's phone: {user_contact['phone']}")
        
        if contact_info:
            enhanced_message = f"{message}\n\n[User Contact Info: {', '.join(contact_info)}]"
        else:
            enhanced_message = message
    else:
        enhanced_message = message
    
    print(f"======================== {enhanced_message}")
    
    content = types.Content(role="user", parts=[types.Part(text=enhanced_message)])
    events = runner.run(user_id=session.user_id,
                       session_id=session.id,
                       new_message=content)
    
    # FIXED: Proper response parsing for ADK events
    final_response = ""
    for event in events:
        # Debug: Print event type and attributes
        # print(f"DEBUG: Event type: {type(event)}")
        # print(f"DEBUG: Event attributes: {dir(event)}")
        
        # Try different ways to access the response
        if hasattr(event, 'text') and event.text:
            final_response += event.text
        elif hasattr(event, 'content') and event.content:
            if hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        final_response += part.text
        elif hasattr(event, 'response') and event.response:
            if hasattr(event.response, 'text'):
                final_response += event.response.text
            elif hasattr(event.response, 'content'):
                if hasattr(event.response.content, 'parts'):
                    for part in event.response.content.parts:
                        if hasattr(part, 'text') and part.text:
                            final_response += part.text
        # Check for message attribute (common in ADK)
        elif hasattr(event, 'message') and event.message:
            if hasattr(event.message, 'content'):
                if hasattr(event.message.content, 'parts'):
                    for part in event.message.content.parts:
                        if hasattr(part, 'text') and part.text:
                            final_response += part.text
    
    print(f"DEBUG: Final response length: {len(final_response)}")
    print(f"DEBUG: Final response preview: {final_response[:200]}...")
    
    return final_response if final_response else "⚠️ No response generated"

def _extract_contact_info(text: str) -> dict:
    """Extract contact information from user messages."""
    contact = {}
    
    # Extract email patterns
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, text)
    if email_match:
        contact['email'] = email_match.group()
    
    # Extract name patterns (after "My name is" or "I'm" or "I am")
    name_patterns = [
        r'(?:my name is|i\'m|i am|name is)\s+([A-Za-z\s]+?)(?:\.|,|$|\s+(?:and|the|my|at))',
        r'(?:this is|it\'s)\s+([A-Za-z\s]+?)(?:\.|,|$|\s+(?:and|the|my|at))'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name.split()) <= 3 and name.replace(' ', '').isalpha():  # Reasonable name check
                contact['name'] = name.title()
                break
    
    # Extract phone patterns
    phone_pattern = r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        contact['phone'] = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
    
    return contact

def _extract_session_replay_url(text: str) -> str:
    """Extract BrowserBase session replay URL from agent response."""
    pattern = r'https://browserbase\.com/sessions/[a-zA-Z0-9\-]+'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def _extract_confirmation_number(text: str) -> str:
    """Extract confirmation number from agent response."""
    patterns = [
        r'Confirmation Number:\*\*\s*([A-Z0-9\-]+)',
        r'REAL-[A-Z]+-\d+',
        r'OT\d+',
        r'Confirmation:\s*([A-Z0-9\-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1) if match.groups() else match.group(0)
    return None

def _update_user_contact(new_contact: dict):
    """Update stored user contact information."""
    if 'user_contact' not in st.session_state:
        st.session_state.user_contact = {}
    
    for key, value in new_contact.items():
        if value:  # Only update non-empty values
            st.session_state.user_contact[key] = value

# ── 3. Streamlit front-end ----------------------------------------------------
st.set_page_config(page_title="🍽️ Restaurant Booking Assistant", page_icon="🍽️", layout="wide")

st.title("🍽️ Restaurant Booking Assistant")
st.caption("**Voice-powered restaurant search and real reservation booking** • Powered by Exa + BrowserBase")

# Initialize session state for user contact
if 'user_contact' not in st.session_state:
    st.session_state.user_contact = {'name': '', 'email': '', 'phone': ''}

# Sidebar with information and user contact management
with st.sidebar:
    st.header("👤 Your Contact Info")
    
    # Display current contact info
    current_contact = st.session_state.user_contact
    
    if any(current_contact.values()):
        st.success("✅ Contact information saved!")
        if current_contact.get('name'):
            st.write(f"**Name:** {current_contact['name']}")
        if current_contact.get('email'):
            st.write(f"**Email:** {current_contact['email']}")
        if current_contact.get('phone'):
            st.write(f"**Phone:** {current_contact['phone']}")
        
        # Edit contact button
        if st.button("✏️ Edit Contact Info"):
            st.session_state.editing_contact = True
    else:
        st.info("💡 Say your name and email in conversation, or enter manually below:")
    
    # Contact editing form
    if 'editing_contact' not in st.session_state:
        st.session_state.editing_contact = False
    
    if st.session_state.editing_contact or not any(current_contact.values()):
        with st.form("contact_form"):
            st.subheader("📝 Enter Contact Details")
            name = st.text_input("Name:", value=current_contact.get('name', ''))
            email = st.text_input("Email:", value=current_contact.get('email', ''))
            phone = st.text_input("Phone:", value=current_contact.get('phone', ''))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Save"):
                    st.session_state.user_contact = {
                        'name': name,
                        'email': email,
                        'phone': phone
                    }
                    st.session_state.editing_contact = False
                    st.rerun()
            with col2:
                if st.form_submit_button("🗑️ Clear"):
                    st.session_state.user_contact = {'name': '', 'email': '', 'phone': ''}
                    st.session_state.editing_contact = False
                    st.rerun()
    
    st.divider()
    
    st.header("🔧 System Status")
    
    # Check if BrowserBase is configured
    browserbase_configured = bool(os.getenv('BROWSERBASE_API_KEY') and os.getenv('BROWSERBASE_PROJECT_ID'))
    exa_configured = bool(os.getenv('EXA_API_KEY'))
    
    if browserbase_configured:
        st.success("✅ BrowserBase: Real automation enabled")
    else:
        st.error("❌ BrowserBase: Not configured")
    
    if exa_configured:
        st.success("✅ Exa Search: Restaurant search enabled")
    else:
        st.error("❌ Exa Search: Not configured")
    
    st.header("🎯 Capabilities")
    st.info("""
    **🔍 Search:** Find restaurants, reviews, and information
    
    **📅 Book:** Make real reservations with browser automation
    
    **🎥 Verify:** Get session replay links as proof
    
    **🗣️ Voice:** Speak your requests naturally
    
    **🧠 Memory:** Remembers your contact information
    """)
    
    st.header("💡 Example Requests")
    st.code("""
    "My name is John Doe, email john@example.com"
    
    "Find the best ramen in San Jose"
    
    "Book a table for 2 at Hinodeya 
    tomorrow at 7pm"
    
    "Search for Italian restaurants 
    with good reviews"
    """)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🎙️ Voice Input")
    audio_blob = st.audio_input("Record your restaurant request →")

with col2:
    st.subheader("⌨️ Text Input")
    text_input = st.text_area("Or type your request:", height=100, placeholder="e.g., 'My name is John, email john@example.com. Find sushi restaurants and book a table for 2'")
    send_text = st.button("Send Message", type="primary")

# Show previous turns stored in Streamlit session_state
if "history" not in st.session_state:
    st.session_state.history = []
if "raw" not in st.session_state:
    st.session_state.raw = None

# Display conversation history
st.subheader("💬 Conversation")

# Show contact extraction status
if any(st.session_state.user_contact.values()):
    st.info(f"🧠 **Remembered Contact:** {st.session_state.user_contact.get('name', 'Unknown')} ({st.session_state.user_contact.get('email', 'No email')})")

for speaker, text, aud, metadata in st.session_state.history:
    with st.chat_message(speaker):
        st.markdown(text)
        
        # Show special restaurant booking information
        if speaker == "assistant" and metadata:
            if metadata.get("confirmation_number"):
                st.success(f"🎉 **Confirmed:** {metadata['confirmation_number']}")
            
            if metadata.get("session_replay_url"):
                st.info(f"🎥 **Proof:** [View Browser Session]({metadata['session_replay_url']})")
            
            if metadata.get("booking_status"):
                if metadata["booking_status"] == "SUCCESS":
                    st.success("✅ **Real Reservation Made**")
                elif metadata["booking_status"] == "FAILED":
                    st.error("❌ **Booking Failed**")
                else:
                    st.warning("⚠️ **Partial Booking**")
        
        # Show contact extraction
        if speaker == "user" and metadata and metadata.get("extracted_contact"):
            contact_info = metadata["extracted_contact"]
            if any(contact_info.values()):
                st.success(f"🧠 **Contact Info Detected:** {', '.join([f'{k}: {v}' for k, v in contact_info.items() if v])}")
        
        if aud:
            st.audio(aud, format="audio/mp3")

# Handle new recording --------------------------------------------------------
if audio_blob:
    raw = audio_blob.getvalue()
    st.session_state.raw = raw

    with st.spinner("🎤 Transcribing your voice..."):
        user_msg = _transcribe(st.session_state.raw)
    
    # Extract contact info from user message
    extracted_contact = _extract_contact_info(user_msg)
    if extracted_contact:
        _update_user_contact(extracted_contact)
    
    st.chat_message("user").markdown(user_msg)
    
    # Store user message with extracted contact metadata
    user_metadata = {"extracted_contact": extracted_contact} if extracted_contact else None
    st.session_state.history.append(("user", user_msg, None, user_metadata))

    with st.spinner("🤖 Processing your restaurant request..."):
        agent_msg = _ask_agent(user_msg, st.session_state.user_contact)
    
    # Extract metadata from agent response
    metadata = {
        "confirmation_number": _extract_confirmation_number(agent_msg),
        "session_replay_url": _extract_session_replay_url(agent_msg),
        "booking_status": "SUCCESS" if "REAL BROWSER AUTOMATION SUCCESSFUL" in agent_msg else 
                         "FAILED" if "BOOKING FAILED" in agent_msg else 
                         "PARTIAL" if "PARTIAL" in agent_msg else None
    }
    
    tts_mp3 = _speak(agent_msg)

    st.chat_message("assistant").markdown(agent_msg)
    st.audio(tts_mp3, format="audio/mp3")
    st.session_state.history.append(("assistant", agent_msg, tts_mp3, metadata))

# Handle text input ----------------------------------------------------------
if send_text and text_input:
    # Extract contact info from user message
    extracted_contact = _extract_contact_info(text_input)
    if extracted_contact:
        _update_user_contact(extracted_contact)
    
    st.chat_message("user").markdown(text_input)
    
    # Store user message with extracted contact metadata
    user_metadata = {"extracted_contact": extracted_contact} if extracted_contact else None
    st.session_state.history.append(("user", text_input, None, user_metadata))

    with st.spinner("🤖 Processing your restaurant request..."):
        agent_msg = _ask_agent(text_input, st.session_state.user_contact)
    
    # Extract metadata from agent response
    metadata = {
        "confirmation_number": _extract_confirmation_number(agent_msg),
        "session_replay_url": _extract_session_replay_url(agent_msg),
        "booking_status": "SUCCESS" if "REAL BROWSER AUTOMATION SUCCESSFUL" in agent_msg else 
                         "FAILED" if "BOOKING FAILED" in agent_msg else 
                         "PARTIAL" if "PARTIAL" in agent_msg else None
    }
    
    tts_mp3 = _speak(agent_msg)

    st.chat_message("assistant").markdown(agent_msg)
    st.audio(tts_mp3, format="audio/mp3")
    st.session_state.history.append(("assistant", agent_msg, tts_mp3, metadata))
    
    # Clear text input after sending
    st.session_state.text_input = ""

# Footer
st.markdown("---")
st.markdown("**🔧 Powered by:** Exa Search • BrowserBase Automation • Google ADK • Streamlit") 