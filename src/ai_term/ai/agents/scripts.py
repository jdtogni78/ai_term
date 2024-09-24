import colorama
from langgraph.graph import END, START, StateGraph
from typing import List, TypedDict, Optional
from dotenv import load_dotenv

from pydantic import BaseModel, Field
from ai_term.ai.llm_wrapper import LLMWrapper
from ai_term.symbols import replace_symbols

load_dotenv()

verbose = False

class Script(BaseModel):
    reasoning: Optional[str] = Field(..., description="The step by step reasoning for this script")
    filename: str = Field(..., description="The name of the file to create")
    content: str = Field(..., description="The content of the script")

class Scripts(BaseModel):
    reasoning: Optional[str] = Field(..., description="The overall reasoning over the request.")
    scripts: List[Script]

class AgentState(TypedDict):
    request: str
    # list of tuples (filename, content)
    scripts: Scripts
    output_review: str

class ScriptAgent:

    def __init__(self):
        self.llm = LLMWrapper("scripts")
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
        request = state["request"]
        if LLMWrapper.USE_INSTRUCTOR:
            scripts = self.create_scripts_instr(request)
        else:
            scripts = self.create_scripts_raw(request)
        if (verbose): print(scripts)
        return {
            "scripts": scripts,
        }

    def create_scripts_instr(self, request):
        return self.llm.run_structured(Scripts, {"request": request})

    def create_scripts_raw(self, request):
        raw_output = ""
        request = replace_symbols(str(request))
        for line in self.llm.stream({"request": request}):
            if self.stream_callback:
                self.stream_callback(line)
            raw_output += line
        scripts = Scripts.parse(raw_output)
        return scripts

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
