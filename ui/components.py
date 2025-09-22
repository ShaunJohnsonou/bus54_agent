"""UI components and styling for the Bus 54 Ticketing Assistant."""

import streamlit as st
from config.settings import LOGO_WIDTH


def apply_custom_styles():
    """Apply custom CSS styles to the Streamlit app."""
    st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
        background-color: #f5f8fa !important;
    }
    .st-emotion-cache-1r6slb0 {  /* Chat message container class */
        max-width: 90%;
        width: 90%;
    }
    .st-emotion-cache-eczf16 {  /* Chat container class */
        max-width: 100%;
    }
    /* Bus 54 branding colors */
    .stButton>button {
        background-color: #0066cc !important;
        color: white !important;
    }
    .stButton>button:hover {
        background-color: #004d99 !important;
    }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """Render the application header with logo and clear button."""
    logo_col, heading_col = st.columns([6, 1])
    
    with logo_col:
        try:
            st.markdown('<div style="padding-top: 0px;">', unsafe_allow_html=True)
            st.image("images/bus54_logo.png", width=LOGO_WIDTH)
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception:
            st.write("Bus 54 Logo")
    
    with heading_col:
        st.markdown('<div style="padding-top: 35px;">', unsafe_allow_html=True)
        if st.button("Clear Chat", use_container_width=True):
            clear_session_state()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def clear_session_state():
    """Clear all chat history and session state."""
    st.session_state.data_gathering_agent_chat_history = []
    st.session_state.user_friendly_response_agent_chat_history = []
    st.session_state.gathered_data_history = []
    if "messages" in st.session_state:
        st.session_state.messages = []


def initialize_session_state():
    """Initialize session state variables."""
    if "data_gathering_agent_chat_history" not in st.session_state:
        st.session_state.data_gathering_agent_chat_history = []
    if "user_friendly_response_agent_chat_history" not in st.session_state:
        st.session_state.user_friendly_response_agent_chat_history = []
    if "gathered_data_history" not in st.session_state:
        st.session_state.gathered_data_history = []
    if "messages" not in st.session_state:
        st.session_state.messages = []


def create_user_message_bubble(content: str) -> str:
    """Create HTML for user message bubble."""
    return f"""
    <div style="display: flex; justify-content: flex-end;">
        <div style="background-color: #e6f2ff; padding: 10px; border-radius: 10px; max-width: 80%; border: 1px solid #0066cc;">
            {content}
        </div>
    </div>
    """


def create_assistant_message_bubble(content: str) -> str:
    """Create HTML for assistant message bubble."""
    return f"""
    <div style="display: flex; justify-content: flex-start;">
        <div style="background-color: #FFFFFF; padding: 10px; border-radius: 10px; max-width: 80%; border: 1px solid #0066cc; box-shadow: 0 1px 3px rgba(0,102,204,0.2);">
            {content}
        </div>
    </div>
    """