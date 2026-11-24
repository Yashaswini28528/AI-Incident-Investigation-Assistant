
import textwrap

from log_parser import extract_log_details


def test_extract_simple_error_log():

    log_text = textwrap.dedent("""
        Service: AuthenticationService
        Error: Invalid API token
        Message: The API token provided by the client is invalid.
    """)

    result = extract_log_details(log_text)

    assert result["service"] == "AuthenticationService"
    assert result["error_type"] == "Invalid API token"
    assert result["error_message"] == "The API token provided by the client is invalid."
    assert result["code_locations"] == []
    assert result["stack_trace"] is None

def test_extract_exception_log():

    log_text = textwrap.dedent("""
        2026-11-15 10:30:45
        Service: OrderService
        RequestId: REQ-1024

        Traceback (most recent call last):
          File "app/orders.py", line 42, in create_order
            connection = database.get_connection()

          File "app/database.py", line 18, in get_connection
            raise TimeoutException("Database connection timeout")

        TimeoutException: Database connection timeout
    """)

    result = extract_log_details(log_text)

    assert result["service"] == "OrderService"
    assert result["request_id"] == "REQ-1024"
    assert result["error_type"] == "TimeoutException"
    assert result["error_message"] == "Database connection timeout"
    assert len(result["code_locations"]) == 2
    assert result["code_locations"][0]["file"] == "app/orders.py"
    assert result["code_locations"][0]["line"] == 42
    assert result["stack_trace"] is not None
    

def test_extract_log_with_missing_fields():

    log_text = "Error: Database connection failed"

    result = extract_log_details(log_text)

    assert result["timestamp"] is None
    assert result["service"] is None
    assert result["request_id"] is None
    assert result["error_type"] == "Database connection failed"
    assert result["error_message"] == "Database connection failed"
    assert result["code_locations"] == []
    assert result["stack_trace"] is None


def test_extract_multiple_code_locations():

    log_text = textwrap.dedent("""
        Service: OrderService

        Traceback (most recent call last):
          File "app/orders.py", line 42, in create_order
            connection = database.get_connection()

          File "app/database.py", line 18, in get_connection
            raise TimeoutException("Database connection timeout")

        TimeoutException: Database connection timeout
    """)

    result = extract_log_details(log_text)

    assert len(result["code_locations"]) == 2

    assert result["code_locations"][0] == {
        "file": "app/orders.py",
        "line": 42
    }

    assert result["code_locations"][1] == {
        "file": "app/database.py",
        "line": 18
    }

def test_extract_timestamp():

    log_text = textwrap.dedent("""
        2026-11-15 10:30:45
        Service: OrderService
        Error: Database connection failed
    """)

    result = extract_log_details(log_text)

    assert result["timestamp"] == "2026-11-15 10:30:45"
    

def test_extract_log_without_error():

    log_text = textwrap.dedent("""
        2026-11-15 10:30:45
        Service: OrderService
        RequestId: REQ-1024
    """)

    result = extract_log_details(log_text)

    assert result["timestamp"] == "2026-11-15 10:30:45"
    assert result["service"] == "OrderService"
    assert result["request_id"] == "REQ-1024"
    assert result["error_type"] is None
    assert result["error_message"] is None
    assert result["code_locations"] == []
    assert result["stack_trace"] is None



