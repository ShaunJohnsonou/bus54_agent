import streamlit as st
import asyncio
import sys
import json
import os
import uuid
import time
from datetime import datetime
from src import functions
import json
# Retry Configuration Constants
MAX_RETRIES = 3  # Maximum number of retry attempts
RETRY_DELAY = 1.0  # Delay in seconds between retries
from utils.system_prompts import convert_to_user_friendly_response_prompt
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Basic_Pydantic_AI_Agent.src.agent import AgentDeps
from utils.manifests import get_all_functions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# from utils.mcp_server import return_function_that_agent_has_used
# from utils.system_prompts import 
# Import all the message part classes from Pydantic AI
from utils.models import gpt_4o_openai_model, gemma3_12b_model, gemma3_27b_model, gemma3_27b_it_qat_model, gpt_oss_20b_model
from pydantic_ai import Agent, agent
from pydantic_ai.messages import ModelRequest, ModelResponse, PartDeltaEvent, PartStartEvent, TextPartDelta
from utils.database_schema import database_schema
# from utils.output_structure import DataGatheringOutputType
import logfire
from dotenv import load_dotenv
from httpx import AsyncClient
from pydantic_ai.toolsets import FunctionToolset
load_dotenv()
logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))
logfire.instrument_pydantic_ai()

GATHER_DATA_MODEL = gpt_4o_openai_model
USER_FRIENDLY_RESPONSE_MODEL = gpt_4o_openai_model


user_information = {
    "name": "John",
    "surname": "Doe",
    "phone": "0793181101",
    "Next of Kin": "Jane Doe",
    "Next of Kin Phone": "0793181102",
    "ID Number": "1234567890"
}


