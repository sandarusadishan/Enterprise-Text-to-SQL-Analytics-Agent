from .connection import get_db_connection

def create_query_history_table():
    """Creates the query_history table automatically in company_sales.db if it doesn't exist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            question TEXT NOT NULL,
            sql_query TEXT,
            insights TEXT,
            rows_fetched INTEGER,
            status TEXT
        )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error creating query_history table: {e}")

def create_session_tables():
    """Creates the sessions and messages tables for chat history management"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            session_name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            sql_query TEXT,
            query_result_json TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error creating session/message tables: {e}")

# Automatically create the required tables upon importing schema.py
create_query_history_table()
create_session_tables()

def get_db_schema() -> str:
    """Extracts schema of all tables from SQLite DB, excluding metadata/history/chat tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' 
            AND name NOT IN ('query_history', 'sessions', 'messages', 'sqlite_sequence');
        """)
        tables = cursor.fetchall()
        conn.close()
        schema = "\n".join([t[0] for t in tables if t[0] is not None])
        return schema
    except Exception as e:
        return f"Error extracting schema: {e}"

def save_query_history(question: str, sql_query: str or None, insights: str or None, rows_fetched: int or None, status: str):
    """Saves a query execution log into the query_history table (legacy)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO query_history (question, sql_query, insights, rows_fetched, status)
        VALUES (?, ?, ?, ?, ?)
        ''', (question, sql_query, insights, rows_fetched, status))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving query history: {e}")
def get_all_history() -> list:
    """Fetches all query logs sorted by timestamp descending (legacy)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, timestamp, question, sql_query, insights, rows_fetched, status FROM query_history ORDER BY timestamp DESC;")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"Error fetching query history: {e}")
        return []

def delete_query_history(record_id: int):
    """Deletes a query log from query_history table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM query_history WHERE id = ?;", (record_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error deleting query history: {e}")
# New Multi-Session Chat Helpers
def create_session(session_id: str, session_name: str):
    """Creates a new chat session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO sessions (session_id, session_name)
        VALUES (?, ?)
        ''', (session_id, session_name))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error creating session: {e}")

def get_all_sessions() -> list:
    """Fetches all sessions sorted by created_at DESC"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, session_name, created_at FROM sessions ORDER BY created_at DESC;")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"Error fetching sessions: {e}")
        return []

def rename_session(session_id: str, new_name: str):
    """Renames an existing session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE sessions SET session_name = ? WHERE session_id = ?
        ''', (new_name, session_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error renaming session: {e}")

def delete_session(session_id: str):
    """Deletes a session and all its messages"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("DELETE FROM sessions WHERE session_id = ?;", (session_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error deleting session: {e}")

def save_message(session_id: str, role: str, content: str, sql_query: str or None = None, query_result_json: str or None = None):
    """Saves a chat message linked to a session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO messages (session_id, role, content, sql_query, query_result_json)
        VALUES (?, ?, ?, ?, ?)
        ''', (session_id, role, content, sql_query, query_result_json))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving message: {e}")

def get_session_messages(session_id: str) -> list:
    """Fetches all messages for a specific session sorted by timestamp ASC"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        SELECT id, session_id, role, content, sql_query, query_result_json, timestamp 
        FROM messages 
        WHERE session_id = ? 
        ORDER BY timestamp ASC;
        ''', (session_id,))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"Error fetching session messages: {e}")
        return []
