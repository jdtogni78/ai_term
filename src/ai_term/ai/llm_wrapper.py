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
from ai_term.config import Colors, Config
load_dotenv()

class LLMWrapper:

    def __init__(self, prompt_name, verbose=False):
        self.llm_model = Config.MODEL_NAME
        self.temperature = 0.0

        self.llm_descr = "local ollama" if os.getenv("GROQ_API_KEY") is None else "groq"
        self.prompt_mode = "instructor" if Config.USE_INSTRUCTOR else "raw"
        if (verbose): print("Using", self.llm_descr, 
                            "model:", self.llm_model, 
                            "prompt mode:", self.prompt_mode)

        self.prompt_file = self.get_prompt_file(prompt_name)
        self.prompt = PromptTemplate.from_file(self.prompt_file)
        if Config.USE_INSTRUCTOR:
            self.client = self.create_instructor()
        else:
            self.client = self.create_llm()
        self.chain = self.prompt | self.client | StrOutputParser()

    def create_llm(self):
        if os.getenv("GROQ_API_KEY") is None:
            kwargs = ({'num_predict': Config.MAX_TOKENS} if Config.MAX_TOKENS is not None else {})
            return ChatOllama(
                model=self.llm_model,
                temperature=self.temperature,
                **kwargs,  # Limit output tokens if MAX_TOKENS is set
            )
        else:
            kwargs = ({'max_tokens': Config.MAX_TOKENS} if Config.MAX_TOKENS is not None else {})
            return ChatGroq(    
                model=self.llm_model,
                api_key=os.getenv("GROQ_API_KEY"),
                temperature=self.temperature,
                **kwargs,  # Limit output tokens if MAX_TOKENS is set
            )
        
    # Using instuctor output are parsed and formatted using pydantic
    # But, we lose the streaming feature
    def create_instructor(self):
        kwargs = ({'max_tokens': Config.MAX_TOKENS} if Config.MAX_TOKENS is not None else {})
        if os.getenv("GROQ_API_KEY") is None:
            client = instructor.from_openai(
                OpenAI(base_url="http://localhost:11434/v1", api_key="ollama"),
                mode=instructor.Mode.JSON,
                **kwargs,  # Limit output tokens if MAX_TOKENS is set
            )
            Colors.print("system", "Using instructor with ollama, mode JSON")
        else:
            client = Groq(
                api_key=os.environ.get("GROQ_API_KEY"),
                **kwargs,  # Limit output tokens if MAX_TOKENS is set
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
