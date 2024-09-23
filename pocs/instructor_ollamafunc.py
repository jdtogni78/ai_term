from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_experimental.llms.ollama_functions import OllamaFunctions
import instructor


model = OllamaFunctions(
    model="llama3.1", 
    keep_alive=-1,
    format="json"
    )

model = model.bind(
    functions=[
        {
            "name": "the person's name",
            "height": "The person's height",
            "hair_color": "The person's hair color",
        }
    ],
)

class Person(BaseModel):
    name: str = Field(description="The person's name", required=True)
    height: float = Field(description="The person's height", required=True)
    hair_color: str = Field(description="The person's hair color")

prompt = PromptTemplate.from_template(
    """Alex is 5 feet tall. 
Claudia is 1 feet taller than Alex and jumps higher than him. 
Claudia is a brunette and Alex is blonde.

Human: {question}
AI: """
)

structured_llm = model.with_structured_output(Person)
chain = prompt | structured_llm

alex = chain.invoke("Describe Alex")
claudia = chain.invoke("Describe Claudia")
