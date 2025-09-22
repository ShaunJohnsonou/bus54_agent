"""Async utilities for handling event loops in the Absa Chatbot."""

import asyncio
import concurrent.futures
from typing import Callable, Any, Tuple


async def run_async_safely(async_func: Callable) -> Any:
    """
    Run an async function safely, handling event loop management.
    
    Args:
        async_func: The async function to run
        
    Returns:
        The result of the async function
    """
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, use ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, async_func())
                return future.result()
        else:
            # Loop is not running, safe to use asyncio.run
            return await async_func()
    except RuntimeError:
        # Event loop is closed or other runtime error, create new one
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            return await async_func()
        except Exception as e:
            raise Exception(f"Failed to run async function: {str(e)}")


def run_async_in_streamlit(async_func: Callable) -> Any:
    """
    Run an async function in a Streamlit context with proper event loop handling.
    
    Args:
        async_func: The async function to run
        
    Returns:
        The result of the async function
    """
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, use ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, async_func())
                return future.result()
        else:
            # Loop is not running, safe to use asyncio.run
            return asyncio.run(async_func())
    except RuntimeError:
        # Event loop is closed or other runtime error, create new one
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            return asyncio.run(async_func())
        except Exception as e:
            raise Exception(f"Failed to process request: {str(e)}")
