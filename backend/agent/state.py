from typing import TypedDict, Optional, Any

class AgentState(TypedDict):
    question: str
    sql_query: Optional[str]
    column_names: Optional[list]
    query_result: Optional[list]
    error_message: Optional[str]
    retry_count: int
    insights: Optional[str]
    chart_json: Optional[Any]
