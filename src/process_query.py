from pydantic_ai import Agent
import sys    
from typing import List
from pydantic_ai.messages import (
        ModelMessage,
        ModelRequest,
        ModelResponse,
        TextPart,
        UserPromptPart,
    )
sys.path.append("C:/Users/ShaunJohnson/repos/chatbot_agent")
from utils.models import mixtral_8x7b_model, gemma3_27b_model, gemma3_12b_model, tinyllama_model, llama3_2_ollama_model, gpt_4o_openai_model, deepstreamr1_32b_model
# from utils.functions import get_underutilized_servers, get_overutilized_servers, get_deallocatable_resources, get_current_utilization, get_memory_usage_trend, get_breaching_hosts, get_servicenow_flags
def query_agent(query: str, agent: Agent, message_history):
    # message_history: list[ModelMessage] = [
    #     ModelRequest([UserPromptPart(content='What is 2+2?')]),
    #     ModelResponse([TextPart(content='2+2 equals 4.')]),
    #     ModelRequest([UserPromptPart(content='And what about 3+3?')]),
    #     ModelResponse([TextPart(content='3+3 equals 6.')]),
    # ]
    agent.model = gemma3_12b_model
    response = agent.run_sync(query)
    return response.__dict__["output"], response.all_messages()

def query_agent_convert_to_user_friendly_response(query: str, agent: Agent):
    agent.model = gemma3_12b_model
    response = agent.run_sync(query)
    return response.__dict__["output"]
