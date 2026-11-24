
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app


client = TestClient(app)


def test_home_endpoint():

    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {
        "message": "AI Incident Investigation Assistant API is running"
    }


def test_health_endpoint():

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "healthy"
    }
    

def test_investigate_valid_log_file():

    fake_report = {
        "explanation": "The database connection timed out.",
        "confidence": "medium"
    }

    with patch("main.analyze_incident", return_value=fake_report) as mock_ai:

        response = client.post(
            "/investigate",
            files={
                "file": (
                    "test.log",
                    b"Service: OrderService\nError: Database connection timeout\nMessage: Database connection failed",
                    "text/plain"
                )
            }
        )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Incident investigation completed successfully"
    assert data["filename"] == "test.log"
    assert data["report"] == fake_report

    mock_ai.assert_called_once()


def test_rejects_invalid_file_extension():

    response = client.post(
        "/investigate",
        files={
            "file": (
                "test.txt",
                b"Database connection failed",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == "Only .log files are supported"

def test_rejects_empty_log_file():

    response = client.post(
        "/investigate",
        files={
            "file": (
                "empty.log",
                b"",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == "Log file cannot be empty"

def test_rejects_large_log_file():

    large_log = (
        b"Service: OrderService\n"
        b"Error: Database connection timeout\n"
        + b"A" * 1_000_001
    )

    response = client.post(
        "/investigate",
        files={
            "file": (
                "large.log",
                large_log,
                "text/plain"
            )
        }
    )

    assert response.status_code == 413

    assert response.json()["detail"] == "File size exceeds the 1 MB limit"

def test_rejects_invalid_utf8_file():

    invalid_content = b"\xff\xfe\xfa"

    response = client.post(
        "/investigate",
        files={
            "file": (
                "invalid.log",
                invalid_content,
                "text/plain"
            )
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == "Log file must use UTF-8 encoding"
def test_rejects_log_without_identifiable_exception():

    log_content = (
        "Service: OrderService\n"
        "Message: Order processing started successfully"
    )

    response = client.post(
        "/investigate",
        files={
            "file": (
                "normal.log",
                log_content,
                "text/plain"
            )
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "No identifiable exception found in the log"
    )
def test_handles_unexpected_investigation_error():

    with patch(
        "main.analyze_incident",
        side_effect=Exception("Groq API connection failed")
    ):

        response = client.post(
            "/investigate",
            files={
                "file": (
                    "error.log",
                    "Service: OrderService\n"
                    "Error: DatabaseTimeoutException\n"
                    "Message: Database connection timed out",
                    "text/plain"
                )
            }
        )

    assert response.status_code == 500

    assert response.json()["detail"] == (
        "Investigation failed due to an internal server error"
    )
def test_rejects_empty_original_log_in_follow_up():

    response = client.post(
        "/investigate/follow-up",
        json={
            "log_text": "   ",
            "additional_information": "Database server is running.",
            "follow_up_questions": [
                "Is the database server running?"
            ]
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Original log text cannot be empty"
    )
def test_rejects_empty_additional_information():

    response = client.post(
        "/investigate/follow-up",
        json={
            "log_text": (
                "Service: AuthenticationService\n"
                "Error: InvalidTokenException\n"
                "Message: Invalid API token"
            ),
            "additional_information": "   ",
            "follow_up_questions": [
                "Is the token valid?"
            ]
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Additional information cannot be empty"
    )
    
def test_rejects_follow_up_without_identifiable_exception():

    response = client.post(
        "/investigate/follow-up",
        json={
            "log_text": (
                "Service: AuthenticationService\n"
                "Message: Application started successfully"
            ),
            "additional_information": "The server is running.",
            "follow_up_questions": [
                "Is the server running?"
            ]
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "No identifiable exception found in the original log"
    )
def test_successful_follow_up_investigation():

    fake_report = {
        "explanation": "The database connection failed.",
        "possible_causes": ["Database connectivity issue"],
        "confirmed_findings": ["Database server is unreachable"],
        "finding_sources": ["Uploaded log"],
        "investigation_metadata": {},
        "unverified_assumptions": [],
        "confidence": "high",
        "recommended_checks": ["Check database connectivity"],
        "uncertainty": "No additional uncertainty",
        "needs_more_information": False,
        "follow_up_questions": []
    }

    log_text = (
        "Service: DatabaseService\n"
        "Error: DatabaseTimeoutException\n"
        "Message: Database connection timed out"
    )

    additional_information = (
        "The database server is unreachable."
    )

    with patch(
        "main.validate_developer_answer",
        return_value={
            "status": "relevant",
            "reason": "The answer provides useful information."
        }
    ) as mock_validation:

        with patch(
            "main.analyze_incident",
            return_value=fake_report
        ) as mock_analysis:

            response = client.post(
                "/investigate/follow-up",
                json={
                    "log_text": log_text,
                    "additional_information": additional_information,
                    "follow_up_questions": [
                        "Is the database server reachable?"
                    ]
                }
            )

    assert response.status_code == 200

    assert response.json()["message"] == (
        "Follow-up investigation completed successfully"
    )

    assert response.json()["report"] == fake_report

    mock_validation.assert_called_once_with(
        log_text,
        ["Is the database server reachable?"],
        additional_information
    )

    mock_analysis.assert_called_once_with(
        log_text,
        additional_information
    ) 
def test_rejects_irrelevant_follow_up_information():

    log_text = (
        "Service: AuthenticationService\n"
        "Error: InvalidTokenException\n"
        "Message: Invalid API token"
    )

    additional_information = (
        "The application server was restarted."
    )

    with patch(
        "main.validate_developer_answer",
        return_value={
            "status": "irrelevant",
            "reason": "The answer does not address the question."
        }
    ) as mock_validation:

        with patch(
            "main.analyze_incident"
        ) as mock_analysis:

            response = client.post(
                "/investigate/follow-up",
                json={
                    "log_text": log_text,
                    "additional_information": additional_information,
                    "follow_up_questions": [
                        "Is the token present in the token store?"
                    ]
                }
            )

    assert response.status_code == 200

    assert response.json()["message"] == (
        "Additional information needs attention"
    )

    assert response.json()["report"] is None

    assert response.json()["validation"]["status"] == "irrelevant"

    mock_validation.assert_called_once()

    mock_analysis.assert_not_called()
def test_rejects_follow_up_request_with_missing_fields():

    response = client.post(
        "/investigate/follow-up",
        json={
            "log_text": "Some incident log"
        }
    )

    assert response.status_code == 422

    response_details = response.json()["detail"]

    missing_fields = [
        error["loc"][-1]
        for error in response_details
    ]

    assert "additional_information" in missing_fields

    assert "follow_up_questions" in missing_fields