import re
import sys
import pandas as pd
import plotly.express as px

# Force standard output to UTF-8 to prevent charmap UnicodeEncodeError on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from database.connection import get_db_connection
from database.schema import get_db_schema
from .state import AgentState
from .prompts import SQL_GENERATION_PROMPT, SQL_FIX_PROMPT, ANALYTICS_PROMPT

# Load environment variables
load_dotenv()

# Initialize the Groq model for Agent actions
llm = ChatGroq(
    model="groq/compound",
    temperature=0
)

def get_content_text(content) -> str:
    """Helper to extract text from Langchain AI Message content (handles list of dicts)"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                if part.get("type") == "text":
                    parts.append(part.get("text", ""))
            else:
                parts.append(str(part))
        return "".join(parts)
    return str(content)

# 1. SQL Generation Node
def generate_sql_node(state: AgentState) -> AgentState:
    print(f"\n🧠 [Node 1: Generate SQL] Question: '{state['question']}'")
    schema = get_db_schema()
    
    # Prepend history context if present
    history_str = state.get("history", "")
    question_with_context = state['question']
    if history_str:
        question_with_context = f"Conversation History:\n{history_str}\n\nUser's Current Question: {state['question']}"
        
    prompt = SQL_GENERATION_PROMPT.format(schema=schema, question=question_with_context)
    response = llm.invoke(prompt)
    raw_sql = get_content_text(response.content).strip()
    
    # Strip markdown block decorations if generated
    cleaned_sql = re.sub(r'```sql|```', '', raw_sql).strip()
    
    print(f"📄 Generated SQL: {cleaned_sql}")
    return {
        "sql_query": cleaned_sql,
        "error_message": None
    }

# 2. Database Execution Node
def execute_sql_node(state: AgentState) -> AgentState:
    print(f"⚡ [Node 2: Execute SQL] Running Query...")
    sql = state.get("sql_query")
    
    # Security Guardrail Check (Strictly Read-Only on MS SQL)
    forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE"]
    if any(keyword in sql.upper() for keyword in forbidden_keywords):
        return {
            "error_message": "SECURITY ERROR: Only READ-ONLY (SELECT) queries are allowed!",
            "query_result": None,
            "column_names": None
        }

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        
        # Get columns list from cursor description
        columns = [description[0] for description in cursor.description] if cursor.description else []
        
        # Parse pyodbc Row objects to clean tuples
        results_tuples = [tuple(row) for row in results]
        conn.close()
        
        print(f"✅ Executed Successfully! Rows fetched: {len(results_tuples)}")
        return {
            "query_result": results_tuples,
            "column_names": columns,
            "error_message": None
        }
    except Exception as e:
        print(f"❌ SQL Execution Failed: {e}")
        return {
            "error_message": str(e),
            "retry_count": state.get("retry_count", 0) + 1
        }

# 3. Self-Correction Node
def fix_sql_node(state: AgentState) -> AgentState:
    print(f"🔄 [Node 3: Self-Correction] Fixing SQL Error: {state['error_message']}")
    schema = get_db_schema()
    
    history_str = state.get("history", "")
    question_with_context = state['question']
    if history_str:
        question_with_context = f"Conversation History:\n{history_str}\n\nUser's Current Question: {state['question']}"
        
    prompt = SQL_FIX_PROMPT.format(
        schema=schema,
        sql_query=state['sql_query'],
        error_message=state['error_message'],
        question=question_with_context
    )
    response = llm.invoke(prompt)
    fixed_sql = re.sub(r'```sql|```', '', get_content_text(response.content).strip()).strip()
    print(f"🔧 Corrected SQL: {fixed_sql}")
    
    return {
        "sql_query": fixed_sql,
        "error_message": None
    }

# 4. Analytics & Visualization Node
def generate_analytics_node(state: AgentState) -> AgentState:
    print(f"📊 [Node 4: Analytics & Insights] Generating Insights & Chart...")
    results = state.get("query_result")
    columns = state.get("column_names")
    
    if not results or not columns:
        return {"insights": "No data found to generate analytics.", "chart_json": None}

    # Build DataFrame from db rows
    df = pd.DataFrame(results, columns=columns)
    
    # Prompt Gemini for text summary insights
    prompt = ANALYTICS_PROMPT.format(question=state['question'], data_df=df.to_string(index=False))
    insights_response = get_content_text(llm.invoke(prompt).content).strip()
    
    # Generate Interactive Plotly Fig Config if valid columns are present
    fig = None
    if len(df.columns) >= 2 and len(df) > 0:
        x_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        y_col = df.columns[-1]
        
        if pd.api.types.is_numeric_dtype(df[y_col]):
            fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}", template="plotly_white")
    
    print("✨ Analytics & Visualizations Ready!")
    return {
        "insights": insights_response,
        "chart_json": fig
    }
