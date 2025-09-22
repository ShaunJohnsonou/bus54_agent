"""Agent management and streaming utilities for the Absa Chatbot."""

import json
import streamlit as st
import uuid
from datetime import datetime
from httpx import AsyncClient
from pydantic_ai import Agent
from pydantic_ai.messages import PartDeltaEvent, PartStartEvent, TextPartDelta
import sys
import os
sys.path.append("/software/source/data")
import telementry_tools
from Basic_Pydantic_AI_Agent.src.agent import AgentDeps
from utils.system_prompts import convert_to_user_friendly_response_prompt_alias_data
from utils.manifests import get_all_functions
from utils.database_schema import database_schema
from config.settings import GATHER_DATA_MODEL, USER_FRIENDLY_RESPONSE_MODEL, AGENT_SETTINGS
from src import functions


class AgentManager:
    """Manages agent interactions and streaming responses."""
    
    def __init__(self):
        self.data_gathering_agent = self._create_data_gathering_agent()
    
    def _create_user_friendly_agent(self, data_structure_description: str) -> Agent:
        """Create the user-friendly response agent."""
        return Agent(
            model=USER_FRIENDLY_RESPONSE_MODEL,
            model_settings={"temperature": AGENT_SETTINGS["user_friendly_temperature"]},
            system_prompt=convert_to_user_friendly_response_prompt_alias_data(
                data_structure_description=data_structure_description
            )
        )
    
    async def run_agent_with_streaming(self, agent_name: str, agent: Agent, user_input: str, conversation_id: str = None, enable_message_history: bool = False):
        """Run an agent with streaming response."""
        try:
            async with AsyncClient() as http_client:
                agent_deps = AgentDeps(http_client=http_client)
                
                message_history = self._get_message_history(agent_name, enable_message_history)
                
                async with agent.iter(user_input, deps=agent_deps, message_history=message_history) as run:
                    async for node in run:
                        if Agent.is_model_request_node(node):
                            async with node.stream(run.ctx) as request_stream:
                                async for event in request_stream:
                                    if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                                        yield event.part.content
                                    elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                                        yield event.delta.content_delta
                
                # Update message history with conversation ID
                new_messages = run.result.new_messages()
                
                # If conversation_id is not provided, generate a new one
                if not conversation_id:
                    conversation_id = str(uuid.uuid4())
                    if not "current_conversation_id" in st.session_state:
                        st.session_state.current_conversation_id = conversation_id
                
                # Add metadata to messages
                for msg in new_messages:
                    if not hasattr(msg, 'metadata'):
                        msg.metadata = {}
                    msg.metadata['conversation_id'] = conversation_id
                
                self._update_message_history(agent_name, new_messages, conversation_id)
                
        except Exception as e:
            #print(f"Error in run_agent_with_streaming: {str(e)}")
            raise
    
    def _get_message_history(self, agent_name: str, enable_message_history: bool):
        """Get message history for the specified agent."""
        if not enable_message_history:
            return None
        
        if agent_name == "data_gathering_agent":
            return st.session_state.data_gathering_agent_chat_history
        elif agent_name == "user_friendly_response_agent":
            return st.session_state.user_friendly_response_agent_chat_history
        return None
    
    def _update_message_history(self, agent_name: str, new_messages, conversation_id: str = None):
        """Update message history for the specified agent."""
        # Update traditional history lists
        if agent_name == "data_gathering_agent":
            st.session_state.data_gathering_agent_chat_history.extend(new_messages)
        elif agent_name == "user_friendly_response_agent":
            st.session_state.user_friendly_response_agent_chat_history.extend(new_messages)
            
        # Update the unified conversation structure if conversation_id is provided
        if conversation_id:
            if "conversations" not in st.session_state:
                st.session_state.conversations = {}
                
            if conversation_id not in st.session_state.conversations:
                st.session_state.conversations[conversation_id] = {
                    'messages': [],
                    'gathered_data': None,
                    'timestamp': datetime.now().isoformat(),
                }
            
            st.session_state.conversations[conversation_id]['messages'].extend(new_messages)
    
    async def handle_complete_interaction(self, user_input: str):
        """Handle the complete user interaction with both agents."""
        try:
            # Phase 1: Get structured response for data gathering
            async with AsyncClient() as http_client:
                agent_deps = AgentDeps(http_client=http_client)
                result = await self.data_gathering_agent.run(user_input, deps=agent_deps)
                
                structured_response = result.output.replace("```json", "").replace("```", "")
                
                if not structured_response:
                    yield None, None, None
                    return
                
                # Convert structured response and gather relevant information
                relevant_response = json.loads(structured_response)
                response_type, gathered_relevant_information, alias_gathered_relevant_information, agent_logs = gather_relevant_information(
                    relevant_response, user_input, functions
                )
                
                # Phase 2: Create user-friendly response agent and stream response
                user_friendly_agent = self._create_user_friendly_agent(alias_gathered_relevant_information)
                
                displayed_result = ""
                # Generate conversation ID for this interaction if not exists
                if not "current_conversation_id" in st.session_state or not st.session_state.current_conversation_id:
                    conversation_id = str(uuid.uuid4())
                    st.session_state.current_conversation_id = conversation_id
                else:
                    conversation_id = st.session_state.current_conversation_id
                    
                generator = self.run_agent_with_streaming(
                    "user_friendly_response_agent", 
                    user_friendly_agent, 
                    user_input,
                    conversation_id,
                    enable_message_history=True
                )
                
                # Stream the response chunks
                async for message in generator:
                    displayed_result += message
                    yield message
                
                # Generate conversation ID for this interaction if not exists
                if not "current_conversation_id" in st.session_state or not st.session_state.current_conversation_id:
                    conversation_id = str(uuid.uuid4())
                    st.session_state.current_conversation_id = conversation_id
                else:
                    conversation_id = st.session_state.current_conversation_id
                    
                # Store in unified conversation structure
                if "conversations" in st.session_state and conversation_id in st.session_state.conversations:
                    st.session_state.conversations[conversation_id]['gathered_data'] = gathered_relevant_information
                    st.session_state.conversations[conversation_id]['user_query'] = user_input
                    st.session_state.conversations[conversation_id]['response'] = displayed_result
                    
                # Yield the final result as a tuple
                yield (structured_response, displayed_result, gathered_relevant_information)
                
        except Exception as e:
            #print(f"Error in complete interaction: {str(e)}")
            import traceback
            traceback.print_exc()
            yield None, None, None


# Global agent manager instance
agent_manager = AgentManager()
