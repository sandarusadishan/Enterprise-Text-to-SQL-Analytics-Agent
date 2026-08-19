# Prompt templates for the Agentic Text-to-SQL and Analytics pipeline

SQL_GENERATION_PROMPT = """
You are an expert SQLite Data Analyst.
Below is the database schema:
{schema}

User Question: "{question}"

Generate a valid, read-only SQLite query to answer the question.
CRITICAL INSTRUCTIONS:
- Return ONLY the raw SQL query. Do NOT use markdown code blocks (like ```sql).
- Do NOT perform updates, drops, or deletes (ONLY SELECT queries).
"""

SQL_FIX_PROMPT = """
The following SQLite query failed to execute.
Schema:
{schema}

Failed Query: {sql_query}
Error Message: {error_message}

User Question: "{question}"

Fix the query and return ONLY the corrected valid SQLite query. Do NOT use markdown code blocks (like ```sql).
"""

ANALYTICS_PROMPT = """
You are a Lead Data Analyst.
User Question: "{question}"
Data Output:
{data_df}

Provide a concise, 2-bullet-point summary highlighting key business insights from this data.
CRITICAL INSTRUCTION:
- If there are monetary values, always use LKR (Sri Lankan Rupee, formatted as 'Rs.' or 'LKR') as the currency. Do NOT use other currency symbols (such as $, ₹, €, etc.).
"""
