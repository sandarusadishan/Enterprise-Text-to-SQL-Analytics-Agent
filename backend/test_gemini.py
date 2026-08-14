import os
from langchain_google_genai import ChatGoogleGenerativeAI

# Correct model name for LangChain Google GenAI integration
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0
)

# Test Prompt එකක් යැවීම
try:
    response = llm.invoke("Hello! Say 'Gemini is connected successfully for Text-to-SQL Agent' if you can read this.")
    print("\n🤖 Gemini Response:")
    print(response.content)
except Exception as e:
    print(f"\n❌ Error: {e}")