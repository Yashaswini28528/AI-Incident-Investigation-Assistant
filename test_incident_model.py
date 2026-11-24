
from incident_assistant import IncidentAnalysis
import pytest


def test_create_valid_incident_report():

    report = IncidentAnalysis(
        explanation="The database connection timed out.",
        possible_causes=["Connection pool exhaustion"],
        confirmed_findings=["The database connection timed out."],
        finding_sources=["Uploaded log - Error details"],
        investigation_metadata={
            "source_inspection_performed": False
        },
        unverified_assumptions=[],
        confidence="medium",
        recommended_checks=["Check database connection pool metrics."],
        uncertainty="Connection pool metrics are unavailable.",
        needs_more_information=True,
        follow_up_questions=["What was the active connection count?"]
    )

    assert report.explanation == "The database connection timed out."
    assert report.confidence == "medium"
    assert report.needs_more_information is True
    assert len(report.possible_causes) == 1
    assert len(report.confirmed_findings) == 1
    

def test_possible_causes_are_copied_to_unverified_assumptions():

    report = IncidentAnalysis(
        explanation="The database connection timed out.",
        possible_causes=[
            "Connection pool exhaustion",
            "Database server overload"
        ],
        confirmed_findings=["The connection timed out."],
        finding_sources=["Uploaded log"],
        investigation_metadata={},
        unverified_assumptions=[],
        confidence="low",
        recommended_checks=["Check connection pool metrics."],
        uncertainty="The exact cause is unknown.",
        needs_more_information=True,
        follow_up_questions=["What are the connection pool metrics?"]
    )

    assert report.unverified_assumptions == [
        "Connection pool exhaustion",
        "Database server overload"
    ]
    

def test_removes_source_inspection_status_from_confirmed_findings():

    report = IncidentAnalysis(
        explanation="The database connection timed out.",
        possible_causes=["Connection pool exhaustion"],
        confirmed_findings=[
            "The database connection timed out.",
            "Source-code inspection was not performed."
        ],
        finding_sources=[
            "Uploaded log",
            "Uploaded log"
        ],
        investigation_metadata={},
        unverified_assumptions=[],
        confidence="medium",
        recommended_checks=["Check connection pool metrics."],
        uncertainty="The exact cause is unknown.",
        needs_more_information=True,
        follow_up_questions=["What are the connection pool metrics?"]
    )

    assert report.confirmed_findings == [
        "The database connection timed out."
    ]

def test_rejects_invalid_confidence_value():

    with pytest.raises(ValueError):

        IncidentAnalysis(
            explanation="The database connection timed out.",
            possible_causes=["Connection pool exhaustion"],
            confirmed_findings=["The connection timed out."],
            finding_sources=["Uploaded log"],
            investigation_metadata={},
            unverified_assumptions=[],
            confidence="very_high",
            recommended_checks=["Check connection pool metrics."],
            uncertainty="The exact cause is unknown.",
            needs_more_information=True,
            follow_up_questions=["What are the connection pool metrics?"]
        )

def test_rejects_missing_required_field():

    with pytest.raises(ValueError):

        IncidentAnalysis(
            possible_causes=["Connection pool exhaustion"],
            confirmed_findings=["The connection timed out."],
            finding_sources=["Uploaded log"],
            investigation_metadata={},
            unverified_assumptions=[],
            confidence="medium",
            recommended_checks=["Check connection pool metrics."],
            uncertainty="The exact cause is unknown.",
            needs_more_information=True,
            follow_up_questions=["What are the connection pool metrics?"]
        )



