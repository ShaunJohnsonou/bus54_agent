"""
Web search agent implementation using Pydantic AI.

This module contains the implementation of the web search agent using Pydantic AI.
The agent can search the web using either Brave Search API or SearXNG based on
environment configuration.
"""

from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from dotenv import load_dotenv
# from openai import AsyncOpenAI  # Unused import
from httpx import AsyncClient
from typing import Optional
import sys
import os
from utils.manifests import get_all_functions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.database_schema import database_schema
# Load environment variables
load_dotenv(override=True)




# ========== Agent Dependencies ==========
@dataclass
class AgentDeps:
    """
    Dependencies for the web search agent.
    
    Attributes:
        http_client: The HTTP client for making requests.
        brave_api_key: The Brave Search API key.
        searxng_base_url: The SearXNG base URL.
    """
    http_client: AsyncClient
    brave_api_key: Optional[str] = None
    searxng_base_url: Optional[str] = None


# ========== Pydantic AI Agent ==========
# agent = Agent(
#     get_model(),
#     model_settings={"temperature": 0.1, "think": True},
#     system_prompt=gather_data_to_provide_user_prompt(function_manifest=get_all_functions() , database_schema= database_schema)
# )

# @agent.tool
# async def web_search(ctx: RunContext[AgentDeps], query: str) -> str:
#     """
#     Search the web with a specific query and get a summary of the top search results.
    
#     Args:
#         ctx: The context for the agent including the HTTP client and optional Brave API key/SearXNG base url
#         query: The query for the web search
        
#     Returns:
#         A summary of the web search.
#         For Brave, this is a single paragraph.
#         For SearXNG, this is a list of the top search results including the most relevant snippet from the page.
#     """
#     #print("Calling web_search tool")
#     return await web_search_tool(
#         query, 
#         ctx.deps.http_client, 
#         ctx.deps.brave_api_key, 
#         ctx.deps.searxng_base_url
#     )


# async def run_web_search_agent(query: str) -> str:
#     """
#     Run the web search agent with the given query.
    
#     Args:
#         query: The search query.
        
#     Returns:
#         The agent's response.
        
#     Raises:
#         ValueError: If required environment variables are missing.
#     """
#     # Get the search provider dependencies
#     brave_api_key = os.getenv("BRAVE_API_KEY")
#     searxng_base_url = os.getenv("SEARXNG_BASE_URL")
    
#     # Create an async HTTP client
#     async with AsyncClient() as http_client:
#         # Create the dependencies
#         deps = AgentDeps(
#             http_client=http_client,
#             brave_api_key=brave_api_key,
#             searxng_base_url=searxng_base_url
#         )
        
#         # Run the agent
#         result = await agent.run(query, deps=deps)
        
#         return result.output
