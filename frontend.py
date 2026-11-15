
import streamlit as st
import requests


# 1. Configure the application page
st.set_page_config(
    page_title="AI Incident Investigation Assistant",
    page_icon="🔍",
    layout="wide"
)


# 2. FastAPI backend endpoints
API_URL = "http://127.0.0.1:8000/investigate"

FOLLOW_UP_API_URL = (
    "http://127.0.0.1:8000/investigate/follow-up"
)


# 3. Initialize session state
if "initial_report" not in st.session_state:
    st.session_state.initial_report = None

if "follow_up_history" not in st.session_state:
    st.session_state.follow_up_history = []

if "original_log_text" not in st.session_state:
    st.session_state.original_log_text = ""

if "upload_signature" not in st.session_state:
    st.session_state.upload_signature = None

if "validation_message" not in st.session_state:
    st.session_state.validation_message = None


# 4. Function to display an investigation report
def display_report(report):

    st.subheader("Main Problem")

    st.write(
        report.get("explanation", "Not available")
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Likely Causes")

        for i, cause in enumerate(
            report.get("possible_causes", []),
            start=1
        ):
            st.write(f"{i}. {cause}")

    with col2:
        st.markdown("### Recommended Actions")

        for i, check in enumerate(
            report.get("recommended_checks", []),
            start=1
        ):
            st.write(f"{i}. {check}")

    st.subheader("Uncertainty")

    st.info(
        report.get(
            "uncertainty",
            "No additional information available."
        )
    )

    with st.expander("View Evidence"):
        for item in report.get("evidence", []):
            st.write(f"- {item}")


# 5. Application title
st.title("AI Incident Investigation Assistant")

st.write(
    "Upload your application log files "
    "to investigate errors using Generative AI."
)


# 6. Log file uploader
uploaded_file = st.file_uploader(
    "Upload your application log file",
    type=["log"]
)


if uploaded_file is not None:

    log_bytes = uploaded_file.getvalue()

    current_signature = (
        uploaded_file.name,
        log_bytes
    )

    # Reset previous investigation when a new file is uploaded
    if current_signature != st.session_state.upload_signature:

        st.session_state.upload_signature = current_signature

        st.session_state.initial_report = None
        st.session_state.follow_up_history = []
        st.session_state.original_log_text = ""
        st.session_state.validation_message = None

    # 7. Initial incident investigation
    if st.button("Investigate Incident"):

        with st.spinner("Investigating incident..."):

            try:
                response = requests.post(
                    API_URL,
                    files={
                        "file": (
                            uploaded_file.name,
                            log_bytes,
                            "text/plain"
                        )
                    },
                    timeout=120
                )

                if response.status_code == 200:

                    result = response.json()

                    st.session_state.initial_report = (
                        result["report"]
                    )

                    st.session_state.original_log_text = (
                        log_bytes.decode("utf-8")
                    )

                    st.session_state.follow_up_history = []
                    st.session_state.validation_message = None

                    st.success(
                        "Initial investigation completed successfully!"
                    )

                else:
                    try:
                        error_message = response.json()["detail"]
                    except (ValueError, KeyError):
                        error_message = "Investigation failed."

                    st.error(error_message)

            except requests.exceptions.RequestException as e:
                st.error(
                    f"Unable to connect to backend: {e}"
                )


# 8. Display the investigation workflow
if st.session_state.initial_report is not None:

    st.divider()

    st.header("Initial Investigation")

    st.caption(
        "Original AI-generated investigation report"
    )

    display_report(
        st.session_state.initial_report
    )

    # Get the latest accepted investigation report
    if st.session_state.follow_up_history:

        latest_report = (
            st.session_state.follow_up_history[-1]["report"]
        )

    else:
        latest_report = st.session_state.initial_report


    # 9. Display follow-up questions and answer form
    if latest_report.get("needs_more_information", False):

        st.divider()

        st.header("Additional Information Required")

        st.write(
            "Please provide answers to the following questions "
            "to improve the investigation:"
        )

        for i, question in enumerate(
            latest_report.get("follow_up_questions", []),
            start=1
        ):
            st.write(f"{i}. {question}")

        current_round = len(
            st.session_state.follow_up_history
        )

        with st.form(
            key=f"follow_up_form_{current_round}"
        ):

            additional_information = st.text_area(
                "Enter your answers here",
                placeholder=(
                    "Provide the requested information "
                    "based on your logs and system observations..."
                ),
                height=150
            )

            submit = st.form_submit_button(
                "Submit Additional Information"
            )


        # 10. Process developer's answers
        if submit:

            if not additional_information.strip():

                st.warning(
                    "Please provide answers before submitting."
                )

            else:

                with st.spinner(
                    "AI is validating your response..."
                ):

                    try:

                        response = requests.post(
                            FOLLOW_UP_API_URL,
                            json={
                                "log_text": (
                                    st.session_state.original_log_text
                                ),
                                "additional_information": (
                                    additional_information
                                ),
                                "follow_up_questions": (
                                    latest_report.get(
                                        "follow_up_questions", []
                                    )
                                )
                            },
                            timeout=120
                        )

                        if response.status_code == 200:

                            result = response.json()

                            validation = result.get(
                                "validation", {}
                            )

                            validation_status = validation.get(
                                "status"
                            )

                            if validation_status == "relevant":

                                updated_report = result.get("report")

                                if updated_report is not None:

                                    st.session_state.follow_up_history.append({
                                        "answers": additional_information,
                                        "report": updated_report
                                    })

                                    st.session_state.validation_message = None

                                    st.success(
                                        "Your answers were accepted! "
                                        "The AI investigation has been updated."
                                    )

                                else:
                                    st.error(
                                        "The AI did not return an updated report."
                                    )

                            else:

                                st.session_state.validation_message = (
                                    validation.get(
                                        "response",
                                        "Please provide information relevant "
                                        "to the incident investigation."
                                    )
                                )

                        else:

                            try:
                                error_message = response.json()["detail"]
                            except (ValueError, KeyError):
                                error_message = (
                                    "Follow-up investigation failed."
                                )

                            st.error(error_message)

                    except requests.exceptions.RequestException as e:

                        st.error(
                            f"Unable to connect to backend: {e}"
                        )


    # 11. Display AI validation response BELOW the answer form
    if st.session_state.validation_message:

        st.info(
            st.session_state.validation_message
        )


    # 12. Display updated investigation reports
    for index, item in enumerate(
        st.session_state.follow_up_history,
        start=1
    ):

        st.divider()

        st.success(
            f"Additional information submitted successfully. "
            f"Updated Investigation – Round {index}"
        )

        st.header(
            f"Updated Investigation – Round {index}"
        )

        st.caption(
            "AI-generated analysis using the original log "
            "and the additional information submitted."
        )

        with st.expander(
            "View Developer's Submitted Answers"
        ):
            st.write(item["answers"])

        display_report(
            item["report"]
        )


    # 13. Final status
    if not latest_report.get("needs_more_information", False):

        st.divider()

        st.success(
            "The AI has sufficient information for its current "
            "analysis. No further evidence has been requested."
        )
