
import json
import os
import chromadb
import ollama

from log_parser import extract_log_details

from langchain_groq import ChatGroq
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from pydantic import BaseModel, Field


# 1. Define the AI investigation report structure
class IncidentAnalysis(BaseModel):

    explanation: str = Field(
        description="Simple explanation of the application error"
    )

    possible_causes: list[str] = Field(
        description="Unconfirmed hypotheses that could explain the error"
    )

    recommended_checks: list[str] = Field(
        description="Practical steps to investigate the possible causes"
    )

    uncertainty: str = Field(
        description="Missing information and why the root cause is not confirmed"
    )


# 2. Create the output parser
parser = PydanticOutputParser(
    pydantic_object=IncidentAnalysis
)


# 3. Connect to the Groq-hosted GPT-OSS model
load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.5,
    api_key=os.getenv("GROQ_API_KEY")
)


# 4. Connect to ChromaDB
client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="incident_knowledge"
)


# 5. Create the AI investigation prompt
prompt = ChatPromptTemplate.from_template("""
You are an experienced software incident investigation assistant.

Analyse the following application error.

Service: {service}
Error Type: {error_type}
Error Message: {error_message}

Stack Trace:
{stack_trace}

Code Locations:
{code_locations}

Retrieved Knowledge:
{retrieved_knowledge}

Your responsibilities:

1. Explain the error in simple technical language.

2. Possible Causes:
   - Suggest only underlying reasons that could explain the observed error.
   - Never repeat the error message or exception type as a possible cause.
   - Each cause must be a distinct, plausible explanation.
   - Treat all causes as unconfirmed hypotheses.

3. Recommended Checks:
   - Suggest practical troubleshooting steps.
   - Connect each check to a possible cause where possible.
   - Do not recommend unrelated actions.

4. Uncertainty:
   - Explain what additional information is needed.
   - State clearly if the exact root cause cannot be determined.

Important rules:

- Never invent facts, file names or line numbers.
- Use only the information supplied.
- If information is insufficient, say so.
- Do not confuse symptoms with underlying causes.

{format_instructions}
""")


# 6. Connect prompt, model and parser
chain = prompt | llm | parser


# 7. Main reusable investigation function
def analyze_incident(log_text: str) -> dict:

    # Extract incident information from uploaded log text
    incident_data = extract_log_details(log_text)

    # Generate an embedding for the application error
    query = incident_data["error_message"]

    query_response = ollama.embed(
        model="nomic-embed-text",
        input=query
    )

    query_embedding = query_response["embeddings"][0]

    # Retrieve relevant knowledge from ChromaDB
    if collection.count() > 0:

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=1
        )

        retrieved_documents = results["documents"][0]

        retrieved_knowledge = (
            retrieved_documents[0]
            if retrieved_documents
            else "No relevant knowledge found."
        )

    else:
        retrieved_knowledge = "No relevant knowledge found."

    print("\n===== RETRIEVED KNOWLEDGE =====")
    print(retrieved_knowledge)

    # Generate evidence directly from extracted log data
    evidence = [
        f"Service: {incident_data['service']}",
        f"Error Type: {incident_data['error_type']}",
        f"Error Message: {incident_data['error_message']}",
    ]

    for location in incident_data["code_locations"]:
        evidence.append(
            f"Code Location: {location}"
        )

    # Send extracted information to the AI
    response = chain.invoke({
        "service": incident_data["service"],
        "error_type": incident_data["error_type"],
        "error_message": incident_data["error_message"],
        "stack_trace": incident_data["stack_trace"],
        "code_locations": json.dumps(
            incident_data["code_locations"]
        ),
        "format_instructions": parser.get_format_instructions(),
        "retrieved_knowledge": retrieved_knowledge
    })

    # Combine AI-generated analysis with Python-generated evidence
    final_report = response.model_dump()

    final_report["evidence"] = evidence

    # Return the investigation report to the caller
    return final_report


# 8. Allow standalone testing of this file
if __name__ == "__main__":

    with open("sample.log", "r", encoding="utf-8") as file:
        log_text = file.read()

    report = analyze_incident(log_text)

    print("\n===== AI INCIDENT INVESTIGATION REPORT =====\n")

    print(json.dumps(report, indent=4))