# Set Streamlit page configuration for wider display
st.set_page_config(
    page_title="Bus 54 Ticketing Assistant",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# Initialize unified conversation tracking structure
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
    with open("cache.txt", "w") as file:
        file.write("")

# For backward compatibility and transition
if "data_gathering_agent_chat_history" not in st.session_state:
    st.session_state.data_gathering_agent_chat_history = []
if "user_friendly_response_agent_chat_history" not in st.session_state:
    st.session_state.user_friendly_response_agent_chat_history = []
if "gathered_data_history" not in st.session_state:
    st.session_state.gathered_data_history = []
if "operations" not in st.session_state:
    st.session_state.operations = []

# Initialize ticket-related session state defaults
if "ticket_pdf_ready" not in st.session_state:
    st.session_state["ticket_pdf_ready"] = False
if "ticket_pdf_bytes" not in st.session_state:
    st.session_state["ticket_pdf_bytes"] = None
if "ticket_pdf_filename" not in st.session_state:
    st.session_state["ticket_pdf_filename"] = None
if "ticket_ready" not in st.session_state:
    st.session_state["ticket_ready"] = False
if "ticket_html_data_url" not in st.session_state:
    st.session_state["ticket_html_data_url"] = None
if "ticket_html_filename" not in st.session_state:
    st.session_state["ticket_html_filename"] = None
if "ticket_html" not in st.session_state:
    st.session_state["ticket_html"] = None

# Message to data mapping for robust tracking
if "message_data_mapping" not in st.session_state:
    st.session_state.message_data_mapping = {}

# Current conversation tracking
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None

def _compute_dataframe_height(dataframe, max_height: int = 600) -> int:
    """Compute a tight height for st.dataframe based on row count.

    Returns 0 if there are no rows (so the caller can skip rendering).
    """
    try:
        row_count = len(dataframe.index) if hasattr(dataframe, 'index') else len(dataframe)
    except Exception:
        row_count = 0

    if row_count <= 0:
        return 0

    header_height = 38
    row_height = 35
    padding_height = 16
    computed_height = header_height + (row_count * row_height) + padding_height
    return computed_height if computed_height < max_height else max_height

def display_message_part(part):
    """
    Display a single part of a message in the Streamlit UI.
    Customize how you display system prompts, user prompts,
    tool calls, tool returns, etc.
    """
    # User messages
    if part.part_kind == 'user-prompt' and part.content:
        with st.chat_message("user"):
            st.markdown(part.content)
    # AI messages
    elif part.part_kind == 'text' and part.content:
        with st.chat_message("assistant"):
            st.markdown(part.content)             

async def run_agent_with_streaming(agent_name, agent, user_input, conversation_id, enable_message_history=False):
    try:
        async with AsyncClient() as http_client:
            agent_deps = AgentDeps(
                http_client=http_client
            )   

            if agent_name == "data_gathering_agent":
                message_history=st.session_state.data_gathering_agent_chat_history
            elif agent_name == "user_friendly_response_agent":
                message_history=st.session_state.user_friendly_response_agent_chat_history
            else:
                pass

            async with agent.iter(user_input, deps=agent_deps, message_history=message_history if enable_message_history else None) as run:
            # async with agent.iter(user_input, deps=agent_deps) as run:
                async for node in run:
                    if Agent.is_model_request_node(node):
                        # A model request node => We can stream tokens from the model's request
                        async with node.stream(run.ctx) as request_stream:
                            async for event in request_stream:
                                if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                                        yield event.part.content
                                elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                                        delta = event.delta.content_delta
                                        yield delta
                
                # Add messages to appropriate history with conversation_id metadata
                new_messages = run.result.new_messages()
                
                # Add conversation_id metadata to each message
                for msg in new_messages:
                    # Store the conversation ID as metadata in the messages
                    if not hasattr(msg, 'metadata'):
                        msg.metadata = {}
                    msg.metadata['conversation_id'] = conversation_id
                
                # Update the session state
                if agent_name == "data_gathering_agent":
                    st.session_state.data_gathering_agent_chat_history.extend(new_messages)
                elif agent_name == "user_friendly_response_agent":
                    st.session_state.user_friendly_response_agent_chat_history.extend(new_messages)
                    
                    # Update the unified conversation structure
                    if conversation_id not in st.session_state.conversations:
                        st.session_state.conversations[conversation_id] = {
                            'messages': [],
                            'gathered_data': None,
                            'timestamp': datetime.now().isoformat(),
                        }
                    
                    st.session_state.conversations[conversation_id]['messages'].extend(new_messages)
    
    except Exception as e:
        # Log the error and re-raise it to be handled in the main function
        #print(f"Error in run_agent_with_streaming: {str(e)}")
        raise       


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~ Main Function with UI Creation ~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def get_message_data(message_id):
    """Get the data associated with a specific message by ID."""
    if message_id in st.session_state.message_data_mapping:
        return st.session_state.message_data_mapping[message_id]
    return None

def get_conversation_data(conversation_id):
    """Get all data for a specific conversation."""
    if conversation_id in st.session_state.conversations:
        return st.session_state.conversations[conversation_id]
    return None

def validate_conversation_state():
    """Validate the consistency of conversation state and fix any issues."""
    # Ensure all conversations have proper structure
    for conv_id in st.session_state.conversations:
        if 'messages' not in st.session_state.conversations[conv_id]:
            st.session_state.conversations[conv_id]['messages'] = []
        if 'gathered_data' not in st.session_state.conversations[conv_id]:
            st.session_state.conversations[conv_id]['gathered_data'] = None
        if 'timestamp' not in st.session_state.conversations[conv_id]:
            st.session_state.conversations[conv_id]['timestamp'] = datetime.now().isoformat()
    
    # Ensure all messages in history have conversation IDs
    for i, msg in enumerate(st.session_state.user_friendly_response_agent_chat_history):
        if not hasattr(msg, 'metadata') or 'conversation_id' not in msg.metadata:
            # For backwards compatibility, assign to a default conversation
            if st.session_state.current_conversation_id:
                if not hasattr(msg, 'metadata'):
                    msg.metadata = {}
                msg.metadata['conversation_id'] = st.session_state.current_conversation_id

def main():
    # Add custom CSS to make the chat container wider
    st.markdown("""
    <style>
    /* Make the app take full width */
    .stApp {
        max-width: none !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        background-color: #f5f8fa !important;
    }
    /* Ensure chat containers use most of the width */
    .st-emotion-cache-1r6slb0, .st-emotion-cache-eczf16, .block-container {
        max-width: 100% !important;
        width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
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
    
    # Sidebar removed

    logo_col, heading_col = st.columns([6, 1])
    with logo_col:
        try:
            # Add a small padding at the top of the image
            st.markdown('<div style="padding-top: 0px;">', unsafe_allow_html=True)
            st.image("images/bus54_logo.png", width=150)
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception:
            st.write("Bus 54 Logo")
    with heading_col:
        # Adjust margin to move heading closer to logo and vertically center
        st.markdown('<div style="padding-top: 35px;">', unsafe_allow_html=True)
        if st.button("Clear Chat", use_container_width=True):
            # Clear all conversation data
            st.session_state.conversations = {}
            st.session_state.message_data_mapping = {}
            st.session_state.current_conversation_id = None
            
            # For backward compatibility
            st.session_state.data_gathering_agent_chat_history = []
            st.session_state.user_friendly_response_agent_chat_history = []
            st.session_state.gathered_data_history = []
            # Reset ticket state
            st.session_state["ticket_ready"] = False
            st.session_state["ticket_html_data_url"] = None
            st.session_state["ticket_html_filename"] = None
            if "messages" in st.session_state:
                st.session_state.messages = []
            st.rerun()
        # Manual refresh button to force a full rerun
        if st.button("Refresh", use_container_width=True):
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Top-right Generate Ticket button (only if ticket.html exists)
        download_button_area = st.empty()
        import os
        ticket_path_exists = os.path.exists("ticket.html")
        if ticket_path_exists:
            with download_button_area:
                if st.button("Generate Ticket", key="header_download_ticket"):
                    from streamlit.components.v1 import html as _st_html
                    import base64 as _b64
                    try:
                        # Read the original ticket.html
                        with open("ticket.html", "r", encoding="utf-8") as _f:
                            html_raw = _f.read()
                        
                        # Create an exact copy with a new name
                        with open("ticket_copy.html", "w", encoding="utf-8") as _f:
                            _f.write(html_raw)
                        
                        # Delete the original ticket.html
                        os.remove("ticket.html")
                        
                    except Exception:
                        html_raw = st.session_state.get("ticket_html") or "<html><body><p>Ticket not found.</p></body></html>"
                        # Create the copy even if original doesn't exist
                        with open("ticket_copy.html", "w", encoding="utf-8") as _f:
                            _f.write(html_raw)
                    
                    # Display the recreated ticket
                    b64 = _b64.b64encode(html_raw.encode("utf-8")).decode("utf-8")
                    _st_html(f"""
                    <script>
                      (function() {{
                        const html = atob('{b64}');
                        const w = window.open('', '_blank');
                        if (w) {{
                          w.document.open();
                          w.document.write(html);
                          w.document.close();
                        }}
                      }})();
                    </script>
                    """, height=0)
                

    # Initialize chat history in session state if not present
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display all messages from the conversation history with custom styling
    # Validate conversation state for history display
    
    # First validate conversation state for consistency
    validate_conversation_state()
    
    # Group messages by conversation_id for display
    conversation_messages = {}
    for message in st.session_state.user_friendly_response_agent_chat_history:
        conv_id = message.metadata.get('conversation_id', 'unknown') if hasattr(message, 'metadata') else 'unknown'
        if conv_id not in conversation_messages:
            conversation_messages[conv_id] = []
        conversation_messages[conv_id].append(message)
    
    # Display messages by conversation, in the order they appear in the history
    for message in st.session_state.user_friendly_response_agent_chat_history:
        if isinstance(message, ModelRequest):
            # Display user messages - right-aligned with light grey background
            for part in message.parts:
                if part.part_kind == 'user-prompt' and part.content:
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: flex-end;">
                            <div style="background-color: #e6f2ff; padding: 10px; border-radius: 10px; max-width: 80%; border: 1px solid #0066cc;">
                                {part.content}
                            </div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
        elif isinstance(message, ModelResponse):
            # Display assistant messages - left-aligned with white background
            for part in message.parts:
                if part.part_kind == 'text' and part.content:
                    # Get the conversation ID from the message metadata
                    conv_id = message.metadata.get('conversation_id', None) if hasattr(message, 'metadata') else None
                    
                    # Get the corresponding gathered data if available
                    gathered_data = None
                    
                    # Try to get data from conversation structure first
                    if conv_id and conv_id in st.session_state.conversations:
                        gathered_data = st.session_state.conversations[conv_id].get('gathered_data')
                    
                    # Fallback to message ID mapping if needed
                    if gathered_data is None and hasattr(message, 'id'):
                        gathered_data = get_message_data(message.id)
                    
                    # Process the content and check if we need to display a table
                    content = part.content
                    has_table = False
                    
                    # We'll always display the table at the bottom if data is available
                    if gathered_data is not None:
                        # No need to look for placeholders anymore
                        has_table = True
                        
                    # Use Streamlit's layout system for integrated display
                    left_spacer, content_col, right_spacer = st.columns([0.1, 0.85, 0.05])
                    
                    with content_col:
                        # Use Streamlit's container with custom styling for the response
                        history_container = st.container()
                        with history_container:
                            # Apply container styling
                            st.markdown("""
                            <style>
                            .history-response-container {
                                background-color: #FFFFFF;
                                padding: 15px;
                                border-radius: 10px;
                                border: 1px solid #0066cc;
                                box-shadow: 0 1px 3px rgba(0,102,204,0.2);
                                margin-bottom: 10px;
                            }
                            </style>
                            """, unsafe_allow_html=True)
                            
                            # Display the text content
                            st.markdown(f"""
                            <div class="history-response-container">
                                {content}
                            </div>
                            """, unsafe_allow_html=True)
                            
    # Chat input for the user
    user_input = st.chat_input("How can I help with your bus ticket needs today?")

    if user_input:
        # Display user prompt in the UI - right-aligned with light grey background
        st.markdown(
            f"""
            <div style="display: flex; justify-content: flex-end;">
                <div style="background-color: #e6f2ff; padding: 10px; border-radius: 10px; max-width: 80%; border: 1px solid #0066cc;">
                    {user_input}
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )

        # Display the assistant's response without icon - left-aligned
        # Create a container for the assistant's response
        assistant_container = st.container()
        with assistant_container:
            # Create a placeholder for the response - will be styled in the markdown
            message_placeholder = st.empty()
            
            try:
                # Use a single async function to handle all async operations
                async def handle_complete_interaction():
                    try:
                        # Generate conversation ID for this interaction
                        conversation_id = str(uuid.uuid4())
                        st.session_state.current_conversation_id = conversation_id
                        
                        # Phase 1: Get structured response for data gathering
                        async with AsyncClient() as http_client:
                            def get_entire_bus_schedule():
                                """
                                Retrieves the complete bus schedule data from the Nigeria bus schedule CSV file.
                                
                                This function reads all bus schedule entries from the CSV file containing Nigerian bus routes,
                                departure times, destinations, arrival times, and bus company information. It's designed
                                to provide comprehensive schedule data for LLM agents to analyze and present to users.
                                
                                Returns:
                                    list: A list of dictionaries, where each dictionary represents a bus schedule entry
                                          with keys: 'departure_time', 'departure_location', 'destination', 
                                          'arrival_time', 'bus_name'. Returns an empty list if file is not found
                                          or if any error occurs during reading.
                                
                                Example return format:
                                    [
                                        {
                                            'departure_time': '08:00',
                                            'departure_location': 'Lagos',
                                            'destination': 'Abuja',
                                            'arrival_time': '14:30',
                                            'bus_name': 'God is Good Motors'
                                        },
                                        ...
                                    ]
                                """
                                import csv
                                import os
                                
                                # Construct path to the Nigeria bus schedule CSV file
                                csv_path = os.path.join("data", "simple_bus_schedule.csv")
                                schedule_data = []
                                
                                try:
                                    # Open and read the CSV file with proper encoding
                                    with open(csv_path, 'r', encoding='utf-8') as csvfile:
                                        reader = csv.DictReader(csvfile)
                                        # Convert each row to a dictionary and add to schedule_data
                                        for row in reader:
                                            schedule_data.append(row)
                                    return schedule_data
                                except FileNotFoundError:
                                    # Return empty list if CSV file doesn't exist
                                    return []
                                except Exception as e:
                                    # Return empty list for any other errors (permissions, encoding, etc.)
                                    return []

                            def download_pdf(departure_time: str, departure_location: str, arrival_time: str, destination: str, bus_name: str):
                                """
                                Generates an HTML ticket document with the provided information.
                                
                                Args:
                                    departure_time (str): The time of departure (e.g., "08:00")
                                    departure_location (str): The location of departure (e.g., "Lagos")
                                    arrival_time (str): The time of arrival (e.g., "14:30")
                                    destination (str): The destination location (e.g., "Abuja")
                                    bus_name (str): The name of the bus service (e.g., "God is Good Motors")
                                """
                                import base64
                                import uuid as _uuid
                                from datetime import datetime as _dt
                                brand_hex = "#0066cc"

                                customer_name = None
                                try:
                                    if isinstance(user_information, dict):
                                        first = user_information.get("name") or ""
                                        last = user_information.get("surname") or ""
                                        full_name = f"{first} {last}".strip()
                                        customer_name = full_name if full_name else None
                                except Exception:
                                    customer_name = None

                                issued_at = _dt.now().strftime("%Y-%m-%d %H:%M")
                                ticket_id = str(_uuid.uuid4())[:8].upper()

                                html_content = f"""
                                <!doctype html>
                                <html lang=\"en\">
                                  <head>
                                    <meta charset=\"utf-8\"/>
                                    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>
                                    <title>Bus 54 Ticket</title>
                                    <style>
                                      body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Liberation Sans', sans-serif; background:#f5f8fa; margin:0; padding:24px; }}
                                      .header {{ background:{brand_hex}; color:#fff; padding:20px 24px; display:flex; align-items:center; }}
                                      .header h1 {{ margin:0 0 0 12px; font-size:22px; font-weight:700; }}
                                      .ticket {{ background:#fff; border:1px solid {brand_hex}; border-radius:10px; box-shadow:0 1px 3px rgba(0,102,204,0.2); margin-top:16px; padding:20px; }}
                                      .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-top:10px; }}
                                      .label {{ color:#6b7280; font-size:12px; margin-bottom:4px; }}
                                      .value {{ color:#111827; font-weight:700; font-size:16px; }}
                                      .foot {{ color:#6b7280; font-size:12px; margin-top:18px; }}
                                      .brand {{ color:{brand_hex}; font-weight:700; }}
                                    </style>
                                  </head>
                                  <body>
                                    <div class=\"header\">
                                      <div style=\"font-weight:800; letter-spacing:.5px;\">BUS 54</div>
                                      <h1>Ticket</h1>
                                    </div>
                                    <div class=\"ticket\">
                                      <div class=\"grid\">
                                        <div>
                                          <div class=\"label\">Passenger</div>
                                          <div class=\"value\">{customer_name or 'N/A'}</div>
                                        </div>
                                        <div>
                                          <div class=\"label\">Bus Company</div>
                                          <div class=\"value\">{bus_name}</div>
                                        </div>
                                        <div>
                                          <div class=\"label\">From</div>
                                          <div class=\"value\">{departure_location}</div>
                                        </div>
                                        <div>
                                          <div class=\"label\">To</div>
                                          <div class=\"value\">{destination}</div>
                                        </div>
                                        <div>
                                          <div class=\"label\">Departure</div>
                                          <div class=\"value\">{departure_time}</div>
                                        </div>
                                        <div>
                                          <div class=\"label\">Arrival</div>
                                          <div class=\"value\">{arrival_time}</div>
                                        </div>
                                        <div>
                                          <div class=\"label\">Issued At</div>
                                          <div class=\"value\">{issued_at}</div>
                                        </div>
                                        <div>
                                          <div class=\"label\">Ticket ID</div>
                                          <div class=\"value\">{ticket_id}</div>
                                        </div>
                                      </div>
                                      <div class=\"foot\">Please arrive 30 minutes before departure. Bring a valid ID. <span class=\"brand\">Bus 54</span></div>
                                    </div>
                                  </body>
                                </html>
                                """

                                # Save HTML content to file system
                                with open("ticket.html", "w", encoding="utf-8") as f:
                                    f.write(html_content)
                                
                                st.session_state["ticket_html"] = html_content
                                b64_html = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
                                data_url = f"data:text/html;base64,{b64_html}"

                                safe_time = (departure_time or "").replace(":", "-")
                                html_filename = f"bus54_ticket_{ticket_id}_{destination}_{safe_time}.html"

                                st.session_state["ticket_ready"] = True
                                st.session_state["ticket_html_data_url"] = data_url
                                st.session_state["ticket_html_filename"] = html_filename

                                return f"Your ticket has been generated for {departure_location} → {destination} at {departure_time}. The generated ticket can be downloaded above via the 'Generate Ticket' button."

                            def book_bus_ticket(
                                departure_time: str, 
                                departure_location: str, 
                                arrival_time: str, 
                                destination: str, 
                                bus_name: str,
                                available_seats: int = 1
                            ):
                                """
                                Books a bus ticket with the provided information and returns a confirmation message.
                                Also updates the CSV file to reduce available seats by 1.
                                
                                Args:
                                    departure_time (str): The time of departure (e.g., "08:00")
                                    departure_location (str): The location of departure (e.g., "Lagos")
                                    arrival_time (str): The time of arrival (e.g., "14:30")
                                    destination (str): The destination location (e.g., "Abuja")
                                    bus_name (str): The name of the bus service (e.g., "God is Good Motors")
                                    available_seats (int, optional): Number of available seats. Defaults to 1.
                                
                                Returns:
                                    str: A confirmation message with the booking details
                                """
                                # Create a ticket record
                                ticket = {
                                    'ticket_id': str(uuid.uuid4()),
                                    'departure_time': departure_time,
                                    'departure_location': departure_location,
                                    'arrival_time': arrival_time,
                                    'destination': destination,
                                    'bus_name': bus_name,
                                    'available_seats': available_seats,
                                    'booking_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                
                                # Save the ticket to cache.txt
                                with open("cache.txt", "a") as file:
                                    file.write(json.dumps(ticket) + "\n")
                                
                                # Update the CSV file to reduce available seats by 1
                                import csv
                                import os
                                
                                csv_path = os.path.join("data", "simple_bus_schedule.csv")
                                temp_path = os.path.join("data", "temp_schedule.csv")
                                
                                try:
                                    # Read all rows from the CSV
                                    rows = []
                                    with open(csv_path, 'r', encoding='utf-8') as csvfile:
                                        reader = csv.DictReader(csvfile)
                                        fieldnames = reader.fieldnames
                                        
                                        for row in reader:
                                            # Check if this is the matching bus entry
                                            if (row['departure_time'] == departure_time and 
                                                row['departure_location'] == departure_location and 
                                                row['destination'] == destination and 
                                                row['bus_name'] == bus_name):
                                                
                                                # Reduce available seats by 1
                                                current_seats = int(row['available_seats'])
                                                if current_seats > 0:
                                                    row['available_seats'] = str(current_seats - 1)
                                            
                                            rows.append(row)
                                    
                                    # Write updated data back to a temporary file
                                    with open(temp_path, 'w', newline='', encoding='utf-8') as csvfile:
                                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                                        writer.writeheader()
                                        writer.writerows(rows)
                                    
                                    # Replace the original file with the updated one
                                    os.replace(temp_path, csv_path)
                                    
                                except Exception as e:
                                    # Log error but continue with booking
                                    print(f"Error updating CSV: {str(e)}")
                                                                            
                                # Return a detailed confirmation message
                                return f"Bus ticket booked successfully!\n\nDetails:\n- Ticket ID: {ticket['ticket_id']}\n- Departure: {departure_location} at {departure_time}\n- Arrival: {destination} at {arrival_time}\n- Bus: {bus_name}\n- Available Seats: {available_seats}\n\n⚠️ IMPORTANT: This booking is reserved for 24 hours. You must complete payment within 24 hours or your booking will be automatically cancelled and the seat will be released."
                            
                            def get_my_bookings():
                                """
                                Retrieves all booked tickets from the cache file.
                                
                                Returns:
                                    list: A list of dictionaries containing ticket information
                                """
                                try:
                                    with open("cache.txt", "r") as file:
                                        lines = file.readlines()
                                    
                                    # Parse each JSON line into a dictionary
                                    booked_tickets = []
                                    for line in lines:
                                        if line.strip():  # Skip empty lines
                                            try:
                                                ticket = json.loads(line.strip())
                                                booked_tickets.append(ticket)
                                            except json.JSONDecodeError:
                                                continue
                                    
                                    return booked_tickets
                                except FileNotFoundError:
                                    # Return empty list if file doesn't exist
                                    return []

                            def get_user_information():
                                """
                                Retrieves user information from the cache file.
                                
                                Returns:
                                    dict: A dictionary containing user information
                                """
                                return user_information

                            agent_toolset = FunctionToolset([get_entire_bus_schedule, book_bus_ticket, get_my_bookings, get_user_information, download_pdf])

                            # Phase 2: Stream user-friendly response
                            # Second agent call
                            agent_convert_to_user_friendly_response = Agent( 
                                model=USER_FRIENDLY_RESPONSE_MODEL,
                                model_settings={"temperature": 0.5, "think": False},
                               toolsets=[agent_toolset],
                                system_prompt=convert_to_user_friendly_response_prompt(),
                            )

                            
                            displayed_result = ""
                            generator = run_agent_with_streaming("user_friendly_response_agent", agent_convert_to_user_friendly_response, user_input, conversation_id, enable_message_history=True)
                            async for message in generator:
                                displayed_result += message
                                message_placeholder.markdown(displayed_result + "▌")

                            
                            # Final response without the cursor

                            # Clear the placeholder first
                            message_placeholder.empty()
                            
                            # Import our data display module
                            from ui.data_display import render_payload
                            
                            # Create integrated response container using Streamlit's layout system
                            with assistant_container:
                                # Create a column that matches our chat bubble width
                                left_spacer, content_col, right_spacer = st.columns([0.1, 0.85, 0.05])
                                
                                with content_col:
                                    # Use Streamlit's container with custom styling for the response
                                    response_container = st.container()
                                    with response_container:
                                        # Apply container styling
                                        st.markdown("""
                                        <style>
                                        .response-container {
                                            background-color: #FFFFFF;
                                            padding: 15px;
                                            border-radius: 10px;
                                            border: 1px solid #0066cc;
                                            box-shadow: 0 1px 3px rgba(0,102,204,0.2);
                                            margin-bottom: 10px;
                                        }
                                        </style>
                                        """, unsafe_allow_html=True)
                                        
                                        # Display the text response (strip the data flag if accidentally present)
                                        safe_text = displayed_result.replace("TEMPORARY_DATA_PLACEHOLDER", "").rstrip()
                                        st.markdown(f"""
                                        <div class="response-container">
                                            {safe_text}
                                        </div>
                                        """, unsafe_allow_html=True)

                                        # If a ticket was generated, add a clear clickable link below
                                        if st.session_state.get("ticket_ready") and st.session_state.get("ticket_html_data_url"):
                                            ticket_url = st.session_state.get("ticket_html_data_url")
                                            st.markdown(
                                                f"""
                                                <div class="response-container" style="margin-top: 8px;">
                                                    <a href="{ticket_url}" target="_blank" rel="noopener" style="color: #0066cc; text-decoration: underline; font-weight: 600;">
                                                        Open/Download Ticket
                                                    </a>
                                                </div>
                                                """,
                                                unsafe_allow_html=True,
                                            )
                                        
                            
                            # Store in unified conversation structure
                            if conversation_id in st.session_state.conversations:
                                st.session_state.conversations[conversation_id]['user_query'] = user_input
                                st.session_state.conversations[conversation_id]['response'] = displayed_result
                            
                            # Link the most recent message to this data
                            # Find the last response message
                            for msg in reversed(st.session_state.user_friendly_response_agent_chat_history):
                                if isinstance(msg, ModelResponse) and hasattr(msg, 'id'):
                                    break
                            
                            # For backward compatibility
                            st.session_state.gathered_data_history.append({
                                "user_query": user_input,
                                "response": displayed_result,
                                "conversation_id": conversation_id
                            })
                            
                            return displayed_result
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        return None, None

                try:
                    # Show processing message with retry info if applicable
                    spinner_message = "Analyzing your request and preparing response..."
                        
                    with st.spinner(spinner_message):
                        # Add delay between retries (except for first attempt)
                        # Use a try-except to handle event loop issues gracefully
                        import concurrent.futures
                        try:
                            # First, try to run in a new event loop (most reliable for Streamlit)
                            displayed_result = asyncio.run(handle_complete_interaction())
                        except RuntimeError as e:
                            if "There is no current event loop" in str(e) or "cannot be called from a running event loop" in str(e):
                                # Handle event loop conflicts in Streamlit
                                try:
                                    # Create and set a new event loop
                                    new_loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(new_loop)
                                    displayed_result = asyncio.run(handle_complete_interaction())
                                except Exception as fallback_error:
                                    # Final fallback: use ThreadPoolExecutor
                                    with concurrent.futures.ThreadPoolExecutor() as executor:
                                        future = executor.submit(asyncio.run, handle_complete_interaction())
                                        displayed_result = future.result()
                            else:
                                raise e
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                        
                        
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()