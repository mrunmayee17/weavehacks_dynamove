# weavehacks_dynamove

Dynamove: In-Vehicle Concierge Copilot @ Weavehacks 2025

---

## Overview

Dynamove is a voice-powered, AI-driven in-vehicle concierge copilot built for the Weavehacks 2025 hackathon. It enables users to search for restaurants, get reviews, and make real reservations using natural language—either by voice or text. The system leverages advanced LLMs, real-time web search, and browser automation to deliver a seamless, verifiable booking experience.

---

## Features

- **Conversational AI:** Powered by Google Gemini models, the agent can understand and respond to natural language queries.
- **Voice and Text Input:** Users can interact via voice (with transcription) or text.
- **Restaurant Search:** Uses Exa API for real-time, web-scale restaurant search and review aggregation.
- **Real Reservation Booking:** Employs BrowserBase and Playwright to automate real bookings on platforms like OpenTable, Resy, and Yelp.
- **Session Replay Proof:** Provides session replay links as verifiable proof of real browser automation.
- **Contact Memory:** Remembers user contact info (name, email, phone) for seamless repeated use.
- **Streamlit UI:** Modern, interactive web interface for both desktop and in-vehicle use.
- **Hackathon-Ready:** Modular, extensible, and easy to demo or adapt for new use cases.

---

## How it Works

1. **User speaks or types a request** (e.g., “Book a table for 2 at Hinodeya tomorrow at 7pm”).
2. **Contact info is extracted** from the conversation or entered manually.
3. **The agent searches for restaurants** using Exa, aggregates reviews, and finds booking platforms.
4. **Browser automation is triggered** to make a real reservation, filling out forms and submitting details.
5. **Confirmation and session replay** are provided to the user for verification.
6. **All interactions are displayed** in a chat-style interface, with audio responses and booking status.

---

## Architecture

- **Streamlit Frontend:** (`Ui/app.py`, `Multitoolagent/app.py`)
  - Provides the main user interface, handles audio and text input, displays conversation, and manages session state.
- **Agent Logic:** (`Ui/multi_tool_agent/agent.py`, `Multitoolagent/multi_tool_agent/agent.py`)
  - Defines the root agent, its capabilities, and the tools it can use.
- **Tools:**
  - **Exa Search:** (`tools/exa_tools.py`, `Multitoolagent/tools/exa_tools.py`)
    - Integrates Exa API for web search and review aggregation.
  - **BrowserBase Automation:** (`tools/browserbase_tools.py`, `Multitoolagent/tools/browserbase_tools.py`)
    - Uses Playwright and BrowserBase for real browser automation and booking.
- **Testing:**
  - `test.py`: Tests agent search and response.
  - `test_real_booking.py`: Tests real booking automation and session replay.
- **Environment Management:**
  - `.env.prod`: Stores all API keys (never committed to git).
  - `.gitignore`: Ensures sensitive files are not tracked.

---

## Setup & Usage

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd weavehacks_dynamove
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
# Also install Playwright and BrowserBase if using real automation:
pip install playwright browserbase
playwright install
```

### 3. Set up environment variables

Create a `.env.prod` file in the root directory with the following (get your own API keys):

```
ASSEMBLYAI_API_KEY=your-assemblyai-key
GOOGLE_API_KEY=your-google-api-key
BROWSERBASE_API_KEY=your-browserbase-key
BROWSERBASE_PROJECT_ID=your-browserbase-project-id
EXA_API_KEY=your-exa-key
```

### 4. Run the app

For the main Streamlit UI:

```bash
streamlit run Ui/app.py
# or
streamlit run Multitoolagent/app.py
```

### 5. Test automation

```bash
python test.py
python test_real_booking.py
```

---

## Example Requests

- “My name is John Doe, email john@example.com”
- “Find the best ramen in San Jose”
- “Book a table for 2 at Hinodeya tomorrow at 7pm”
- “Search for Italian restaurants with good reviews”

---

## Hackathon Context

This project was built for [Weavehacks 2025](https://lu.ma/weavehacks), a premier hackathon focused on next-generation mobility, AI, and in-vehicle experiences. Dynamove demonstrates how AI copilots can transform the way we discover, book, and experience dining on the go.

---

## Team & Credits

- Built by Mrunmayee Rane, Amala Deshmukh, and Rohan Rao for Weavehacks 2025
- Powered by: Google ADK, Gemini, Exa, BrowserBase, Playwright, AssemblyAI, Streamlit

---

## License

MIT License
