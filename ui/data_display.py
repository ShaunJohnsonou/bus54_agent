import streamlit as st
import pandas as pd
from typing import Any

def to_items_wide(df_items: pd.DataFrame) -> pd.DataFrame:
    """
    Transform breach-style data by exploding nested breach items and pivoting to wide format.
    
    Args:
        df_items: DataFrame with potentially nested breach data
        
    Returns:
        DataFrame with one row per server and metrics as columns
    """
    # For breach-style data: explode + pivot to wide columns per metric
    if "breaches" in df_items.columns:
        exploded = df_items.explode("breaches", ignore_index=True)
        # Normalize the breach dict
        breach_df = pd.json_normalize(exploded["breaches"]).add_prefix("breach.")
        merged = pd.concat([exploded.drop(columns=["breaches"]).reset_index(drop=True),
                            breach_df.reset_index(drop=True)], axis=1)
        # Pivot to one row per host with metric columns (use current_value; keep threshold separately if desired)
        wide = merged.pivot_table(
            index=[c for c in merged.columns if c not in ["breach.metric","breach.current_value","breach.threshold"]],
            columns="breach.metric",
            values="breach.current_value",
            aggfunc="first"
        ).reset_index()
        # make columns simple strings
        wide.columns = [c if isinstance(c, str) else c[1] for c in wide.columns]
        return wide
    return df_items

