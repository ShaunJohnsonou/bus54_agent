import streamlit as st
from utils.sql_utils import execute_sql_on_parquet
import json
import pandas as pd
from typing import Tuple, Dict, Any, Union, List



def convert_da_to_ui_schema(function_name, payload):
    if function_name == "overstressed_servers":
        return payload["items"]
    elif function_name == "list_servers":
        return payload["items"]
    elif function_name == "underutilized_servers":
        return payload["items"]
    elif function_name == "overstressed_servers":
        return payload
    elif function_name == "memory_coverage":
        return payload["items"]
    elif function_name == "server_detail":
        return payload["item"]
    elif function_name == "reallocation_candidates":
        return payload
    elif function_name == "feature_coverage":
        return payload["items"]
    return payload





def extract_data_schema(data):
    """
    Extract a simplified schema structure from data without exposing actual values.
    
    Args:
        data: Input data in various formats (DataFrame, dict, list of dicts, JSON string)
        
    Returns:
        dict: A simplified dictionary describing the data structure format
    """
    import pandas as pd
    import json
    import ast
    import numpy as np
    
    # Convert input to DataFrame for consistent processing
    df = None
    
    try:
        if isinstance(data, pd.DataFrame):
            df = data
        elif isinstance(data, str):
            try:
                # Try to parse as JSON
                parsed_data = json.loads(data)
                if isinstance(parsed_data, list):
                    df = pd.DataFrame(parsed_data)
                elif isinstance(parsed_data, dict):
                    df = pd.DataFrame([parsed_data])
                else:
                    raise ValueError("JSON data must be a list or dictionary")
            except json.JSONDecodeError:
                try:
                    # Try to parse as Python literal
                    parsed_data = ast.literal_eval(data)
                    if isinstance(parsed_data, list):
                        df = pd.DataFrame(parsed_data)
                    elif isinstance(parsed_data, dict):
                        df = pd.DataFrame([parsed_data])
                    else:
                        raise ValueError("Data must be a list or dictionary")
                except (SyntaxError, ValueError):
                    # If not valid JSON or Python literal, try as CSV string
                    df = pd.read_csv(pd.StringIO(data))
        elif isinstance(data, list) and all(isinstance(item, dict) for item in data):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            raise ValueError("Unsupported data format")
            
        if df is None or df.empty:
            return {"error": "Empty data or unsupported format"}
        
        # Determine data structure type
        data_structure_type = "Unknown"
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            data_structure_type = "List of Dictionaries (List[dict])"
        elif isinstance(data, dict):
            data_structure_type = "Dictionary (dict)"
        elif isinstance(data, pd.DataFrame):
            data_structure_type = "DataFrame"
        elif isinstance(data, str):
            if isinstance(parsed_data, list) and all(isinstance(item, dict) for item in parsed_data):
                data_structure_type = "JSON List of Objects"
            elif isinstance(parsed_data, dict):
                data_structure_type = "JSON Object"
            
        # Create simplified schema
        simplified_schema = {
            "retrieved_data_structure": data_structure_type,
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "column_structure": {}
        }
        
        # Get column data types in a simplified format
        for col in df.columns:
            # Determine simplified data type
            if pd.api.types.is_numeric_dtype(df[col]):
                if df[col].dropna().apply(lambda x: float(x).is_integer()).all():
                    col_type = "integer"
                else:
                    col_type = "float"
            elif pd.api.types.is_string_dtype(df[col]):
                col_type = "string"
            elif pd.api.types.is_datetime64_dtype(df[col]):
                col_type = "datetime"
            elif pd.api.types.is_bool_dtype(df[col]):
                col_type = "boolean"
            else:
                col_type = str(df[col].dtype)
                
            simplified_schema["column_structure"][col] = col_type
            
        return simplified_schema
        
    except Exception as e:
        return {"error": f"Failed to extract schema: {str(e)}"}
        
        
