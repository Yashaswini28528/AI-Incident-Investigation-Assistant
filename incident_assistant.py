
import json

import chromadb
import ollama
from typing import Literal

from log_parser import extract_log_details

from llm_config import llm

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from pydantic import BaseModel, Field
from source_agent import inspect_source_code


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

    needs_more_information: bool = Field(
        description="Whether additional evidence is required for investigation"
    )

    follow_up_questions: list[str] = Field(
        description="Specific questions to ask the developer for missing evidence"
    )

class AnswerValidation(BaseModel):

    status: Literal[
        "relevant",
        "partially_relevant",
        "greeting",
        "unrelated"
    ] = Field(
        description="Category of the developer's submitted message"
    )

    response: str = Field(
        description="A natural response to the developer's message"
    )


# 2. Create the output parser
parser = PydanticOutputParser(
    pydantic_object=IncidentAnalysis
)


# 3. Connect to the Groq-hosted GPT-OSS model



# 4. Connect to ChromaDB
client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="incident_knowledge"
)


# 5. Configure retrieval settings
RETRIEVAL_LIMIT = 3
DISTANCE_THRESHOLD = 0.70


# 6. Create the AI investigation prompt
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

Source Code Findings:
{source_code_findings}

Retrieved Knowledge:
{retrieved_knowledge}

Additional Information Provided by Developer:
{additional_information}

Your responsibilities:

1. Main Problem:
   - Explain the exact observed problem in one or two short sentences.
   - Focus on what failed and why the operation failed.

2. Possible Causes:
   - Suggest a maximum of TWO most likely underlying causes.
   - Prioritize causes supported by the available evidence.
   - Never repeat the error message as a cause.
   - Do not invent causes when evidence is insufficient.

3. Recommended Checks:
   - Suggest a maximum of TWO specific troubleshooting actions.
   - Each action should help verify one of the possible causes.
   - Prioritize the most useful checks.

4. Uncertainty:
   - State what cannot be confirmed from the available evidence.
   - Identify the specific missing information needed for further investigation.

5. Follow-up Investigation:
   - Decide whether additional evidence is required.
   - Set needs_more_information to true if important evidence is missing.
   - Generate specific follow-up questions for the developer.
   - Ask only questions relevant to the current incident.
   - If sufficient evidence is available, set needs_more_information to false
     and return an empty follow_up_questions list.

Important rules:

- Keep the entire report concise and developer-friendly.
- Never provide long lists or lengthy explanations.
- Never invent facts, file names or line numbers.
- Use only the supplied logs, code locations and retrieved knowledge.
- Distinguish observed facts from unconfirmed hypotheses.
- If evidence supports only one possible cause, provide only one.
- Never claim that a root cause is confirmed without sufficient evidence.
- Never ask unnecessary follow-up questions.
- Do not claim that an incident is resolved merely because a report was generated.
- Use source-code findings only when they are available.
- Distinguish actual code observations from possible causes.
- Do not assume that inspected code caused the exception.
- If source-code inspection could not find a file, mention that
  the source code was unavailable.
- Never claim a root cause is confirmed without sufficient evidence.

{format_instructions}
""")


# 7. Connect prompt, model and parser
chain = prompt | llm | parser

# Validate developer's submitted answers
validation_parser = PydanticOutputParser(
    pydantic_object=AnswerValidation
)

validation_prompt = ChatPromptTemplate.from_template("""
You are an answer validation assistant for an AI Incident Investigation system.

Your job is to understand the developer's message and classify it.

Original incident:
{incident_error}

Investigation questions:
{follow_up_questions}

Developer's message:
{developer_answer}

Classify the message into exactly one category:

1. relevant:
The message provides useful information that helps answer the investigation questions.

2. partially_relevant:
The message provides some useful incident information but important details are still missing.

3. greeting:
The message contains greetings or casual conversation such as:
Hi, hello, how are you, have you had lunch, or have you had dinner.

4. unrelated:
The message contains requests or questions unrelated to incident investigation,
such as predicting the future, writing poems, jokes, general knowledge questions,
or unrelated personal questions.

Important rules:
- Understand the meaning of the message, not just individual keywords.
- Do not classify greetings as relevant evidence.
- Do not invent incident information.
- If the message contains both useful evidence and casual conversation,
  classify it based on the useful evidence.
- For greetings, respond naturally and politely, then guide the developer
  back to the investigation.
