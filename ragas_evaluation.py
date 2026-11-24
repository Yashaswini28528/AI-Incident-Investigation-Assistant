
import asyncio
import json
import os

import instructor
from dotenv import load_dotenv
from openai import AsyncOpenAI
from langsmith import Client

from ragas.llms import llm_factory
from ragas.metrics.collections import (
    Faithfulness,
    ContextPrecision,
    ContextRecall
)

from incident_assistant import analyze_incident
from log_parser import extract_log_details


# 1. Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env")


# 2. Connect to the LangSmith dataset
DATASET_NAME = "Incident-Investigation-Evaluation"

langsmith_client = Client()


# 3. Connect to Groq through its OpenAI-compatible endpoint
groq_client = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    timeout=120,
    max_retries=1
)


# 4. Initialize the RAGAS evaluation model
ragas_llm = llm_factory(
    model="openai/gpt-oss-20b",
    provider="openai",
    client=groq_client,
    mode=instructor.Mode.MD_JSON,
    max_tokens=8192,
    reasoning_effort="low"
)


# 5. Initialize the three RAGAS metrics
faithfulness_metric = Faithfulness(llm=ragas_llm)

context_precision_metric = ContextPrecision(llm=ragas_llm)

context_recall_metric = ContextRecall(llm=ragas_llm)


# 6. Configure evaluation limits
MAX_EXAMPLES = 1

RATE_LIMIT_COOLDOWN = 35


# 7. Run one metric with limited retry handling
async def calculate_metric(name, metric, **kwargs):

    print(f"\nCalculating {name}...")

    # Allow the previous model requests to leave
    # Groq's token-per-minute window.
    await asyncio.sleep(RATE_LIMIT_COOLDOWN)

    for attempt in range(2):

        try:
            result = await metric.ascore(**kwargs)

            score = result.value

            print(f"{name}: {score:.3f}")

            return score

        except Exception as error:

            error_message = str(error)

            is_rate_limit = (
                "429" in error_message
                or "rate_limit" in error_message.lower()
            )

            if is_rate_limit and attempt == 0:

                print(
                    "Groq rate limit reached. "
                    "Waiting before one retry..."
                )

                await asyncio.sleep(RATE_LIMIT_COOLDOWN)

                continue

            print(f"{name} could not be calculated.")
            print(f"Reason: {error}")

            return None

    return None


# 8. Evaluate one incident
async def evaluate_example(example):

    inputs = example.inputs or {}
    reference_outputs = example.outputs or {}

    log_text = inputs.get("log_text")

    if not isinstance(log_text, str) or not log_text.strip():
        print("Skipping: Missing incident log.")
        return

    if not reference_outputs:
        print("Skipping: Missing reference output.")
        return

    print("\n===================================")
    print("Starting RAGAS incident evaluation")
    print("===================================")

    # Extract the actual query used by ChromaDB
    incident_data = extract_log_details(log_text)

    retrieval_query = incident_data["error_message"]

    # Run the real application and capture retrieval results
    report = analyze_incident(
        log_text,
        include_retrieval_context=True
    )

    retrieved_contexts = report.pop(
        "_ragas_retrieved_contexts",
        []
    )

    if not retrieved_contexts:
        print("No relevant ChromaDB documents retrieved.")
        print("Cannot evaluate retrieval quality for this example.")
        return

    print("\nRetrieved documents:", len(retrieved_contexts))

    # Include both the uploaded log and retrieved knowledge
    # because the application uses both as evidence.
    faithfulness_contexts = [
        log_text,
        *retrieved_contexts
    ]

    # Keep only the actual AI-generated report fields
    response_fields = [
        "explanation",
        "possible_causes",
        "confirmed_findings",
        "unverified_assumptions",
        "recommended_checks",
        "uncertainty"
    ]

    generated_report = {
        field: report.get(field)
        for field in response_fields
    }

    response_text = json.dumps(
        generated_report,
        indent=2,
        ensure_ascii=False
    )

    # Use the expected investigation content as reference
    reference_fields = [
        "explanation",
        "possible_causes",
        "recommended_checks",
        "uncertainty"
    ]

    reference_report = {
        field: reference_outputs[field]
        for field in reference_fields
        if field in reference_outputs
    }

    reference_text = json.dumps(
        reference_report,
        indent=2,
        ensure_ascii=False
    )

    # 9. Evaluate faithfulness
    faithfulness_score = await calculate_metric(
        "Faithfulness",
        faithfulness_metric,
        user_input=log_text,
        response=response_text,
        retrieved_contexts=faithfulness_contexts
    )

    # 10. Evaluate retrieval precision
    precision_score = await calculate_metric(
        "Context Precision",
        context_precision_metric,
        user_input=retrieval_query,
        reference=reference_text,
        retrieved_contexts=retrieved_contexts
    )

    # 11. Evaluate retrieval recall
    recall_score = await calculate_metric(
        "Context Recall",
        context_recall_metric,
        user_input=retrieval_query,
        retrieved_contexts=retrieved_contexts,
        reference=reference_text
    )

    # 12. Display final scores
    print("\n===================================")
    print("       FINAL RAGAS RESULTS")
    print("===================================")

    print(f"Faithfulness:       {faithfulness_score}")
    print(f"Context Precision:  {precision_score}")
    print(f"Context Recall:     {recall_score}")

    print("===================================")


# 13. Run the evaluation
async def main():

    try:
        examples = list(
            langsmith_client.list_examples(
                dataset_name=DATASET_NAME
            )
        )

        if not examples:
            print("No evaluation examples found.")
            return

        selected_examples = examples[:MAX_EXAMPLES]

        print("\nStarting RAGAS evaluation...")
        print("Dataset:", DATASET_NAME)
        print("Examples selected:", len(selected_examples))

        for example in selected_examples:
            await evaluate_example(example)

        print("\nRAGAS evaluation finished.")

    finally:
        await groq_client.close()


if __name__ == "__main__":
    asyncio.run(main())
