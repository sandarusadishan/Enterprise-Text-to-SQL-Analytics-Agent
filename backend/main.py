import uuid
import json
import sys

# Force standard output to UTF-8 to prevent charmap UnicodeEncodeError on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database.schema import (
    create_session,
    get_all_sessions,
    delete_session,
    save_message,
    get_session_messages,
    rename_session
)
from agent.graph import agent_app

app = FastAPI(title="OmniQuery API", version="1.0.0")

# Enable CORS for the React development server on port 5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageInput(BaseModel):
    question: str

@app.get("/api/sessions")
def list_sessions():
    try:
        return get_all_sessions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions")
def start_session():
    try:
        session_id = str(uuid.uuid4())
        create_session(session_id, "New Chat")
        return {"session_id": session_id, "session_name": "New Chat"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/sessions/{session_id}")
def remove_session(session_id: str):
    try:
        delete_session(session_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}/messages")
def list_messages(session_id: str):
    try:
        return get_session_messages(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions/{session_id}/messages")
def send_message(session_id: str, data: MessageInput):
    try:
        question = data.question
        
        # Load existing messages to construct conversation history context
        existing_messages = get_session_messages(session_id)
        
        # Save user prompt
        save_message(session_id=session_id, role="user", content=question)
        
        # If this is the first message in the session, auto-rename the session
        if not existing_messages or len(existing_messages) == 0:
            rename_session(session_id, question[:36])
            
        # Format history string
        history_parts = []
        for msg in existing_messages:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            history_parts.append(f"{role_label}: {msg['content']}")
        history_str = "\n".join(history_parts)
        
        # Run LangGraph Workflow
        initial_state = {
            "question": question,
            "sql_query": None,
            "column_names": None,
            "query_result": None,
            "error_message": None,
            "retry_count": 0,
            "insights": None,
            "chart_json": None,
            "history": history_str
        }
        
        final_output = agent_app.invoke(initial_state)
        
        # Format assistant content
        error_msg = final_output.get("error_message")
        if error_msg:
            assistant_content = f"❌ Execution Error: {error_msg}"
            result_json_str = None
        else:
            assistant_content = final_output.get("insights", "Here are the query results:")
            
            # Serialize column names and query results to JSON
            columns = final_output.get("column_names") or []
            rows = final_output.get("query_result") or []
            result_json_str = json.dumps({"columns": columns, "rows": rows})
            
        # Save assistant response
        save_message(
            session_id=session_id,
            role="assistant",
            content=assistant_content,
            sql_query=final_output.get("sql_query"),
            query_result_json=result_json_str
        )
        
        return {
            "role": "assistant",
            "content": assistant_content,
            "sql_query": final_output.get("sql_query"),
            "query_result_json": result_json_str
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
