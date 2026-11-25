
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from incident_assistant import (
    analyze_incident,
    validate_developer_answer
)
from log_parser import extract_log_details
import logging
from starlette.concurrency import run_in_threadpool


# 1. Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 2. Create FastAPI application
app = FastAPI(
    title="AI Incident Investigation Assistant",
    description="API for investigating application errors using Generative AI",
    version="1.0.0"
)


# 3. Follow-up request model
class FollowUpRequest(BaseModel):
    log_text: str
    additional_information: str
    follow_up_questions: list[str]
    previous_answers: list[str] = Field(default_factory=list)
    previous_questions: list[str] = Field(default_factory=list)


# 4. Home endpoint
@app.get("/")
async def home():
    return {
        "message": "AI Incident Investigation Assistant API is running"
    }


# 5. Health endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy"
    }


# 6. Initial investigation endpoint
@app.post("/investigate")
async def investigate(file: UploadFile = File(...)):

    try:
        if not file.filename or not file.filename.lower().endswith(".log"):
            raise HTTPException(
                status_code=400,
                detail="Only .log files are supported"
            )

        log_bytes = await file.read(1_000_001)

        if len(log_bytes) > 1_000_000:
            raise HTTPException(
                status_code=413,
                detail="File size exceeds the 1 MB limit"
            )

        try:
            log_text = log_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Log file must use UTF-8 encoding"
            )

        if not log_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Log file cannot be empty"
            )

        incident_data = extract_log_details(log_text)

        if not incident_data["error_type"] or not incident_data["error_message"]:
            raise HTTPException(
                status_code=400,
                detail="No identifiable exception found in the log"
            )

        report = await run_in_threadpool(
            analyze_incident,
            log_text
        )

        return {
            "message": "Incident investigation completed successfully",
            "filename": file.filename,
            "report": report
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Unexpected error during investigation")

        raise HTTPException(
            status_code=500,
            detail="Investigation failed due to an internal server error"
        )


# 7. Follow-up investigation endpoint
@app.post("/investigate/follow-up")
async def investigate_follow_up(request: FollowUpRequest):

    try:
        if not request.log_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Original log text cannot be empty"
            )

        if not request.additional_information.strip():
            raise HTTPException(
                status_code=400,
                detail="Additional information cannot be empty"
            )

        incident_data = extract_log_details(request.log_text)

        if not incident_data["error_type"] or not incident_data["error_message"]:
            raise HTTPException(
                status_code=400,
                detail="No identifiable exception found in the original log"
            )

        # Validate only the answers submitted in the current round
        validation = await run_in_threadpool(
            validate_developer_answer,
            request.log_text,
            request.follow_up_questions,
            request.additional_information
        )

        status = validation.get("status", "").lower()

        # Reject only greetings and unrelated responses.
        # Useful partial answers and unavailable information
        # must still produce an updated investigation.
        if status in {"greeting", "unrelated"}:
            return {
                "message": "Additional information needs attention",
                "validation": validation,
                "report": None
            }

        # Retain all previously accepted answers and the current answer
        all_answers = request.previous_answers + [
            request.additional_information
        ]

        # Tell the investigation which questions have already been asked.
        # This helps prevent the same questions from being repeated.
        history_context = ""

        if request.previous_questions:
            history_context = (
                "QUESTIONS ALREADY ASKED IN PREVIOUS ROUNDS:\n"
                + "\n".join(
                    f"- {question}"
                    for question in request.previous_questions
                )
                + "\n\nDo not repeat these questions."
            )

        cumulative_information = "\n\n".join(all_answers)

        if history_context:
            cumulative_information = (
                history_context
                + "\n\nANSWERS RECEIVED SO FAR:\n"
                + cumulative_information
            )

        # Generate an updated report even when the answer is partial
        # or the requested information is unavailable.
        report = await run_in_threadpool(
            analyze_incident,
            request.log_text,
            cumulative_information
        )

        return {
            "message": "Follow-up investigation completed successfully",
            "validation": validation,
            "report": report
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Unexpected error during follow-up investigation"
        )

        raise HTTPException(
            status_code=500,
            detail="Follow-up investigation failed due to an internal server error"
        )
