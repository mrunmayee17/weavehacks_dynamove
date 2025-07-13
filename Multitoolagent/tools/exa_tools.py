# tools/exa_tools.py
import os, httpx
from google.adk.tools import FunctionTool

def exa_search(query: str, k: int) -> str:
    """
    Returns a markdown bullet list of search hits with full content.
    """
    EXA_API_KEY = os.environ.get("EXA_API_KEY")
    EXA_ENDPOINT = "https://api.exa.ai/search"  
    if not EXA_API_KEY:
        raise RuntimeError("Set EXA_API_KEY env-var first")

    # CORRECTED API call with proper parameter structure
    r = httpx.post(
        EXA_ENDPOINT,
        json={
            "query": query, 
            "numResults": k,  # Changed from "k" to "numResults"
            "contents": {     # Wrapped content options in "contents" object
                "text": {
                    "maxCharacters": 2000,
                    "includeHtmlTags": False
                },
                "highlights": {
                    "numSentences": 3,
                    "highlightsPerUrl": 3
                }
            }
        },
        headers={"Authorization": f"Bearer {EXA_API_KEY}"},
    )
    r.raise_for_status()
    data = r.json()
    
    # Debug output
    print(f"DEBUG: Response keys: {data.keys()}")
    print(f"DEBUG: Cost breakdown: {data.get('costDollars', 'N/A')}")
    
    results = []
    for i, result in enumerate(data.get("results", []), 1):
        title = result.get("title", "No Title")
        url = result.get("url", "No URL")
        text = result.get("text", "No text available")
        highlights = result.get("highlights", [])
        
        # Debug text length
        print(f"DEBUG: Result {i} text length: {len(text)}")
        
        # Better formatting with more content
        if len(text) > 100:
            summary = text[:800] + "..." if len(text) > 800 else text
        else:
            summary = text
            
        # Include highlights if available
        highlight_text = ""
        if highlights:
            highlight_text = f"\n   🔍 **Highlights:** {' | '.join(highlights[:2])}"
        
        results.append(f"**{i}. {title}**\n   🔗 **URL:** {url}\n   📝 **Content:** {summary}{highlight_text}\n")
    
    return "\n".join(results)

# Create the FunctionTool
ExaSearchTool = FunctionTool(exa_search)