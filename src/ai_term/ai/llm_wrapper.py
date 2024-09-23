import os
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama

import instructor
from openai import OpenAI
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class LLMWrapper:
    def __init__(self, prompt_file):
        self.llm_model = self.get_model()
        self.temperature = 0.0
        self.prompt_file = prompt_file
        self.prompt = PromptTemplate.from_file(prompt_file)
        self.chain = self.prompt | self.create_llm() | StrOutputParser()
        self.client = self.create_instructor()

    def create_llm(self):
        if os.getenv("GROQ_API_KEY") is None:
            return ChatOllama(
                model=self.get_model(),
                temperature=self.temperature,
            )
        else:
            return ChatGroq(    
                model=self.get_model(),
                api_key=os.getenv("GROQ_API_KEY"),
                temperature=self.temperature,
            )

    def get_model(self):
        if os.getenv("GROQ_API_KEY") is None:
            return "llama3.1"
        else:
            return "llama-3.1-70b-versatile"

    # Using instuctor output are parsed and formatted using pydantic
    # But, we lose the streaming feature
    def create_instructor(self):
        if os.getenv("GROQ_API_KEY") is None:
            client = instructor.from_openai(OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama",  # required, but unused
            ))
        else:
            client = Groq(
                api_key=os.environ.get("GROQ_API_KEY"),
            )

            client = instructor.from_groq(client, mode=instructor.Mode.TOOLS)
        return client

    def stream(self, input):
        return self.chain.stream(input)

    def run_structured(self, response_model, prompt_kwargs):
        prompt = self.prompt.format(**prompt_kwargs)
        scripts = self.client.chat.completions.create(
            model=self.llm_model,
            response_model=response_model,
            messages=[{"role": "user", "content": prompt}],
        )
        
        return scripts

