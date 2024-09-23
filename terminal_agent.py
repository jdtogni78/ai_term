from colorama import Fore, Back, Style
import colorama
import sys
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, create_openai_tools_agent
from langchain.prompts import PromptTemplate, StringPromptTemplate
from langchain_community.chat_models import ChatOllama
from langchain_groq import ChatGroq
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
import operator
import os
from typing import Annotated, List, Sequence, TypedDict, Union
import subprocess
import re
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import getpass

from pydantic import BaseModel
import instructor
from groq import Groq
from openai import OpenAI
from typing import List

load_dotenv()

verbose = False

from symbols import SYMBOL_CHOICE

def persist_predictions(state):
    for key, value in state.items():
        if verbose: print(" **", key, value)
    if "predicted_commands" in state:
        with open("/tmp/predicted_commands.txt", "w") as f:
            print("")
            for i, cmd in enumerate(state["predicted_commands"]):
                f.write(cmd + "\n")
                print(SYMBOL_CHOICE + " " + str(i+1), cmd)
        print("NOTE: run 'aicmd <number>' to execute the command\n")
    return state

class AgentState(TypedDict):
    command: str
    stdout: str
    stderr: str
    predicted_command: str
    output_review: str
    agent_out: Union[AgentAction, AgentFinish, None]
    scratchpad: Annotated[list[tuple[AgentAction, str]], operator.add]

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

# Define your agents
class OutputAnalysis(BaseModel):
    reasoning: str
    predicted_commands: List[str]

class OutputAnalysisAgent():
    class AgentState(TypedDict):
        terminal_history: list[dict[str, str]]
        output_analysis: OutputAnalysis
        predicted_commands: List[str]
        agent_out: Union[AgentAction, AgentFinish, None]
        scratchpad: Annotated[list[tuple[AgentAction, str]], operator.add]

    def __init__(self):
        self.llm = LLMWrapper("prompt_output_review.md")
        self.color = colorama.Fore.GREEN
        self.ai_color = colorama.Fore.YELLOW
        self.stream_callback = None
        self.command_stream_callback = None
        self.graph = None
        self.runnable = None

    def set_stream_callback(self, callback):
        self.stream_callback = callback

    def set_command_stream_callback(self, callback):
        self.command_stream_callback = callback

    def analyze(self, state):
        if (verbose): print(self.color + "> analyzing stdout and stderr")
        history = state["terminal_history"]
        analisys = self.llm.run_structured(OutputAnalysis, {"terminal_history": history})
        
        for cmd in analisys.predicted_commands:
            if self.command_stream_callback:
                self.command_stream_callback(cmd)

        if (verbose): print(self.ai_color + "review: ", analisys)
        return {
            "output_analysis": analisys.reasoning,
            "predicted_commands": analisys.predicted_commands,
            "scratchpad": [{"output_analysis": analisys}]
        }
    
    def print_output_analysis(self, state):
        print("\nOutput analysis: ", state["output_analysis"])
        return state

    def create_runnable(self):
        graph = StateGraph(self.AgentState)
        
        graph.add_node("output_reviewer", self.analyze)
        graph.add_node("print_output_analysis", self.print_output_analysis)
        graph.add_node("persist_predictions", persist_predictions)
        
        graph.add_edge(START, "output_reviewer")
        graph.add_edge("output_reviewer", "print_output_analysis")
        graph.add_edge("print_output_analysis", "persist_predictions")
        graph.add_edge("persist_predictions", END)
        
        self.graph = graph
        self.runnable = graph.compile()

    def run(self, history):
        if self.runnable is None:
            self.create_runnable()
        return self.runnable.invoke({"terminal_history" : history})

    def get_state(self):
        return self.runnable.get_state()

class Suggestion(BaseModel):
    reasoning: str
    predicted_commands: List[str]

