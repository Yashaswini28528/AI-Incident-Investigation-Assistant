import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


# 1. Load environment variables
load_dotenv()


# 2. Retrieve the Groq API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env")


# 3. Create the shared Groq model
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.5,
    api_key=GROQ_API_KEY,

    # Reliability settings
    timeout=30,
    max_retries=2
)