import os
import re
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama

import instructor
from openai import OpenAI
from groq import Groq
from dotenv import load_dotenv
from ai_term.symbols import replace_symbols
from ai_term.config import Colors
load_dotenv()

from ai_term.config import Config

class LLMWrapper:

    def __init__(self, prompt_name):
        self.llm_model = self.get_model()
        self.temperature = 0.0

        self.prompt_mode = "instructor" if Config.USE_INSTRUCTOR else "raw"
        self.prompt_file = self.get_prompt_file(prompt_name)
        self.prompt = PromptTemplate.from_file(self.prompt_file)
        
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
            client = instructor.from_openai(
                OpenAI(base_url="http://localhost:11434/v1", api_key="ollama"),
                mode=instructor.Mode.JSON,
            )
            Colors.print("system", "Using instructor with ollama, mode JSON")
        else:
            client = Groq(
                api_key=os.environ.get("GROQ_API_KEY"),
            )

            client = instructor.from_groq(client, mode=instructor.Mode.TOOLS)
            Colors.print("system", "Using instructor with GROQ, mode TOOLS")
        return client

    def stream(self, input):
        return self.chain.stream(input)

    def run_structured(self, response_model, prompt_kwargs):
        prompt = self.prompt.format(**prompt_kwargs)
        prompt = replace_symbols(prompt)
        scripts = self.client.chat.completions.create(
            model=self.llm_model,
            response_model=response_model,
            messages=[{"role": "user", "content": prompt}],
        )
        
        return scripts

    def get_prompt_file(self, name):
        file_map = {
            "instructor": f"prompts/instr_{name}.md",
            "raw": f"prompts/raw_{name}.md",
        }
        file_name = file_map[self.prompt_mode]
        return file_name
