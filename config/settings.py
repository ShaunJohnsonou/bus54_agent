"""Configuration settings for the Bus 54 Ticketing Assistant."""

import os
from dotenv import load_dotenv
import logfire
from utils.models import gpt_4o_openai_model

# Load environment variables
load_dotenv()

# Configure logging
logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))
logfire.instrument_pydantic_ai()

# Model configurations
GATHER_DATA_MODEL = gpt_4o_openai_model
USER_FRIENDLY_RESPONSE_MODEL = gpt_4o_openai_model

# Streamlit page configuration
STREAMLIT_CONFIG = {
    "page_title": "Bus 54 Ticketing Assistant",
    "layout": "wide",
    "initial_sidebar_state": "collapsed"
}

# Agent settings
AGENT_SETTINGS = {
    "retries": 5,
    "gather_data_temperature": 0.1,
    "user_friendly_temperature": 0.5
}

# UI Constants
LOGO_WIDTH = 600
DATAFRAME_HEIGHT = 400
MAX_MESSAGE_WIDTH = "80%"

# Bus 54 specific settings
BUS_COMPANY_NAME = "Bus 54"
BUS_COMPANY_TAGLINE = "Your Journey, Our Priority"
BUS_DATA_FILES = {
    "static_data": "data/static_bus_data.json",
    "schedules": "data/bus_schedules.csv",
    "schedules_parquet": "data/bus_schedules.parquet"
}

# Bus 54 branding colors
BRAND_COLORS = {
    "primary": "#0066cc",  # Blue
    "secondary": "#004d99",  # Darker Blue
    "accent": "#e6f2ff",    # Light Blue
    "text": "#333333",      # Dark Gray
    "background": "#f5f8fa"  # Light Gray
}