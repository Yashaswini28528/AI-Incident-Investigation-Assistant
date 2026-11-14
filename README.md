# AI Incident Investigation Assistant

An AI-powered application that helps developers investigate application errors by analyzing log files, retrieving relevant technical knowledge, and generating structured investigation reports.

## Features

- Upload application `.log` files for investigation.
- Extract error details, exception types, stack traces, and code locations.
- Use an LLM to explain errors and suggest possible causes.
- Retrieve relevant technical knowledge using RAG.
- Generate structured reports with evidence, recommended checks, and uncertainty.
- Expose investigation functionality through a REST API.

## Tech Stack

- **Language:** Python
- **Backend:** FastAPI
- **LLM orchestration:** LangChain
- **LLM provider:** Groq
- **Embeddings:** Ollama – nomic-embed-text
- **Vector database:** ChromaDB
- **API testing:** Swagger UI

## How It Works

1. Upload an application log file.
2. FastAPI receives and validates the file.
3. Python extracts important incident details.
4. Ollama generates embeddings for the error.
5. ChromaDB retrieves relevant technical knowledge.
6. LangChain sends the context to the Groq-hosted LLM.
7. The API returns a structured investigation report.

## Project Structure

```text
AI-Incident-Investigation-Assistant/
│
├── knowledge_base/
│   └── database_timeout.md
│
├── main.py
├── incident_assistant.py
├── log_parser.py
├── embedding_test.py
├── chroma_test.py
├── groq_test.py
├── langchain_test.py
├── sample.log
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.13
- Ollama
- A Groq API key

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd AI-Incident-Investigation-Assistant
```

### 2. Create and activate a virtual environment

```bash
py -3.13 -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

### 5. Start Ollama

Ensure Ollama is running and the embedding model is available:

```bash
ollama pull nomic-embed-text
```

### 6. Start the backend

```bash
uvicorn main:app --reload
```

### 7. Open Swagger UI

Visit:

`http://127.0.0.1:8000/docs`

Upload a `.log` file using the `/investigate` endpoint to generate an incident investigation report.

## Current Scope

This version supports log-file-based incident investigation with knowledge retrieval and AI-generated analysis. Additional capabilities such as source-code investigation, advanced workflow orchestration, and deployment can be added in future versions.

## Security

Never commit API keys, `.env` files, or other sensitive credentials to the repository.