"""
Web search tools for the Pydantic AI agent.
"""

from httpx import AsyncClient
from typing import Optional
import asyncio
import json


async def web_search_tool(
    query: str, 
    http_client: AsyncClient, 
    brave_api_key: Optional[str] = None,
    searxng_base_url: Optional[str] = None
) -> str:
    """
    Perform a web search using either Brave Search API or SearXNG.
    
    Args:
        query: The search query
        http_client: HTTP client for making requests
        brave_api_key: Optional Brave Search API key
        searxng_base_url: Optional SearXNG instance base URL
    
    Returns:
        Search results as a formatted string
    """
    
    # Try Brave Search first if API key is provided
    if brave_api_key:
        try:
            return await _brave_search(query, http_client, brave_api_key)
        except Exception as e:
            #print(f"Brave search failed: {e}")
    
    # Fall back to SearXNG if available
    if searxng_base_url:
        try:
            return await _searxng_search(query, http_client, searxng_base_url)
        except Exception as e:
            #print(f"SearXNG search failed: {e}")
    
    # If neither service is available, return a message
    return "Web search is not currently available. Please configure either Brave Search API key or SearXNG instance."


async def _brave_search(query: str, http_client: AsyncClient, api_key: str) -> str:
    """
    Search using Brave Search API.
    """
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key
    }
    params = {
        "q": query,
        "count": 5
    }
    
    response = await http_client.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    data = response.json()
    results = []
    
    if "web" in data and "results" in data["web"]:
        for result in data["web"]["results"][:5]:
            title = result.get("title", "No title")
            description = result.get("description", "No description")
            url = result.get("url", "No URL")
            results.append(f"**{title}**\n{description}\nSource: {url}\n")
    
    return "\n".join(results) if results else "No search results found."


async def _searxng_search(query: str, http_client: AsyncClient, base_url: str) -> str:
    """
    Search using SearXNG instance.
    """
    url = f"{base_url.rstrip('/')}/search"
    params = {
        "q": query,
        "format": "json",
        "engines": "google,bing,duckduckgo",
        "categories": "general"
    }
    
    response = await http_client.get(url, params=params)
    response.raise_for_status()
    
    data = response.json()
    results = []
    
    if "results" in data:
        for result in data["results"][:5]:
            title = result.get("title", "No title")
            content = result.get("content", "No content")
            url = result.get("url", "No URL")
            results.append(f"**{title}**\n{content}\nSource: {url}\n")
    
    return "\n".join(results) if results else "No search results found."