class SuggestionAgent:
    class AgentState(TypedDict):
        request: str
        suggestion: Suggestion
        agent_out: Union[AgentAction, AgentFinish, None]
        predicted_commands: List[str]
        scratchpad: Annotated[list[tuple[AgentAction, str]], operator.add]

    def __init__(self):
        self.llm = LLMWrapper("prompt_suggestion.md")
        self.color = colorama.Fore.GREEN
        self.ai_color = colorama.Fore.YELLOW
        self.stream_callback = None
        self.command_stream_callback = None
        self.graph = None
        self.runnable = None

    def set_stream_callback(self, callback):
        self.stream_callback = callback

    def set_command_stream_callback(self, callback):
        self.command_stream_callback = callback

    def make_suggestion(self, state):
        # remove the ai_cmd from the command
        request = state["request"]
        if (verbose): print(self.color + "> requesting ai help: ", request)
        # Generate suggestions based on context
        suggestion = self.llm.run_structured(Suggestion, {"request": request})

        for cmd in suggestion.predicted_commands:
            if self.command_stream_callback:
                self.command_stream_callback(cmd)

        return {
            "suggestion": suggestion.reasoning,
            "predicted_commands": suggestion.predicted_commands,
            "scratchpad": [{"make_suggestion": suggestion}]
        }
    
    def print_suggestion(self, state):
        print("\nSuggestion: ", state["suggestion"])
        return state

    def create_runnable(self):
        graph = StateGraph(self.AgentState)
        graph.add_node("suggestion_agent", self.make_suggestion)
        graph.add_node("print_suggestion", self.print_suggestion)
        graph.add_node("persist_predictions", persist_predictions)
        
        graph.add_edge(START, "suggestion_agent")
        graph.add_edge("suggestion_agent", "print_suggestion")
        graph.add_edge("print_suggestion", "persist_predictions")
        graph.add_edge("persist_predictions", END)
        
        self.graph = graph
        self.runnable = graph.compile()

    def run(self, request): #output is Suggestion
        if self.runnable is None:
            self.create_runnable()
        return self.runnable.invoke({"request" : request})

    def get_state(self):
        return self.runnable.get_state()


class Script(BaseModel):
    filename: str
    content: str

class Scripts(BaseModel):
    scripts: List[Script]

class ScriptAgent:
    class AgentState(TypedDict):
        request: str
        # list of tuples (filename, content)
        scripts: Scripts
        output_review: str
        agent_out: Union[AgentAction, AgentFinish, None]
        scratchpad: Annotated[list[tuple[AgentAction, str]], operator.add]

    def __init__(self):
        self.llm = LLMWrapper("prompt_scripts.md")
        self.color = colorama.Fore.GREEN
        self.ai_color = colorama.Fore.YELLOW
        self.stream_callback = None
        self.script_stream_callback = None
        self.graph = None
        self.runnable = None
        # Define your desired output structure

    def set_stream_callback(self, callback):
        self.stream_callback = callback

    def set_script_stream_callback(self, callback):
        self.script_stream_callback = callback

    def persist_scripts(self, state):
        for script in state["scripts"].scripts:
            print(">> creating script: ", script.filename)
            print(script.content)
            print("<<")
            if self.script_stream_callback:
                self.script_stream_callback(script.filename, script.content)
            with open("/tmp/" + script.filename, "w") as f:
                f.write(script.content)

        return state

    def create_scripts(self, state):
        """get the command, send to ai to generate a script
        the script is a list of tuples (filename, content)
        return the state with the scripts 
        """
        scripts = self.llm.run_structured(Scripts, {"request": state["request"]})
        if (verbose): print(scripts)
        return {
            "scripts": scripts,
            "scratchpad": [{"create_scripts": scripts}]
        }

    def create_runnable(self):
        graph = StateGraph(self.AgentState)
        graph.add_node("script_agent", self.create_scripts)
        graph.add_node("save_scripts", self.persist_scripts)
        graph.add_edge(START, "script_agent")
        graph.add_edge("script_agent", "save_scripts")
        graph.add_edge("save_scripts", END)
        self.graph = graph
        self.runnable = graph.compile()

    def run(self, request):
        if self.runnable is None:
            self.create_runnable()
        return self.runnable.invoke({"request" : request})

    def get_state(self):
        return self.runnable.get_state()
