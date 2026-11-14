from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

# Load the API key from .env
load_dotenv()

# Connect to Groq
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.5,
    api_key=os.getenv("GROQ_API_KEY")
)

# Send a test question
response = llm.invoke("Explain a database connection timeout in simple words.")

# Display the response
print(response.content)