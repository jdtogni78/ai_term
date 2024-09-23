from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List

import instructor


# Define your desired output structure
class UserInfo(BaseModel):
    name: str
    age: int


# Patch the OpenAI client
client = instructor.from_openai(OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # required, but unused
))

# Extract structured data from natural language
user_info = client.chat.completions.create(
    model="llama3.1",
    response_model=UserInfo,
    messages=[{"role": "user", "content": "John Doe is 30 years old."}],
)

print(user_info.name)
print(user_info.age)

##### Sample 2

class Character(BaseModel):
    name: str
    age: int
    fact: List[str] = Field(..., description="A list of facts about the character")


# enables `response_model` in create call
client = instructor.from_openai(
    OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",  # required, but unused
    ),
    mode=instructor.Mode.JSON,
)

resp = client.chat.completions.create(
    model="llama3.1",
    messages=[
        {
            "role": "user",
            "content": "Tell me about the Harry Potter",
        }
    ],
    response_model=Character,
)
print(resp.model_dump_json(indent=2))
# """
# {
#   "name": "Harry James Potter",
#   "age": 37,
#   "fact": [
#     "He is the chosen one.",
#     "He has a lightning-shaped scar on his forehead.",
#     "He is the son of James and Lily Potter.",
#     "He attended Hogwarts School of Witchcraft and Wizardry.",
#     "He is a skilled wizard and sorcerer.",
#     "He fought against Lord Voldemort and his followers.",
#     "He has a pet owl named Snowy."
#   ]
# }
# """