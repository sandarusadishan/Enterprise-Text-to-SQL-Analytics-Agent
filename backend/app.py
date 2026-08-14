import streamlit as st
import pandas as pd
import io
import csv
import plotly.express as px
from dotenv import load_dotenv

# Environment Variables auto-load
load_dotenv()

from agent.graph import agent_app
from database.schema import save_query_history, get_all_history
from database.connection import get_db_connection

# 1. Page Configuration
st.set_page_config(
    page_title="Enterprise Text-to-SQL Analytics Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Next-Level Custom CSS Styling
st.markdown("""
<style>
    /* Dark Theme Background Refinement */
    .stApp {
        background-color: #0E1117;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Card Container Styling */
    .custom-card {
        background: #1E222D;
        border: 1px solid #2E3440;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    /* Executive Metric Display */
    .metric-box {
        background: linear-gradient(135deg, #1F2937 0%, #111827 100%);
        border: 1px solid #374151;
        border-radius: 10px;
        padding: 14px;
        text-align: center;
    }
    .metric-value {
        font-size: 22px;
        font-weight: 700;
        color: #38BDF8;
    }
    .metric-label {
        font-size: 11px;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Status Pills in Sidebar */
    .status-badge {
        background-color: #1E293B;
        color: #38BDF8;
        border: 1px solid #0284C7;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
        display: inline-block;
        margin-bottom: 8px;
    }

    /* Subheader Refinement */
    .section-header {
        font-size: 18px;
        font-weight: 600;
        color: #F3F4F6;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Sidebar Architecture Panel
st.sidebar.markdown("### 🛠️ Agent Architecture")
st.sidebar.markdown("""
<div class="status-badge">🟢 Llama 3.3 70B (Groq)</div>
<div class="status-badge">🛡️ LangGraph Stateful Agent</div>
<div class="status-badge">🗄️ SQLite Database</div>
""", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.info("""
**Key Features:**
- Autonomous SQL Generation
- Self-Correction Guardrails
- Data Insights & Plotly Visualizations
""")

# 3.1. Interactive Sidebar Query History
st.sidebar.divider()
st.sidebar.markdown("### 📜 Past Analytics Logs")

history_list = get_all_history()

if "selected_history_option" not in st.session_state:
    st.session_state.selected_history_option = "-- Select to load --"

if history_list:
    options = ["-- Select to load --"] + [f"{h['timestamp']} | {h['question']}" for h in history_list]
    
    if st.session_state.selected_history_option not in options:
        st.session_state.selected_history_option = "-- Select to load --"
        
    selected_option = st.sidebar.selectbox(
        "Load Query History",
        options=options,
        index=options.index(st.session_state.selected_history_option),
        key="history_selectbox",
        label_visibility="collapsed"
    )
    
    if selected_option != st.session_state.selected_history_option:
        st.session_state.selected_history_option = selected_option
        if selected_option != "-- Select to load --":
            selected_index = options.index(selected_option) - 1
            record = history_list[selected_index]
            
            # Load the record and re-execute SQL to populate chart and results table
            if record["status"] == "SUCCESS" and record["sql_query"]:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute(record["sql_query"])
                    results = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    results_tuples = [tuple(row) for row in results]
                    conn.close()
                    
                    df = pd.DataFrame(results_tuples, columns=columns)
                    fig = None
                    if len(df.columns) >= 2 and len(df) > 0:
                        x_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
                        y_col = df.columns[-1]
                        if pd.api.types.is_numeric_dtype(df[y_col]):
                            fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}", template="plotly_white")
                    
                    st.session_state.last_result = {
                        "question": record["question"],
                        "sql_query": record["sql_query"],
                        "column_names": columns,
                        "query_result": results_tuples,
                        "error_message": None,
                        "insights": record["insights"],
                        "chart_json": fig
                    }
                except Exception as e:
                    st.session_state.last_result = {
                        "question": record["question"],
                        "sql_query": record["sql_query"],
                        "error_message": f"Error reloading historical query: {e}",
                        "insights": None,
                        "chart_json": None
                    }
            else:
                st.session_state.last_result = {
                    "question": record["question"],
                    "sql_query": record["sql_query"],
                    "error_message": f"Query execution failed: {record['insights']}",
                    "insights": None,
                    "chart_json": None
                }
else:
    st.sidebar.info("No past queries recorded.")

# 4. Header Section
st.markdown("""
<div style="padding-bottom: 10px;">
    <h1 style="font-size: 32px; font-weight: 800; color: #FFFFFF; margin-bottom: 0px;">
        📊 Enterprise Text-to-SQL & Analytics Agent
    </h1>
    <p style="color: #9CA3AF; font-size: 15px; margin-top: 5px;">
        Ask any question in natural language, and AI will autonomously query the database, generate insights, and plot charts.
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# 5. Input Box for User Question
st.markdown('<div class="section-header">💬 Ask a question about your business data:</div>', unsafe_allow_html=True)

col_input, col_btn = st.columns([4, 1])

with col_input:
    user_question = st.text_input(
        "Query",
        placeholder="e.g., What is the total sales amount for each customer?",
        label_visibility="collapsed"
    )

with col_btn:
    run_btn = st.button("🚀 Run Analytics Agent", type="primary", use_container_width=True)

# Initialize session state for query output persistence
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# 6. Logic & Output Display
if run_btn:
    if not user_question.strip():
        st.warning("Please enter a valid question!")
    else:
        # Reset the selectbox state to prevent history selection from lingering
        st.session_state.selected_history_option = "-- Select to load --"
        
        with st.spinner("🤖 Agent is thinking, writing SQL, and analyzing data..."):
            # Initializing Graph State
            initial_state = {
                "question": user_question,
                "sql_query": None,
                "column_names": None,
                "query_result": None,
                "error_message": None,
                "retry_count": 0,
                "insights": None,
                "chart_json": None
            }
            
            # Execute LangGraph Workflow
            final_output = agent_app.invoke(initial_state)
            st.session_state.last_result = final_output

            # Log execution details into query_history
            error_msg = final_output.get("error_message")
            if error_msg:
                status = "FAILED"
                rows_fetched = 0
                insights = error_msg
            else:
                status = "SUCCESS"
                results = final_output.get("query_result", [])
                rows_fetched = len(results) if results else 0
                insights = final_output.get("insights", "No insights generated.")
            
            save_query_history(
                question=user_question,
                sql_query=final_output.get("sql_query"),
                insights=insights,
                rows_fetched=rows_fetched,
                status=status
            )
            
            # Programmatically rerun the app to immediately update the history list
            st.rerun()

# Render results from session state if available
if st.session_state.last_result is not None:
    final_output = st.session_state.last_result
    
    # UI Display Section
    if final_output.get("error_message"):
        st.error(f"❌ Execution Error: {final_output['error_message']}")
    else:
        st.divider()
        
        # Metric Summary Cards
        results = final_output.get("query_result", [])
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f'<div class="metric-box"><div class="metric-value">{len(results)}</div><div class="metric-label">Rows Fetched</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown('<div class="metric-box"><div class="metric-value">Groq 70B</div><div class="metric-label">LPU Engine</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown('<div class="metric-box"><div class="metric-value">SUCCESS</div><div class="metric-label">Agent Status</div></div>', unsafe_allow_html=True)
        with m4:
            st.markdown('<div class="metric-box"><div class="metric-value">ACTIVE</div><div class="metric-label">Guardrails</div></div>', unsafe_allow_html=True)

        st.write("") # Spacer

        # Main Layout Columns
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown('<div class="section-header">💡 Business Insights Summary</div>', unsafe_allow_html=True)
            insights_text = final_output.get("insights", "No insights generated.")
            st.markdown(f'<div class="custom-card">{insights_text}</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="section-header">💻 Executed SQL Query</div>', unsafe_allow_html=True)
            st.code(final_output.get("sql_query"), language="sql")

        with col2:
            st.markdown('<div class="section-header">📊 Interactive Data Visualization</div>', unsafe_allow_html=True)
            chart = final_output.get("chart_json")
            if chart:
                # Apply Dark Theme formatting to Plotly chart
                chart.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#E5E7EB"),
                    margin=dict(l=20, r=20, t=30, b=20)
                )
                st.plotly_chart(chart, use_container_width=True)
            else:
                st.info("No visual chart available for this query.")
        
        # Raw Data Table Section with Export Capability
        st.divider()
        col_header, col_export = st.columns([3, 1])
        with col_header:
            st.markdown('<div class="section-header">📋 Raw Query Results Table</div>', unsafe_allow_html=True)
            
        columns = final_output.get("column_names")
        if results and columns:
            df = pd.DataFrame(results, columns=columns)
            
            # Format analysis report CSV content
            csv_buffer = io.StringIO()
            csv_writer = csv.writer(csv_buffer)
            csv_writer.writerow(["Enterprise Text-to-SQL Analytics Report"])
            csv_writer.writerow([])
            csv_writer.writerow(["Question", final_output.get("question", "")])
            csv_writer.writerow(["Executed SQL Query", final_output.get("sql_query", "")])
            csv_writer.writerow(["Status", "SUCCESS"])
            csv_writer.writerow([])
            csv_writer.writerow(["Business Insights"])
            insights_lines = final_output.get("insights", "").split("\n")
            for line in insights_lines:
                csv_writer.writerow([line])
            csv_writer.writerow([])
            csv_writer.writerow(["Raw Data Table"])
            csv_writer.writerow(columns)
            for row in results:
                csv_writer.writerow(row)
                
            csv_data = csv_buffer.getvalue()
            
            with col_export:
                st.download_button(
                    label="📥 Export Analysis Report",
                    data=csv_data,
                    file_name="analytics_report.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
            st.dataframe(df, use_container_width=True)