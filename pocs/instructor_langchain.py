from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
# from langchain.chat_models import ChatOpenAI
# from langchain_community.chat_models import ChatOllama
# import ollama
# from langchain_ollama import ChatOllama
from openai import OpenAI


from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
import instructor
import os
from langchain_core.output_parsers import StrOutputParser



# Set your OpenAI API key
# os.environ["OPENAI_API_KEY"] = "your-api-key-here"

# Define the output structure
class ProgrammingLanguage(BaseModel):
    name: str = Field(description="Name of the programming language")
    paradigm: str = Field(description="Primary programming paradigm of the language")
    year_created: int = Field(description="Year the language was created")
    key_features: List[str] = Field(description="List of key features of the language")

# Create a parser
parser = PydanticOutputParser(pydantic_object=ProgrammingLanguage)

# Create a prompt template
template = """
Provide information about the following programming language: {language}

{format_instructions}

Language Information:
"""

prompt = PromptTemplate(
    template=template,
    input_variables=["language"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)


# Patch the OpenAI client
llm = instructor.from_openai(OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # required, but unused
))

# Create a chain
chain = (prompt | llm | StrOutputParser())

def get_language_info(language_name: str) -> ProgrammingLanguage:
    # Run the chain
    output = chain.run(language=language_name)
    
    # Parse the output
    return parser.parse(output)

# Example usage
if __name__ == "__main__":
    languages = ["Python", "JavaScript", "Rust"]
    
    for lang in languages:
        info = get_language_info(lang)
        print(f"\nInformation about {lang}:")
        print(f"Name: {info.name}")
        print(f"Paradigm: {info.paradigm}")
        print
