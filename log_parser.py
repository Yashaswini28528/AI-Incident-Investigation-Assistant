
import re
import json

# Read application logs from a file
with open("sample.log", "r", encoding="utf-8") as file:
    log_text = file.read()


# Function to extract information from application logs
def extract_log_details(log_text):

    # Patterns used to identify information in the log
    patterns = {
        "timestamp": r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}",
        "service": r"Service:\s*(.+)",
        "request_id": r"RequestId:\s*(.+)"
    }

    # Dictionary to store extracted information
    extracted_data = {}

    # Extract each field
    for field, pattern in patterns.items():

        match = re.search(pattern, log_text, re.IGNORECASE)

        if match:
            if match.lastindex:
                extracted_data[field] = match.group(1).strip()
            else:
                extracted_data[field] = match.group(0).strip()
        else:
            extracted_data[field] = None

    # Extract exception type and error message
    exception_match = re.search(
        r"(?m)^([A-Za-z_][\w.]*(?:Error|Exception)):\s*(.+)$",
        log_text
    )

    if exception_match:
        extracted_data["error_type"] = exception_match.group(1)
        extracted_data["error_message"] = exception_match.group(2)
    else:
        extracted_data["error_type"] = None
        extracted_data["error_message"] = None

    # Extract source-code file names and line numbers
    locations = re.findall(
        r'File "([^"]+)", line (\d+)',
        log_text
    )

    extracted_data["code_locations"] = [
        {
            "file": file,
            "line": int(line)
        }
        for file, line in locations
    ]
        # Extract the complete stack trace
    traceback_match = re.search(
        r"(?s)Traceback \(most recent call last\):.*",
        log_text
    )

    if traceback_match:
        extracted_data["stack_trace"] = traceback_match.group(0).strip()
    else:
        extracted_data["stack_trace"] = None

    return extracted_data


# Execute the function
if __name__ == "__main__":

    result = extract_log_details(log_text)

    print(json.dumps(result, indent=4))
