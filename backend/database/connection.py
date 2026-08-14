import sqlite3

DB_PATH = "company_sales.db"

def get_db_connection():
    """Establishes and returns a connection to the local SQLite database"""
    return sqlite3.connect(DB_PATH)
