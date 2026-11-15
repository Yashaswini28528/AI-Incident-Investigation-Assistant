
from langchain.agents import create_agent

from llm_config import llm
from source_tools import read_source_code


# 1. Create the AI agent
source_agent = create_agent(

    # Use our existing Groq model
    model=llm,

    # Give the agent access to our source-code tool
    tools=[read_source_code],

    # Explain the agent's responsibilities
    

system_prompt = """
You are an AI software incident investigation assistant.

You have access to a tool called read_source_code.

IMPORTANT TOOL USAGE RULES:

1. When the incident context contains source-code file paths,
   you MUST call read_source_code for those paths.

2. Use the exact relative file paths provided.
   For example: app/database.py

3. Inspect every provided file that is available.
   Do not stop after inspecting the first file.

4. If a file is unavailable, report that it could not be found.
   Continue inspecting the remaining files.

5. Never invent source-code content.

6. Clearly distinguish:
   - What the source code actually contains.
   - What the code might indicate about the incident.
   - What additional evidence is still required.

7. Do not claim that a source-code observation is the
   confirmed root cause without supporting evidence.

8. If the code does not establish the cause, explain
   what additional information is needed.

Return a clear and concise source-code investigation report.

IMPORTANT:
- Include the exact function names found in the inspected files.
- Include the actual code behavior observed.
- Never invent function names such as get_connection()
  unless that function exists in the inspected source.
- If a requested function is not present, explicitly say so.
"""

)

# Reusable function for source-code investigation
def inspect_source_code(incident_context: str) -> str:

    result = source_agent.invoke({
        "messages": [
            {"role": "user", "content": incident_context}
        ]
    })

    # Print the complete agent conversation for debugging
    print("\n===== SOURCE AGENT DEBUG =====")

    for message in result["messages"]:
        print("\nMessage Type:", type(message).__name__)
        print("Message Content:", message.content)

        if hasattr(message, "tool_calls"):
            print("Tool Calls:", message.tool_calls)

    print("==============================\n")

    return result["messages"][-1].content



# 2. Test the agent independently

if __name__ == "__main__":

    incident_context = """
    Service: OrderService
    Error Type: TimeoutException
    Error Message: Database connection timeout
    Code Location: app/database.py

    Investigate this incident using source code
    if additional inspection is useful.
    """

    report = inspect_source_code(incident_context)

    print("\n===== SOURCE CODE INVESTIGATION =====\n")
    print(report)
