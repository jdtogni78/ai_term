import colorama
from langgraph.graph import AgentAction, AgentFinish
from langgraph.graph import END, START, StateGraph
import operator
from typing import Annotated, List, TypedDict, Union
from dotenv import load_dotenv
from pydantic import BaseModel

from ai_term.ai.llm_wrapper import LLMWrapper

load_dotenv()

verbose = False

class Script(BaseModel):
    filename: str
    content: str

class Scripts(BaseModel):
    scripts: List[Script]

class AgentState(TypedDict):
    request: str
    # list of tuples (filename, content)
    scripts: Scripts

class ScriptAgent:

    def __init__(self):
        self.llm = LLMWrapper("prompts/prompt_scripts.md")
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
        graph = StateGraph(AgentState)
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
