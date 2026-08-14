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

# Automatically create the table upon importing schema.py
create_query_history_table()

def get_db_schema() -> str:
    """Extracts schema of all tables from SQLite DB, excluding metadata/history tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT IN ('query_history', 'sqlite_sequence');")
        tables = cursor.fetchall()
        conn.close()
        schema = "\n".join([t[0] for t in tables if t[0] is not None])
        return schema
    except Exception as e:
        return f"Error extracting schema: {e}"

def save_query_history(question: str, sql_query: str or None, insights: str or None, rows_fetched: int or None, status: str):
    """Saves a query execution log into the query_history table"""
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
    """Fetches all query logs sorted by timestamp descending"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, timestamp, question, sql_query, insights, rows_fetched, status FROM query_history ORDER BY timestamp DESC;")
        rows = cursor.fetchall()
        
        # Extract column names from description
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        # Format as list of dictionaries
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"Error fetching query history: {e}")
        return []
