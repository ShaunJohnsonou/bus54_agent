import pandas as pd
import duckdb

def execute_sql_on_parquet(sql_query, parquet_file_path, parameters=None):
    """
    Execute SQL queries directly on Parquet files.
    
    Args:
        sql_query (str): The SQL query to execute
        parquet_file_path (str): Path to the Parquet file
        parameters (dict, optional): Parameters to be used in the SQL query
        
    Returns:
        pd.DataFrame: Results of the SQL query as a pandas DataFrame
    """
    # Connect to an in-memory DuckDB database
    con = duckdb.connect(database=':memory:')
    
    # Register the Parquet file as a view with the name server_growth_trends
    con.execute(f"CREATE VIEW server_growth_trends AS SELECT * FROM '{parquet_file_path}'")
    
    # Execute the SQL query with parameters if provided
    if parameters:
        result = con.execute(sql_query, parameters)
    else:
        result = con.execute(sql_query)
    
    # Convert to pandas DataFrame
    df_result = result.fetchdf()
    
    return df_result
# query = "SELECT hostname, current_cpu_usage FROM parquet_data WHERE current_cpu_usage > ?"
# params = [80]
# results = execute_sql_on_parquet(query, "data/server_growth_trends.parquet", params)
