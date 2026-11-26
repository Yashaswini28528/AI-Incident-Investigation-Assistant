
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from llm_config import llm


# Define the structure of the AI response
class IncidentAnalysis(BaseModel):

    error_type: str = Field(description="Name of the exception")

    explanation: str = Field(description="Simple explanation of the error")

    possible_causes: list[str] = Field(
        description="List of possible reasons for the error"
    )


# Create an output parser
parser = PydanticOutputParser(
    pydantic_object=IncidentAnalysis
)


# Create a prompt template
prompt = ChatPromptTemplate.from_template(
    """
    You are an application incident investigation assistant.

    Analyse this error:

    {error_message}

    Provide a simple explanation and possible causes.

    Do not claim that a possible cause is confirmed.

    {format_instructions}
    """
)


# Connect the prompt, LLM and output parser
chain = prompt | llm | parser


# Execute the chain
response = chain.invoke({
    "error_message": "Database connection timeout",
    "format_instructions": parser.get_format_instructions()
})


# Display structured results
print(response.model_dump())
