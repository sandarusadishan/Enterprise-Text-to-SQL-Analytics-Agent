# OmniQuery | Autonomous BI Analytics Agent

OmniQuery is a full-stack, stateful Agentic AI assistant that translates natural language business questions into valid SQL queries, executes them against a relational database, recovers from runtime errors autonomously, and renders dynamic interactive charts and executive business summaries.

## 🏗️ Technical Architecture

OmniQuery uses a stateful Graph workflow pattern to manage session histories, query generations, and error corrections:

1. **User Request**: User inputs a question in the glassmorphic React interface.
2. **FastAPI Layer**: Receives the prompt, loads session context, and invokes the LangGraph state machine.
3. **SQL Generation Node**: Dynamically builds schema prompts (excluding metadata tables) and generates SQLite queries.
4. **Execution & Self-Healing Loop**: Executes the query. If a database error occurs, the error message is fed back to the LLM context to correct and retry.
5. **Insights Node**: Synthesizes the raw query result payload into a 2-bullet business summary.
6. **Visualization**: Returns data tables and coordinates to render responsive Recharts bar graphs.

---

## 🚀 Key Features

* **Self-Healing SQL Loop**: Catch and resolve SQL syntax and schema errors dynamically at runtime.
* **Multi-Session Chat History**: Create, rename, pin (📌), and delete (🗑️) session threads.
* **Interactive Charting**: Auto-fallback axis scaling for zero-value columns and value labels on top of charts.
* **Local DB Integration**: Pre-populated with real enterprise company sales data.
* **Offline Status Banner**: Automated frontend banner alerts if the FastAPI server is offline.
* **One-Click Batch Startup**: Launches all server processes in separate terminals with a single click.

---

## 🛠️ Quickstart & Local Setup

### Prerequisite
Ensure Python 3.9+ and Node.js are installed.

### Step 1: Clone and Run One-Click Startup
If on Windows, double-click the **`run_all.bat`** file in the root folder. This will automatically set up and launch:
1. The FastAPI Backend (`http://localhost:8000`)
2. The Streamlit Backup UI (`http://localhost:8501`)
3. The React Frontend Dev Server (`http://localhost:5173`)

---

### Step 2: Manual Backend Setup (If not using run_all.bat)
1. Navigate to the backend directory:
   ```bash
   cd backend
