"""Message display utilities for the Bus 54 Ticketing Assistant."""

import streamlit as st
import pandas as pd
from typing import List
from pydantic_ai.messages import ModelRequest, ModelResponse

from ui.components import create_user_message_bubble, create_assistant_message_bubble
from data.processor import process_gathered_data_to_dataframe, clean_response_content, should_display_table
from config.settings import DATAFRAME_HEIGHT


def display_chat_history():
    """Display all messages from the conversation history."""
    message_index = 0
    
    for message in st.session_state.user_friendly_response_agent_chat_history:
        if isinstance(message, ModelRequest):
            _display_user_message(message)
        elif isinstance(message, ModelResponse):
            _display_assistant_message(message, message_index // 2)
            message_index += 1


def _display_user_message(message: ModelRequest):
    """Display a user message."""
    for part in message.parts:
        if part.part_kind == 'user-prompt' and part.content:
            st.markdown(
                create_user_message_bubble(part.content),
                unsafe_allow_html=True
            )


def _display_assistant_message(message: ModelResponse, data_index: int):
    """Display an assistant message with optional data table."""
    for part in message.parts:
        if part.part_kind == 'text' and part.content:
            # Get corresponding gathered data if available
            gathered_data = _get_gathered_data_for_message(data_index)
            
            # Clean the content
            content = clean_response_content(part.content)
            
            # Display the text content
            st.markdown(
                create_assistant_message_bubble(content),
                unsafe_allow_html=True
            )
            
            # Display table if data is available
            if should_display_table(gathered_data):
                _display_data_table(gathered_data)


def _get_gathered_data_for_message(data_index: int):
    """Get gathered data for a specific message index."""
    if data_index < len(st.session_state.gathered_data_history):
        return st.session_state.gathered_data_history[data_index].get("gathered_data")
    return None


def _display_data_table(gathered_data):
    """Display gathered data as a table."""
    processed_data = process_gathered_data_to_dataframe(gathered_data)
    
    if isinstance(processed_data, pd.DataFrame):
        st.dataframe(processed_data, use_container_width=True, height=DATAFRAME_HEIGHT)
    elif isinstance(processed_data, str):
        st.markdown(processed_data)


def display_user_input(user_input: str):
    """Display user input as a chat bubble."""
    st.markdown(
        create_user_message_bubble(user_input),
        unsafe_allow_html=True
    )


def display_assistant_response_with_data(response_content: str, gathered_data, container):
    """Display assistant response with data table."""
    # Clean and display the response
    content = clean_response_content(response_content)
    styled_response = create_assistant_message_bubble(content)
    
    with container:
        st.markdown(styled_response, unsafe_allow_html=True)
        
        # Display data table if available
        if should_display_table(gathered_data):
            processed_data = process_gathered_data_to_dataframe(gathered_data)
            
            if isinstance(processed_data, pd.DataFrame):
                st.dataframe(processed_data, use_container_width=True, height=DATAFRAME_HEIGHT)
            elif isinstance(processed_data, str):
                st.markdown(processed_data)