def extract_detailed_data_schema(data):
    """
    Extract the detailed schema structure and data types from data without exposing actual values.
    
    Args:
        data: Input data in various formats (DataFrame, dict, list of dicts, JSON string)
        
    Returns:
        dict: A dictionary describing the schema structure with data types and sample formats
    """
    import pandas as pd
    import json
    import ast
    import numpy as np
    import datetime
    
    # Helper function to convert NumPy types to Python native types
    def convert_numpy_types(obj):
        if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, (np.datetime64, pd.Timestamp)):
            return str(obj)
        return obj
    
    # Convert input to DataFrame for consistent processing
    df = None
    
    try:
        if isinstance(data, pd.DataFrame):
            df = data
        elif isinstance(data, str):
            try:
                # Try to parse as JSON
                parsed_data = json.loads(data)
                if isinstance(parsed_data, list):
                    df = pd.DataFrame(parsed_data)
                elif isinstance(parsed_data, dict):
                    df = pd.DataFrame([parsed_data])
                else:
                    raise ValueError("JSON data must be a list or dictionary")
            except json.JSONDecodeError:
                try:
                    # Try to parse as Python literal
                    parsed_data = ast.literal_eval(data)
                    if isinstance(parsed_data, list):
                        df = pd.DataFrame(parsed_data)
                    elif isinstance(parsed_data, dict):
                        df = pd.DataFrame([parsed_data])
                    else:
                        raise ValueError("Data must be a list or dictionary")
                except (SyntaxError, ValueError):
                    # If not valid JSON or Python literal, try as CSV string
                    df = pd.read_csv(pd.StringIO(data))
        elif isinstance(data, list) and all(isinstance(item, dict) for item in data):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            raise ValueError("Unsupported data format")
            
        if df is None or df.empty:
            return {"error": "Empty data or unsupported format"}
            
        # Extract schema information
        schema = {
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "columns": {}
        }
        
        for col in df.columns:
            col_info = {
                "dtype": str(df[col].dtype),
                "non_null_count": int(df[col].count()),
                "null_count": int(df[col].isna().sum())
            }
            
            # Calculate null percentage
            col_info["null_percentage"] = float(round((col_info["null_count"] / len(df)) * 100, 2))
            
            # Determine more specific data type and format
            sample_values = df[col].dropna().head(3).tolist()
            sample_values = [convert_numpy_types(val) for val in sample_values]
            
            if df[col].dtype == 'object':
                # Check if string, dict, list, etc.
                if len(sample_values) > 0:
                    sample_type = type(sample_values[0]).__name__
                    col_info["inferred_type"] = sample_type
                    
                    # For strings, add additional info
                    if sample_type == 'str':
                        col_info["max_length"] = int(df[col].str.len().max()) if not pd.isna(df[col].str.len().max()) else 0
                        col_info["min_length"] = int(df[col].str.len().min()) if not pd.isna(df[col].str.len().min()) else 0
                        
                        # Check if it might be a date/time string
                        date_pattern = float(df[col].str.match(r'^\d{4}-\d{2}-\d{2}').mean() > 0.7)
                        time_pattern = float(df[col].str.match(r'\d{2}:\d{2}:\d{2}').mean() > 0.7)
                        
                        if date_pattern:
                            col_info["potential_format"] = "date (YYYY-MM-DD)"
                        elif time_pattern:
                            col_info["potential_format"] = "time (HH:MM:SS)"
                            
                    # For nested structures (dict, list)
                    elif sample_type in ('dict', 'list'):
                        # Extract nested structure without values
                        if sample_type == 'dict' and len(sample_values) > 0:
                            sample_dict = sample_values[0]
                            col_info["nested_structure"] = {k: type(v).__name__ for k, v in sample_dict.items()}
                        elif sample_type == 'list' and len(sample_values) > 0:
                            sample_list = sample_values[0]
                            if len(sample_list) > 0 and isinstance(sample_list[0], dict):
                                col_info["nested_structure"] = {k: type(v).__name__ for k, v in sample_list[0].items()}
                            else:
                                col_info["nested_structure"] = f"list of {type(sample_list[0]).__name__}" if sample_list else "empty list"
            
            elif pd.api.types.is_numeric_dtype(df[col]):
                # For numeric columns
                col_info["min"] = float(df[col].min())
                col_info["max"] = float(df[col].max())
                col_info["mean"] = float(df[col].mean())
                
                # Check if integer-like
                if df[col].dropna().apply(lambda x: float(x).is_integer()).all():
                    col_info["appears_integer"] = True
                
                # Check if it might be a categorical/code
                if len(df[col].unique()) < 20:  # Arbitrary threshold
                    col_info["unique_values_count"] = int(len(df[col].unique()))
                    col_info["potential_categorical"] = True
                    
            elif pd.api.types.is_datetime64_dtype(df[col]):
                # For datetime columns
                col_info["min_date"] = str(df[col].min())
                col_info["max_date"] = str(df[col].max())
                col_info["date_range_days"] = int((df[col].max() - df[col].min()).days)
            
            # Add unique value count for all columns
            col_info["unique_values"] = int(len(df[col].unique()))
            col_info["is_unique"] = bool(col_info["unique_values"] == len(df))
            
            schema["columns"][col] = col_info
            
        return schema
        
    except Exception as e:
        return {"error": f"Failed to extract schema: {str(e)}"}



