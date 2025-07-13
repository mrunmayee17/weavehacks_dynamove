# tools/exa_tools.py
import os, httpx
from google.adk.tools import FunctionTool

EXA_API_KEY = os.getenv("EXA_API_KEY")
EXA_ENDPOINT = "https://api.exa.ai/search"

def exa_search(query: str, k: int) -> str:
    """
    Returns a markdown bullet list of search hits with actual text content.
    """
    if not EXA_API_KEY:
        raise RuntimeError("Set EXA_API_KEY env-var first")

    # Updated payload with better content retrieval options
    payload = {
        "query": query,
        "numResults": k,
        "contents": {
            "text": True,
            "livecrawl": "fallback"  # Try live crawling if cached content isn't available
        }
    }
    
    try:
        r = httpx.post(
            EXA_ENDPOINT,
            json=payload,
            headers={"x-api-key": EXA_API_KEY},
            timeout=30,  # Increased timeout for live crawling
        )
        r.raise_for_status()
        
        response_data = r.json()
        
        # Debug print to see what we're getting
        print(f"DEBUG: Response keys: {response_data.keys()}")
        if 'costDollars' in response_data:
            print(f"DEBUG: Cost breakdown: {response_data['costDollars']}")
        
        hits = response_data.get("results", [])[:k]
        
        # Process the results
        results = []
        for i, h in enumerate(hits):
            title = h.get('title', 'No title')
            url = h.get('url', 'No URL')
            text = h.get('text', 'No text available')
            
            # Debug print for each result
            print(f"DEBUG: Result {i+1} text length: {len(text) if text != 'No text available' else 0}")
            
            # If no text, try to get highlights or summary as fallback
            if text == 'No text available' or not text:
                highlights = h.get('highlights', [])
                if highlights:
                    text = ' '.join(highlights)
                else:
                    summary = h.get('summary', '')
                    if summary:
                        text = summary
                    else:
                        text = 'No text content available'
            
            # Truncate text to reasonable length
            if len(text) > 500:
                text = text[:500] + "..."
            
            results.append(f"- **{title}** – {url}\n  {text}")
        
        return "\n".join(results)
        
    except httpx.HTTPStatusError as e:
        return f"HTTP Error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"Error searching with Exa: {str(e)}"

ExaSearchTool = FunctionTool(exa_search)

