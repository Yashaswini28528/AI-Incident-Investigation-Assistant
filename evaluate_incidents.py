
import os

from dotenv import load_dotenv
from langsmith import Client
from langchain_groq import ChatGroq
from openevals.llm import create_llm_as_judge
from incident_assistant import analyze_incident


# 1. Load environment variables
load_dotenv()


# 2. Connect to LangSmith
client = Client()

DATASET_NAME = "Incident-Investigation-Evaluation"
# 3. Configure the LLM judge model
judge_model = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0
)

# 4. Define incident investigation evaluation criteria

INCIDENT_CORRECTNESS_PROMPT = """
You are an expert software incident investigation evaluator.

Evaluate the AI-generated incident report using the original
log and the expected reference output.

Original incident input:
{inputs}

Expected reference output:
{reference_outputs}

AI-generated investigation report:
{outputs}

Evaluate these criteria:

1. Explanation:
   Does the report correctly explain the incident?

2. Possible causes:
   Are the suggested causes technically relevant and plausible?

3. Recommended checks:

   Compare the generated recommended_checks list against
   the reference recommended_checks list.

   Examine every reference recommendation individually.

   Search the entire generated list for a semantically
   equivalent recommendation before marking anything missing.

   Do not penalize different wording when the meaning is
   equivalent.

   Only identify a recommendation as missing when no
   equivalent recommendation exists in the generated report.

   Clearly identify the specific missing recommendation
   in your reasoning.

   Never claim that a recommendation is missing if it is
   already present in the generated report.

4. Evidence and uncertainty:
   Does the report avoid claiming an unverified cause as confirmed?

Scoring:

1.0 = The report is substantially correct, relevant and well-supported.
0.5 = The report is partially correct but has meaningful omissions
      or inaccuracies.
0.0 = The report is substantially incorrect, irrelevant or misleading.

Intermediate decimal scores between 0.0 and 1.0 are allowed.
Do not require exact wording from the reference output.
Judge technical correctness and relevance.

Return your score with a brief explanation.
"""
# 5. Create the LLM-as-a-Judge evaluator

incident_correctness_evaluator = create_llm_as_judge(
    prompt=INCIDENT_CORRECTNESS_PROMPT,
    judge=judge_model,
    continuous=True,
    feedback_key="incident_correctness",
    structured_output_kwargs={
        "method": "json_schema",
        "strict": True
    }
)



# 3. Define our application as the evaluation target
def run_incident_investigation(inputs: dict) -> dict:

    log_text = inputs.get("log_text")

    if not isinstance(log_text, str) or not log_text.strip():
        raise ValueError("A valid log_text input is required")

    report = analyze_incident(log_text)

    # Convert Pydantic output into a Python dictionary
    if hasattr(report, "model_dump"):
        report = report.model_dump()

    elif hasattr(report, "dict"):
        report = report.dict()

    if not isinstance(report, dict):
        raise TypeError("Incident analysis must return a dictionary")

    return report


# 4. Define our first evaluator
def report_completeness(outputs: dict) -> dict:

    required_fields = [
        "explanation",
        "possible_causes",
        "recommended_checks",
        "confidence",
        "uncertainty"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in outputs or outputs[field] is None
    ]

    score = len(missing_fields) == 0

    return {
        "key": "report_completeness",
        "score": score,
        "comment": (
            "All required fields are present."
            if score
            else f"Missing fields: {missing_fields}"
        )
    }
# 5. Run the LangSmith evaluation
if __name__ == "__main__":

    print("Starting incident investigation evaluation...")

    results = client.evaluate(
    run_incident_investigation,
    data=DATASET_NAME,
    evaluators=[
        report_completeness,
        incident_correctness_evaluator
    ],
    experiment_prefix="incident-assistant-llm-judge",
    description=(
        "Incident investigation evaluation using "
        "report completeness and LLM-as-a-Judge."
    )
)

    print("\nEvaluation completed!")
    print(results)