
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


# Load environment variables from .env
load_dotenv()


# Create the shared Groq model
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.5,
    api_key=os.getenv("GROQ_API_KEY")
)