import pandas as pd
import json

def convert_to_dataframe(obj):
    """
    Converts any nested Python object into a flattened, human-readable Pandas DataFrame.
    Handles nested dicts, lists of dicts, and mixed types gracefully.
    """
    def flatten(obj):
        """Recursively flattens nested dictionaries and lists."""
        if isinstance(obj, dict):
            return {k: flatten(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            # Convert list of dicts to readable string
            if all(isinstance(item, dict) for item in obj):
                return [json.dumps(item, indent=2) for item in obj]
            else:
                return obj
        else:
            return obj

    # Try to parse JSON string if applicable
    if isinstance(obj, str):
        try:
            obj = json.loads(obj)
        except json.JSONDecodeError:
            raise ValueError("String input is not valid JSON.")

    # Flatten the object
    flat_obj = flatten(obj)

    # Normalize using pandas
    try:
        if isinstance(flat_obj, list):
            df = pd.json_normalize(flat_obj)
        elif isinstance(flat_obj, dict):
            if all(isinstance(v, dict) for v in flat_obj.values()):
                df = pd.json_normalize(list(flat_obj.values()))
            else:
                df = pd.json_normalize(flat_obj)
        else:
            df = pd.DataFrame([flat_obj])
    except Exception as e:
        raise ValueError(f"Failed to convert object to DataFrame: {e}")

    # Convert any remaining complex objects to strings
    for col in df.columns:
        df[col] = df[col].apply(lambda x: json.dumps(x, indent=2) if isinstance(x, (dict, list)) else x)

    return df





# def convert_to_dataframe(data: Any) -> pd.DataFrame:
#     """
#     Convert any type of data to a pandas DataFrame.
    
#     Args:
#         data: Data in any format (dict, list, DataFrame, etc.)
        
#     Returns:
#         pd.DataFrame: The data converted to a DataFrame
#     """
#     if isinstance(data, pd.DataFrame):
#         return data
    
#     # Handle lists of dictionaries
#     if isinstance(data, list) and all(isinstance(item, dict) for item in data):
#         return pd.DataFrame(data)
    
#     # Handle single dictionary
#     if isinstance(data, dict):
#         # Check if it's a nested structure with special keys like in reallocation_candidates
#         if "_raw_data" in data:
#             # Extract the relevant data from the nested structure
#             processed_data = []
#             if "donors" in data and isinstance(data["donors"], list):
#                 for donor in data["donors"]:
#                     donor["type"] = "donor"
#                     processed_data.append(donor)
#             if "receivers" in data and isinstance(data["receivers"], list):
#                 for receiver in data["receivers"]:
#                     receiver["type"] = "receiver"
#                     processed_data.append(receiver)
#             if processed_data:
#                 return pd.DataFrame(processed_data)
            
#             # If we have nested data from reallocation_candidates in the _raw_data field
#             if "donors" in data["_raw_data"] and "items" in data["_raw_data"]["donors"]:
#                 donors_df = pd.DataFrame(data["_raw_data"]["donors"]["items"])
#                 if not donors_df.empty:
#                     donors_df["type"] = "donor"
#             else:
#                 donors_df = pd.DataFrame()
                
#             if "receivers" in data["_raw_data"] and "items" in data["_raw_data"]["receivers"]:
#                 receivers_df = pd.DataFrame(data["_raw_data"]["receivers"]["items"])
#                 if not receivers_df.empty:
#                     receivers_df["type"] = "receiver"
#             else:
#                 receivers_df = pd.DataFrame()
                
#             if not donors_df.empty and not receivers_df.empty:
#                 return pd.concat([donors_df, receivers_df], ignore_index=True)
#             elif not donors_df.empty:
#                 return donors_df
#             elif not receivers_df.empty:
#                 return receivers_df
        
#         # Handle server breach data with nested metrics
#         if "hostname" in data and "breaches" in data and isinstance(data["breaches"], list):
#             flattened_data = {"hostname": data["hostname"]}
#             for breach in data["breaches"]:
#                 if "metric" in breach and "current_value" in breach:
#                     flattened_data[breach["metric"]] = breach["current_value"]
#             return pd.DataFrame([flattened_data])
        
#         # Handle normal dictionaries by converting to a single-row DataFrame
#         return pd.DataFrame([data])
    
#     # Handle string data - try to convert from JSON
#     if isinstance(data, str):
#         try:
#             json_data = json.loads(data)
#             return convert_to_dataframe(json_data)  # Recursively handle the parsed JSON
#         except json.JSONDecodeError:
#             # If it's not JSON, create a simple one-column DataFrame
#             return pd.DataFrame({"value": [data]})
    
#     # Handle other types by creating a simple DataFrame
#     if isinstance(data, (int, float, bool)):
#         return pd.DataFrame({"value": [data]})
    
#     # Handle completely unknown types
#     return pd.DataFrame({"data": ["Unable to convert to DataFrame format"]})


def gather_relevant_information(agent_response: Dict[str, Any], user_input: str, 
                               functions: Any) -> Tuple[str, Union[pd.DataFrame, Dict[str, Any]], Dict[str, Any], Dict[str, Any]]:
    """
    Gather relevant information based on the agent's response.
    Always returns a pandas DataFrame for the gathered information.
    
    Args:
        agent_response: The response from the agent
        user_input: The user's input query
        functions: Module containing functions that can be called
        
    Returns:
        Tuple containing:
        - response_type: Type of response
        - gathered_information: Data gathered, converted to DataFrame when possible
        - alias_gathered_information: Schema description of the data
        - agent_logs: Logs from the agent's processing
    """
    function_list = []
    response_type = agent_response["response_type"]
    print("response_type: ", response_type)
    agent_logs = {}
    if response_type == "function_call":
        with st.spinner("Calling function..."):
            function_name = agent_response["function_name"]
            function_list.append(function_name)
            func = getattr(functions, function_name, None)
            parameters = agent_response["parameters"]
            agent_logs["function_name"] = function_name
            agent_logs["parameters"] = parameters
            
            if not callable(func):
                raise AttributeError(f"Function '{function_name}' not found or not callable")

            gathered_information = func(**parameters)
            print("function_name: ", function_name)
            print("gathered_information: ", gathered_information)
            gathered_information = convert_da_to_ui_schema(function_name, gathered_information)

    elif response_type == "multiple_function_calls":
        with st.spinner("Calling multiple functions..."):
            function_results = {}
            agent_logs["functions_called"] = []
            
            for func_call in agent_response["functions"]:
                function_name = func_call["function_name"]
                function_list.append(function_name)

                parameters = func_call["parameters"]
                func = getattr(functions, function_name, None)
                
                if not callable(func):
                    raise AttributeError(f"Function '{function_name}' not found or not callable")
                
                result = func(**parameters)
                print("result: ", result)
                function_results[function_name] = result
                agent_logs["functions_called"].append({
                    "function_name": function_name,
                    "parameters": parameters
                })
            
            gathered_information = function_results

    elif response_type == "sql_query":
        with st.spinner("Executing SQL query..."):
            SQL_Command = agent_response["sql_command"]
            agent_logs["SQL_Command"] = SQL_Command
            # gathered_information = execute_sql_on_parquet(SQL_Command, "data/server_growth_trends.parquet")
            gathered_information = execute_sql_on_parquet(SQL_Command, "data/00_all_normalized.parquet")

    elif response_type == "mixed_data_gathering":
        with st.spinner("Gathering data from multiple sources..."):
            mixed_results = {"function_results": {}, "sql_results": []}
            agent_logs["mixed_operations"] = {"functions": [], "sql_commands": []}
            
            # Execute functions if present
            if "functions" in agent_response:
                for func_call in agent_response["functions"]:
                    function_name = func_call["function_name"]
                    function_list.append(function_name)

                    parameters = func_call["parameters"]
                    func = getattr(functions, function_name, None)
                    
                    if not callable(func):
                        raise AttributeError(f"Function '{function_name}' not found or not callable")
                    
                    result = func(**parameters)
                    print("result: ", result)
                    mixed_results["function_results"][function_name] = result
                    agent_logs["mixed_operations"]["functions"].append({
                        "function_name": function_name,
                        "parameters": parameters
                    })
            
            # Execute SQL commands if present
            if "sql_commands" in agent_response:
                for sql_command in agent_response["sql_commands"]:
                    result = execute_sql_on_parquet(sql_command, "data/server_growth_trends.parquet")
                    mixed_results["sql_results"].append(result)
                    agent_logs["mixed_operations"]["sql_commands"].append(sql_command)
            
            gathered_information = mixed_results

    elif response_type == "SQL":  # Keep backward compatibility
        with st.spinner("Executing SQL query..."):
            gathered_information = agent_response
            SQL_Command = gathered_information["sql_command"]
            agent_logs["SQL_Command"] = SQL_Command
            gathered_information = execute_sql_on_parquet(SQL_Command, "data/server_growth_trends.parquet")

    elif response_type == "no_additional_info":
        with st.spinner("Preparing response..."):
            # No data gathering needed, just pass the reason to the response generator
            gathered_information = {
                "message": "No additional data gathering required",
                "reason": agent_response.get("reason", "General inquiry or greeting"),
                "user_query": user_input
            }
            agent_logs["no_data_reason"] = agent_response.get("reason", "Not specified")

    elif response_type == "natural_response":
        with st.spinner("Generating natural language response..."):
            # Extract the response directly from the agent's response
            gathered_information = agent_response.get("response", "No response content available.")
            # For natural responses, we'll return the original text and a special DataFrame
            # to indicate that this is a natural language response
            natural_df = pd.DataFrame({"response": [gathered_information]})
            gathered_information = natural_df

    # Convert gathered information to DataFrame for all response types except no_additional_info
    # which needs special handling to avoid confusing the user interface
    # if response_type != "natural_response" and response_type != "no_additional_info":
        # Convert to DataFrame
        # gathered_information = convert_to_dataframe(gathered_information)
    
    print(f"!!!gathered_information: {gathered_information}")
    # Extract schema after DataFrame conversion
    alias_gathered_information = extract_data_schema(gathered_information)

    # gathered_information = convert_to_dataframe(gathered_information)

    return response_type, gathered_information, alias_gathered_information, agent_logs, function_list