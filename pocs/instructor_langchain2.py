import instructor
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import OpenAI

# Load Instructor TaskModel
model = TaskModel("gpt2")

# Use LangChain's LLMChain for additional steps
openai_model = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # required, but unused
)

# Example: Generate a task using Instructor
prompt_text = "Translate the following text into French."
task_instruction = model.generate(prompt_text)

# Create a prompt template for LangChain
prompt = PromptTemplate(input_variables=["text"], template="Translate: {text}")

# Chain the instruction from Instructor with LangChain
chain = LLMChain(llm=openai_model, prompt=prompt)

# Example input to the chain
input_text = "Hello, how are you?"
task_output = chain.run(text=input_text)

print("Generated Instruction:", task_instruction)
print("LangChain Output:", task_output)
