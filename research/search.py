import os
from tavily import TavilyClient
from config.env import TAVILY_API_KEY

def web_search(query: str) -> str:
    """
    Executes a high-speed, agent-optimized web search.
    Returns a consolidated string of the most relevant snippets.
    """
    if not TAVILY_API_KEY:
        return "ERROR: TAVILY_API_KEY is missing from environment variables."

    try:
        # Initialize the Tavily client
        client = TavilyClient(api_key=TAVILY_API_KEY)
        
        # Execute the search optimized for LLM context
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True
        )
        
        # Format the response for the Groq engine
        results = []
        
        # Include the AI-generated direct answer if available
        if response.get("answer"):
            results.append(f"Direct Answer: {response['answer']}\n")
            
        # Append the top source snippets
        for idx, result in enumerate(response.get("results", [])):
            results.append(f"Source {idx + 1} ({result.get('url')}):\n{result.get('content')}\n")
            
        if not results:
            return f"No relevant data found for query: '{query}'"
            
        return "\n".join(results)

    except Exception as e:
        return f"ERROR: Web search failed. Exception: {str(e)}"