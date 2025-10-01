# test_groq_new.py
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

def test_new_groq():
    try:
        api_key = os.getenv("GROQ_API_KEY")
        print(f"GROQ API Key: {api_key[:20]}...")
        
        llm = ChatGroq(
            groq_api_key=api_key,
            model_name="llama-3.3-70b-versatile",  # New model
            temperature=0.1
        )
        
        response = llm.invoke("Hello, how are you?")
        print(f"✅ GROQ API working with new model! Response: {response.content}")
        
    except Exception as e:
        print(f"❌ GROQ API error: {e}")

if __name__ == "__main__":
    test_new_groq()