def render_payload(gathered_relevant_information: Any) -> None:
    """
    Render data payload in a structured format with summary metrics and detailed views.
    
    Args:
        gathered_relevant_information: Data in any format (DataFrame, dict, list, etc.)
    """
    # 1) Build a DataFrame from items using json_normalize instead of stringifying
    df = None

    if isinstance(gathered_relevant_information, pd.DataFrame):
        df = gathered_relevant_information

    elif isinstance(gathered_relevant_information, list):
        # assume list of dicts; flatten to columns
        import json  # Import here since we might use it below for string conversion
        df = pd.json_normalize(gathered_relevant_information, sep=".")
        df = to_items_wide(df)

    elif isinstance(gathered_relevant_information, dict):
        # If dict with 'items', flatten items; otherwise show the dict as JSON
        if "items" in gathered_relevant_information:
            items = gathered_relevant_information.get("items") or []
            
            import json
            import re
            
            # Special case: If items is a string representation of a list of JSON objects
            # from the screenshot, it appears the items field contains a string that looks like a list of server objects
            if isinstance(items, str):
                # Try direct parsing first
                try:
                    parsed_items = json.loads(items)
                    items = parsed_items
                except json.JSONDecodeError:
                    # The string might be a Python list representation rather than valid JSON
                    try:
                        # Replace single quotes with double quotes for proper JSON
                        items_str = items.replace("'", '"')
                        # Try to parse modified string
                        parsed_items = json.loads(items_str)
                        items = parsed_items
                    except json.JSONDecodeError:
                        # If that fails, try extracting individual JSON objects
                        try:
                            # Check if it looks like a list of server data with specific pattern
                            if "\\n {" in items or '\"server\"' in items or "'server'" in items:
                                # Extract server objects using regex
                                server_list = []
                                server_pattern = r'{\s*"server"\s*:\s*"([^"]+)".*?}'
                                matches = re.findall(server_pattern, items.replace("'", '"'))
                                
                                if matches:
                                    # We found server names, now let's extract all data for each server
                                    for server_name in matches:
                                        # Extract the full object for this server
                                        full_pattern = r'({[^{}]*?"server"\s*:\s*"' + re.escape(server_name) + r'"[^{}]*?})'
                                        server_match = re.search(full_pattern, items.replace("'", '"'))
                                        if server_match:
                                            try:
                                                server_data = json.loads(server_match.group(1))
                                                server_list.append(server_data)
                                            except Exception:
                                                # If parsing fails, create a simple object with server name
                                                server_list.append({"server": server_name})
                                    
                                    if server_list:
                                        items = server_list
                
                        except Exception as e:
                            st.error(f"Advanced parsing failed: {str(e)}")
                            # Leave items as is if all parsing methods fail
            
            # Create a DataFrame from the parsed items
            if isinstance(items, list) and items:
                if all(isinstance(item, dict) for item in items):
                    # We have a list of dictionaries, we can create a DataFrame
                    df = pd.DataFrame(items)
                else:
                    # We have a list of non-dictionary items
                    df = pd.DataFrame({"value": items})
            else:
                # For non-list items, display as JSON and return
                st.write("Raw data (could not parse into table format):")
                st.json(items)
                return
                
            # render summary fields nicely
            col1, col2, col3 = st.columns(3)
            col1.metric("Status", gathered_relevant_information.get("status", ""))
            col2.metric("Total", gathered_relevant_information.get("total", 0))
            crit = gathered_relevant_information.get("criteria", {})
            if crit:
                if "avg_gt" in crit or "p95_gt" in crit:
                    col3.write(f"avg>{crit.get('avg_gt','-')}, p95>{crit.get('p95_gt','-')}")
                elif "avg_lt" in crit or "p95_lt" in crit:
                    col3.write(f"avg<{crit.get('avg_lt','-')}, p95<{crit.get('p95_lt','-')}")
            if gathered_relevant_information.get("notes"):
                st.caption("\n".join(gathered_relevant_information["notes"]))
        # Special case for reallocation_candidates
        elif "_raw_data" in gathered_relevant_information and "donors" in gathered_relevant_information and "receivers" in gathered_relevant_information:
            # Create summary metrics
            col1, col2, col3 = st.columns(3)
            if "summary" in gathered_relevant_information:
                summary = gathered_relevant_information["summary"]
                col1.metric("Donor Count", summary.get("donor_count", 0))
                col2.metric("Receiver Count", summary.get("receiver_count", 0))
                donor_crit = summary.get("donor_criteria", {})
                receiver_crit = summary.get("receiver_criteria", {})
                if donor_crit and receiver_crit:
                    col3.write(f"Donors: avg<{donor_crit.get('avg_lt','-')}, Receivers: avg>{receiver_crit.get('avg_gt','-')}")
            
            # Create tabs for donors and receivers
            donor_tab, receiver_tab = st.tabs(["Donors", "Receivers"])
            
            with donor_tab:
                donors = gathered_relevant_information.get("donors", [])
                if donors:
                    donors_df = pd.DataFrame(donors)
                    st.dataframe(donors_df, use_container_width=True)
            
            with receiver_tab:
                receivers = gathered_relevant_information.get("receivers", [])
                if receivers:
                    receivers_df = pd.DataFrame(receivers)
                    st.dataframe(receivers_df, use_container_width=True)
            
            if gathered_relevant_information.get("notes"):
                st.caption("\n".join(gathered_relevant_information["notes"]))
            
            # No need to continue processing as we've handled this special case
            return
        else:
            # Direct JSON display for other dictionary types
            st.json(gathered_relevant_information)
            return

    else:
        # Fallback: show as JSON or text
        if isinstance(gathered_relevant_information, str):
            st.write(gathered_relevant_information)
        else:
            try:
                st.json(gathered_relevant_information)
            except Exception:
                st.write(str(gathered_relevant_information))
        return

    # 2) Actually render the table (scrollable)
    if df is not None and not df.empty:
        # Format numeric columns for better display
        for col in df.select_dtypes(include=['float']).columns:
            if df[col].max() <= 1.0 and df[col].min() >= 0:
                # Likely a percentage between 0-1
                df[col] = df[col].map(lambda x: f"{x:.1%}" if pd.notnull(x) else x)
            else:
                # Regular floating point number, show with 2 decimal places
                df[col] = df[col].map(lambda x: f"{x:.2f}" if pd.notnull(x) else x)
        
        # Compute a reasonable height based on row count, with a minimum and maximum
        row_count = len(df)
        row_height = 35  # Approximate height per row in pixels
        header_height = 38
        padding = 16
        min_height = 200
        max_height = 500
        computed_height = header_height + (row_count * row_height) + padding
        display_height = max(min_height, min(computed_height, max_height))
        
        st.dataframe(df, use_container_width=True, height=display_height)

        # 3) Optional: per-row drill-down for nested bits that stayed nested
        raw_items = None
        if isinstance(gathered_relevant_information, dict) and "items" in gathered_relevant_information:
            raw_items = gathered_relevant_information.get("items")
        elif isinstance(gathered_relevant_information, list):
            raw_items = gathered_relevant_information
            
        if raw_items and len(raw_items) > 0 and isinstance(raw_items[0], dict):
            with st.expander("Row Details", expanded=False):
                for i, item in enumerate(raw_items, start=1):
                    with st.expander(f"Row {i}: {item.get('server', item.get('hostname', ''))}"):
                        st.json(item)
