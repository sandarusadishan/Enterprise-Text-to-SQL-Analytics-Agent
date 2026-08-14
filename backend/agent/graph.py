from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    generate_sql_node, 
    execute_sql_node, 
    fix_sql_node, 
    generate_analytics_node
)

# Define routing conditional logic
def decide_next_step(state: AgentState) -> str:
    """Evaluates if execution is successful or if repair is required (max retries = 3)"""
    if state.get("error_message"):
        if state.get("retry_count", 0) >= 3:
            print("⛔ Max retries reached. Stopping execution.")
            return END
        return "fix_sql"
    return "generate_analytics"

# Instantiate workflow graph
workflow = StateGraph(AgentState)

# Register workflow steps (nodes)
workflow.add_node("generate_sql", generate_sql_node)
workflow.add_node("execute_sql", execute_sql_node)
workflow.add_node("fix_sql", fix_sql_node)
workflow.add_node("generate_analytics", generate_analytics_node)

# Set starting entry node
workflow.set_entry_point("generate_sql")

# Add transition transitions (edges)
workflow.add_edge("generate_sql", "execute_sql")

workflow.add_conditional_edges("execute_sql", decide_next_step, {
    "fix_sql": "fix_sql",
    "generate_analytics": "generate_analytics"
})

workflow.add_edge("fix_sql", "execute_sql")
workflow.add_edge("generate_analytics", END)

# Compile graph app
agent_app = workflow.compile()