- For unrelated messages, politely explain that you are an incident
  investigation assistant and redirect the developer.
- For partially relevant messages, ask for the missing details.
- For relevant messages, acknowledge the useful information.

{format_instructions}
""")

validation_chain = validation_prompt | llm | validation_parser

def validate_developer_answer(
    log_text: str,
    follow_up_questions: list[str],
    developer_answer: str
) -> dict:

    incident_data = extract_log_details(log_text)

    response = validation_chain.invoke({
        "incident_error": incident_data["error_message"],
        "follow_up_questions": "\n".join(follow_up_questions),
        "developer_answer": developer_answer,
        "format_instructions": validation_parser.get_format_instructions()
    })

    return response.model_dump()


# 8. Main reusable investigation function

def analyze_incident(
    log_text: str,
    additional_information: str = ""
) -> dict:

    # 1. Extract incident information from uploaded log text
    incident_data = extract_log_details(log_text)

    # 2. Generate an embedding for the application error
    query = incident_data["error_message"]

    query_response = ollama.embed(
        model="nomic-embed-text",
        input=query
    )

    query_embedding = query_response["embeddings"][0]

    # 3. Retrieve relevant knowledge from ChromaDB
    document_count = collection.count()

    if document_count > 0:

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(RETRIEVAL_LIMIT, document_count)
        )

        retrieved_documents = results["documents"][0]
        retrieved_distances = results["distances"][0]

        # Filter documents using the distance threshold
        relevant_documents = [
            document
            for document, distance in zip(
                retrieved_documents,
                retrieved_distances
            )
            if distance <= DISTANCE_THRESHOLD
        ]

        if relevant_documents:
            retrieved_knowledge = "\n\n".join(relevant_documents)
        else:
            retrieved_knowledge = (
                "No sufficiently relevant knowledge found."
            )

    else:
        retrieved_knowledge = "No relevant knowledge found."

    print("\n===== RETRIEVED KNOWLEDGE =====")
    print(retrieved_knowledge)
    print("==============================\n")

    # 4. Generate evidence directly from extracted log data
    evidence = [
        f"Service: {incident_data['service']}",
        f"Error Type: {incident_data['error_type']}",
        f"Error Message: {incident_data['error_message']}",
    ]

    for location in incident_data["code_locations"]:
        evidence.append(
            f"Code Location: {location}"
        )

    # 5. Inspect source code when code locations are available
    source_code_findings = (
        "Source-code inspection was not performed because "
        "no code locations were provided."
    )

    if incident_data["code_locations"]:

        # Extract file paths from the parsed code locations
        file_paths = [
            location["file"]
            for location in incident_data["code_locations"]
            if isinstance(location, dict)
            and location.get("file")
        ]

        if file_paths:

            incident_context = f"""
            Service: {incident_data['service']}
            Error Type: {incident_data['error_type']}
            Error Message: {incident_data['error_message']}

            Stack Trace:
            {incident_data['stack_trace']}

            Code Locations:
            {json.dumps(file_paths)}

            Inspect the provided source files if useful.
            Inspect all listed files that are available.
            Only use these exact file paths.
            """

            source_code_findings = inspect_source_code(
                incident_context
            )

        else:
            source_code_findings = (
                "Code locations were present, but no valid "
                "file paths could be extracted."
            )

    # 6. Send extracted information to the AI
    response = chain.invoke({
        "service": incident_data["service"],
        "error_type": incident_data["error_type"],
        "error_message": incident_data["error_message"],
        "stack_trace": incident_data["stack_trace"],
        "code_locations": json.dumps(
            incident_data["code_locations"]
        ),
        "format_instructions": parser.get_format_instructions(),
        "retrieved_knowledge": retrieved_knowledge,
        "additional_information": additional_information,
        "source_code_findings": source_code_findings,
    })

    # 7. Combine AI-generated analysis with Python-generated evidence
    final_report = response.model_dump()

    final_report["evidence"] = evidence

    # 8. Return the investigation report
    return final_report



# 9. Allow standalone testing of this file
if __name__ == "__main__":

    with open("sample.log", "r", encoding="utf-8") as file:
        log_text = file.read()

    report = analyze_incident(log_text)

    print("\n===== AI INCIDENT INVESTIGATION REPORT =====\n")

    print(json.dumps(report, indent=4))
