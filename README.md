# AI Incident Investigation Assistant

An AI-powered application that helps developers investigate application errors by analyzing log files, retrieving relevant technical knowledge, and generating structured investigation reports with supporting evidence.

## Features

- Upload application `.log` files for investigation.
- Extract error details, exception types, stack traces, and code locations.
- Use an LLM to explain errors and identify possible causes.
- Retrieve relevant technical knowledge using Retrieval-Augmented Generation (RAG).
- Inspect relevant source-code files when additional investigation is required.
- Generate structured reports containing evidence, recommended checks, confidence, and uncertainty.
- Ask follow-up questions about an investigation.
- Expose investigation functionality through a REST API.
- Provide a user interface for uploading logs and viewing investigation results.
- Evaluate AI responses and retrieval quality.

## Tech Stack

| Category | Technology |
|---|---|
| Language | Python |
| Backend | FastAPI |
| Frontend | Streamlit |
| LLM orchestration | LangChain |
| LLM provider | Groq (GPT-OSS 20B) |
| Embedding model | Google Gemini Embedding |
| Vector database | ChromaDB |
| Structured output | Pydantic |
| Evaluation | LangSmith, OpenEvals, RAGAS |
| API testing | Swagger UI |
| Containerization | Docker, Docker Compose |
| Version control | Git, GitHub |
| Deployment | Render (planned) |

## How It Works

1. The user uploads an application log file through the frontend or REST API.
2. FastAPI receives and validates the uploaded file.
3. Python extracts important incident details, including exceptions, stack traces, and code locations.
4. Gemini generates embeddings for the incident query.
5. ChromaDB retrieves relevant technical knowledge using vector similarity search.
6. If required, the source-code investigation component inspects relevant files from the permitted source-code directory.
7. LangChain combines the incident details, retrieved knowledge, and investigation evidence.
8. Groq-hosted GPT-OSS 20B generates a structured investigation report.
9. The application returns the report and supports follow-up questions.

## Project Structure

```text
AI-Incident-Investigation/
│
├── knowledge_base/
│   ├── authentication_error.md
│   └── database_timeout.md
│
├── source_code/
│
├── chroma_db/
│
├── main.py
├── frontend.py
├── incident_assistant.py
├── log_parser.py
├── llm_config.py
├── embedding_config.py
├── source_agent.py
├── source_tools.py
│
├── chroma_test.py
├── groq_test.py
├── requirements.txt
├── Dockerfile
├── frontend.Dockerfile
├── docker-compose.yml
│
├── .env.example
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python environment compatible with the project dependencies.
- Groq API key.
- Google AI Studio API key.
- Git.
- Docker Desktop (optional, for containerized execution).

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd AI-Incident-Investigation
```

### 2. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_api_key
```

Never commit the `.env` file or expose API keys.

### 5. Build the knowledge base

Run the indexing script to generate embeddings for the Markdown documents and store them in ChromaDB:

```bash
python chroma_test.py
```

### 6. Start the backend

```bash
uvicorn main:app --reload
```

### 7. Start the frontend

Open another terminal, activate the virtual environment, and run:

```bash
streamlit run frontend.py
```

### 8. Access the application

- **Frontend:** `http://localhost:8501`
- **Swagger UI:** `http://127.0.0.1:8000/docs`

Upload a `.log` file to generate an incident investigation report.

## Evaluation and Testing

The project includes evaluation and testing of its AI-generated responses and retrieval workflow.

- Validate structured LLM outputs.
- Test knowledge retrieval using ChromaDB.
- Evaluate retrieval and response quality.
- Use LangSmith tracing and evaluation tools.
- Run automated tests using pytest.

## Security

- Keep API keys and environment variables out of GitHub.
- Validate uploaded log files.
- Restrict source-code inspection to permitted directories and file types.
- Prevent unauthorized file access and path traversal.
- Do not execute or modify inspected source-code files.
- Avoid uploading confidential production logs or proprietary source code to external AI providers.

## Current Scope

The application supports log-based incident investigation, knowledge retrieval, optional source-code inspection, structured AI-generated reports, and follow-up questions.

Docker-based containerization has been implemented and tested locally. Cloud deployment to Render is a planned next step.
