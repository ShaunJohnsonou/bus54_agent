from pydantic import BaseModel, Field
from typing import List, Dict, Any, Union, Literal


class FunctionCall(BaseModel):
    """Represents a single function call with parameters"""
    function_name: str = Field(description="Exact name of the function to call")
    parameters: Dict[str, Any] = Field(description="Parameters to pass to the function")


class SingleFunctionCallResponse(BaseModel):
    """Response for calling a single function"""
    response_type: Literal["function_call"]
    function_name: str = Field(description="Exact name of the function to call")
    parameters: Dict[str, Any] = Field(description="Parameters to pass to the function")


# class MultipleFunctionCallsResponse(BaseModel):
#     """Response for calling multiple functions"""
#     response_type: Literal["multiple_function_calls"]
#     functions: List[FunctionCall] = Field(description="List of functions to call")


class SqlQueryResponse(BaseModel):
    """Response for executing a SQL query"""
    response_type: Literal["sql_query"]
    sql_command: str = Field(description="The SQL command to execute")


# class MixedDataGatheringResponse(BaseModel):
#     """Response for mixed approach using both functions and SQL"""
#     response_type: Literal["mixed_data_gathering"]
#     functions: List[FunctionCall] = Field(description="List of functions to call")
#     sql_commands: List[str] = Field(description="List of SQL commands to execute")


class NoAdditionalInfoResponse(BaseModel):
    """Response when no additional data gathering is needed"""
    response_type: Literal["no_additional_info"]
    reason: str = Field(description="Brief explanation why no data gathering is needed")


# Union type for all possible data gathering responses
DataGatheringOutputType = Union[
    SingleFunctionCallResponse,
    # MultipleFunctionCallsResponse,
    SqlQueryResponse,
    # MixedDataGatheringResponse,
    NoAdditionalInfoResponse
]


class UserFriendlyResponse(BaseModel):
    """Response format for user-friendly outputs"""
    response: str = Field(description="Full formatted response with Markdown formatting")
    add_to_memory: bool = Field(description="Whether this response should be added to memory")


# For backwards compatibility (fixing the typo)
class DataGatheringOutputTypeOld(BaseModel):
    """Legacy model - use DataGatheringOutputType union instead"""
    response_type: str
    gathered_relevant_information: str  # Fixed typo: gathed -> gathered