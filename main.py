
from fastapi import FastAPI, UploadFile, File, HTTPException

from incident_assistant import analyze_incident


# Create the FastAPI application
app = FastAPI(
    title="AI Incident Investigation Assistant",
    description="API for investigating application incidents using Generative AI",
    version="1.0.0"
)


# 1. Root endpoint
@app.get("/")
def home():
    return {
        "message": "Welcome to AI Incident Investigation Assistant",
        "status": "running"
    }


# 2. Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Incident Investigation Backend"
    }


# 3. Main incident investigation endpoint
@app.post("/investigate")
async def investigate(file: UploadFile = File(...)):

    # Validate the uploaded file
    if not file.filename or not file.filename.lower().endswith(".log"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a .log file"
        )

    try:
        # Read the uploaded log file
        log_content = await file.read()

        # Convert bytes into readable text
        log_text = log_content.decode("utf-8")

        # Check whether the uploaded log file is empty
        if not log_text.strip():
         raise HTTPException(
        status_code=400,
        detail="The uploaded log file is empty"
    )

        # Send log text to our AI investigation pipeline
        report = analyze_incident(log_text)

        # Return the AI investigation report
        return {
            "message": "Incident investigation completed successfully",
            "filename": file.filename,
            "report": report
        }

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file must contain valid UTF-8 text"
        )

    except HTTPException:
     raise

    except Exception as e:
     raise HTTPException(
        status_code=500,
        detail="Incident investigation failed due to an internal server error"
    )
