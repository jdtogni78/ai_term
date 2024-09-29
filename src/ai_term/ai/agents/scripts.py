from langgraph.graph import END, START, StateGraph
from typing import List, TypedDict, Optional

from pydantic import BaseModel, Field
from ai_term.ai.llm_wrapper import LLMWrapper
from ai_term.symbols import replace_symbols
from ai_term.config import Config, Colors
from ai_term.utils.xml_utils import extract_all_xml
verbose = False

class Script(BaseModel):
    reasoning: Optional[str] = Field(..., description="The step by step reasoning for this script")
    filename: str = Field(..., description="The name of the file to create")
    content: str = Field(..., description="The content of the script")

class Scripts(BaseModel):
    summary: Optional[str] = Field(..., description="The overall summary/reasoning over the request.")
    scripts: List[Script]

class AgentState(TypedDict):
    request: str
    # list of tuples (filename, content)
    scripts: Scripts
    output_review: str

class ScriptAgent:

    def __init__(self):
        self.llm = LLMWrapper("scripts")
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
            Colors.print("system", "* creating script: /tmp/" + script.filename)
            if (verbose):
                Colors.print("system", script.content)
                Colors.print("system", "<<")
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
        if Config.USE_INSTRUCTOR:
            scripts = self.create_scripts_instr(request)
        else:
            scripts = self.create_scripts_raw(request)
        if (verbose): print(scripts)
        print("\n")
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
        return self.parse_scripts(raw_output)

    def parse_scripts(self, raw_output):
        filenames = extract_all_xml("filename", raw_output)
        contents = extract_all_xml("content", raw_output)
        reasonings = extract_all_xml("reasoning", raw_output)
        summary = extract_all_xml("summary", raw_output)
        scrs = []
        for i, (filename, content) in enumerate(zip(filenames, contents)):
            if (i >= len(reasonings)):
                reason = "-"
            else:
                reason = reasonings[i]
            script = Script(filename=filename, content=content, reasoning=reason)
            scrs.append(script)
        return Scripts(summary="".join(summary), scripts=scrs)

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

if __name__ == "__main__":
    agent = ScriptAgent()
    import sys
    if len(sys.argv) != 2:
        print("Usage: python scripts.py <file>")
        sys.exit(1)
    file = sys.argv[1]
    with open(file, "r") as f:
        content = f.read()
    print(agent.parse_scripts(content))
