import asyncio, io, os, wave, uuid
import streamlit as st
from google.adk.runners  import Runner
from google.adk.sessions import InMemorySessionService
from google.genai        import types
import openai, tempfile, os, io, wave
from gtts import gTTS
import io
# import speech_recognition as sr

# ---- ① Load the agent ------------------------------------------------------
from multi_tool_agent.agent import root_agent

import assemblyai as aai
from dotenv import load_dotenv

# Load environment variables from .env.prod
load_dotenv('.env.prod')

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

@st.cache_resource
def init_services():
    sess_service = InMemorySessionService()

    runner = Runner(
        app_name        = "voice_demo",
        agent           = root_agent,
        session_service = sess_service,
    )

    # NEW: synchronous wrapper added in ADK 1.0
    user_id  = str(uuid.uuid4())
    session  = sess_service.create_session_sync(
        app_name="voice_demo",
        user_id=user_id,
    )

    return runner, session
runner, session = init_services()

import re

# --- Contact info memory ---
if "user_contact" not in st.session_state:
    st.session_state.user_contact = {"name": "", "email": "", "phone": ""}

def extract_contact_info(text: str) -> dict:
    """Extracts name, email, and phone from text."""
    contact = {}
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text)
    if email_match:
        contact["email"] = email_match.group()
    name_match = re.search(r"(?:my name is|i am|i'm)\s+([A-Za-z\s]+)", text, re.IGNORECASE)
    if name_match:
        contact["name"] = name_match.group(1).strip().title()
    phone_match = re.search(r"(\d{3})[^\d]?(\d{3})[^\d]?(\d{4})", text)
    if phone_match:
        contact["phone"] = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
    return contact

def update_user_contact(new_contact: dict):
    for k, v in new_contact.items():
        if v:
            st.session_state.user_contact[k] = v

def _transcribe(audio_bytes: bytes) -> str:
    """
    Uses AssemblyAI’s /transcribe endpoint.
    Pass raw WAV/MP3 bytes; SDK uploads & blocks until done.
    """
    if not aai.settings.api_key:
        return "⚠️  ASSEMBLYAI_API_KEY missing"

    try:
        transcriber = aai.Transcriber()
        transcript  = transcriber.transcribe(audio_bytes)   # bytes accepted ✔️ :contentReference[oaicite:0]{index=0}
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
        return buf.read()          # raw MP3 buffer
    except Exception as err:
        st.warning(f"TTS error: {err}")
        return b""

def _ask_agent(message: str) -> str:
    """Send *message* to the ADK agent and return its final reply, with slot-filling and tool call debug."""
    # Extract and update contact info
    contact = extract_contact_info(message)
    update_user_contact(contact)
    # Enhance message with contact info if available
    contact_info = st.session_state.user_contact
    if any(contact_info.values()):
        contact_str = ", ".join([f"{k}: {v}" for k, v in contact_info.items() if v])
        enhanced_message = f"{message}\n\n[User Contact Info: {contact_str}]"
    else:
        enhanced_message = message

    content = types.Content(role="user", parts=[types.Part(text=enhanced_message)])
    events = runner.run(user_id=session.user_id, session_id=session.id, new_message=content)

    # Debug: Print all tool calls and arguments
    tool_call_debug = []
    for evt in events:
        if hasattr(evt, "get_function_calls"):
            calls = evt.get_function_calls()
            for call in calls:
                tool_call_debug.append(str(call))
        if evt.is_final_response():
            # Optionally, you can parse evt.content.parts for more details
            return evt.content.parts[0].text + ("\n\n" + "\n".join(tool_call_debug) if tool_call_debug else "")

    return "⚠️  No response"

# ── 3. Streamlit front-end ----------------------------------------------------
st.title("🎙️  Voice Chat with an ADK Agent")
st.caption("Hold **Record**, speak, and wait for the reply.")

audio_blob = st.audio_input("Record your voice →")

# Show previous turns stored in Streamlit session_state
if "history" not in st.session_state:
    st.session_state.history = []    # list[(speaker, text, audio_bytes|None)]
if "raw" not in st.session_state:
    st.session_state.raw = None

for speaker, text, aud in st.session_state.history:
    with st.chat_message(speaker):
        st.markdown(text)
        if aud:
            st.audio(aud, format="audio/mp3")

# Handle new recording --------------------------------------------------------
if audio_blob:
    raw = audio_blob.getvalue()
    st.session_state.raw = raw

    with st.spinner("Transcribing…"):
        user_msg = _transcribe(st.session_state.raw)
    st.chat_message("user").markdown(user_msg)
    st.session_state.history.append(("user", user_msg, None))

    with st.spinner("Thinking…"):
        agent_msg = _ask_agent(user_msg)
    tts_mp3 = _speak(agent_msg)

    st.chat_message("assistant").markdown(agent_msg)
    st.audio(tts_mp3, format="audio/mp3")
    st.session_state.history.append(("assistant", agent_msg, tts_mp3))

# --- Optionally, add a sidebar to show remembered contact info ---
with st.sidebar:
    st.header("Your Contact Info")
    for k, v in st.session_state.user_contact.items():
        if v:
            st.write(f"**{k.title()}:** {v}")