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

load_dotenv()

verbose = False

class AgentState(TypedDict):
    command: str
    stdout: str
    stderr: str
    predicted_command: str
    output_review: str
    agent_out: Union[AgentAction, AgentFinish, None]
    scratchpad: Annotated[list[tuple[AgentAction, str]], operator.add]

def extract_all_xml_from_string(s, key): 
    # Find all occurrences of <key>value</key> in the string (the string is NOT a proper xml)
    # find all <key> 
    found_keys = re.findall(r'<' + key+'>([^<]+)</' + key + '>', s)
    if len(found_keys) > 0:
        return "\n".join(found_keys)
    else:
        return ""

def create_llm():
    if os.getenv("GROQ_API_KEY") is None:
        return ChatOllama(
            model="llama3.1",
            temperature=0.0,
        )
    else:
        return ChatGroq(    
            model="llama-3.1-70b-versatile",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.0,
        )

# Define your agents
class OutputAnalysisAgent:
    def __init__(self):
        self.prompt = PromptTemplate.from_file("prompt_output_review.md")
        self.llm = create_llm()
        self.chain = self.prompt | self.llm | StrOutputParser()
        self.color = colorama.Fore.GREEN
        self.ai_color = colorama.Fore.YELLOW
        self.stream_callback = None
        self.command_stream_callback = None

    def set_stream_callback(self, callback):
        self.stream_callback = callback

    def set_command_stream_callback(self, callback):
        self.command_stream_callback = callback

    def analyze(self, state):
        if (verbose): print(self.color + "> analyzing stdout and stderr")
        stdout = state["stdout"]
        stderr = state["stderr"]
        command = state["command"]
        review = ""
        for step in self.chain.stream({
            "stdout": stdout, 
            "stderr": stderr,
            "command": command,
        }):
            review += step
            if self.stream_callback:
                self.stream_callback(step)
        # sample prediction: **Command:** `cut -d, --complement -f1; cut -d, -f2-4 file.csv`
        # check if the review contains "**Command:** "
        predicted_cmd = extract_all_xml_from_string(review, "next_command")
        if self.command_stream_callback:
            self.command_stream_callback(predicted_cmd)

        if (verbose): print(self.ai_color + "review: ", review)
        if (verbose): print(self.ai_color + "predicted_cmd: ", predicted_cmd)
        return {
            "output_review": review,
            "predicted_command": predicted_cmd,
            "scratchpad": [{"review": review, "predicted_command": predicted_cmd}]
        }

class SuggestionAgent:
    def __init__(self, ai_cmd):
        self.ai_cmd = ai_cmd
        self.prompt = PromptTemplate.from_file("prompt_suggestion.md")
        self.llm = create_llm()
        self.chain = self.prompt | self.llm | StrOutputParser()
        self.color = colorama.Fore.GREEN
        self.ai_color = colorama.Fore.YELLOW
        self.stream_callback = None
        self.command_stream_callback = None

    def set_stream_callback(self, callback):
        self.stream_callback = callback

    def set_command_stream_callback(self, callback):
        self.command_stream_callback = callback

    def make_suggestion(self, state):
        # remove the ai_cmd from the command
        command = state["command"]
        if command.startswith(self.ai_cmd + " "):
            command = command[len(self.ai_cmd):]
        if (verbose): print(self.color + "> requesting ai help: ", command)
        # Generate suggestions based on context
        suggestion = ""
        
        # stream, if needed, the output of the chain
        for step in self.chain.stream({"request": command, "scratchpad": state["scratchpad"]}):
            suggestion += step
            if self.stream_callback:
                self.stream_callback(step)
        # check if the suggestion contains "**Next Command:** "
        predicted_cmd = extract_all_xml_from_string(suggestion, "command")
        if self.command_stream_callback:
            self.command_stream_callback(predicted_cmd)

        if (verbose): print(self.ai_color + "suggestion: ", suggestion)
        if (verbose): print(self.ai_color + "predicted_cmd: ", predicted_cmd)
        return {
            "predicted_command": predicted_cmd,
            "output_review": suggestion,
            "scratchpad": [{"make_suggestion": suggestion, "predicted_command": predicted_cmd}]
        }

class InputCommandRouter:
    def __init__(self, ai_cmd):
        self.ai_cmd = ai_cmd
        self.color = colorama.Fore.BLUE
        self.stdout_color = colorama.Fore.WHITE
        self.stderr_color = colorama.Fore.RED
        self.stream_callback_stdout = None
        self.stream_callback_stderr = None

    def set_stream_callback_stdout(self, callback):
        self.stream_callback_stdout = callback

    def set_stream_callback_stderr(self, callback):
        self.stream_callback_stderr = callback

    def run_command(self, command):
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        stdout = ""
        stderr = ""
        if (verbose): 
            print(self.color + "# run command: ", command)
        while True:
            output = process.stdout.readline()
            error = process.stderr.readline()
            if (verbose):
                if output:
                    print(self.stdout_color + output, file=sys.stdout)
                if error:
                    # print to stderr
                    print(self.stderr_color + error, file=sys.stderr)

            if output:
                stdout += output
                if self.stream_callback_stdout:
                    self.stream_callback_stdout(output)
            if error:
                stderr += error
                if self.stream_callback_stderr:
                    self.stream_callback_stderr(error)

            if process.poll() is not None and not output and not error:
                break
        return stdout, stderr

    def command_input(self, state: list):
        if (verbose): print(self.color + "> command input")
        command = state["command"]
        stdout = ""
        stderr = ""
        if not command.startswith(self.ai_cmd + " ") and not command == "exit":
            # execute command on terminal
            stdout, stderr = self.run_command(command)
                
        return {
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "scratchpad": [{
                "command": command, 
                "stdout": stdout, 
                "stderr": stderr
            }]
        }
    
    def route(self, state: list):
        if (verbose): print(self.color + "> routing command:", state["command"])
        """Routes commands to the appropriate agent.
        * "<ai_cmd> <query>", store <query> in state, return self.ai_cmd
        * "exit", return "exit"
        """
        if state["command"] == "exit":
            return "exit"
        elif state["command"].startswith(self.ai_cmd + " "):
            return self.ai_cmd
        else:
            if state["stderr"] == "":
                return "exit"
            else:
                return "review_output"

class TerminalAgent:
    def __init__(self, ai_cmd="askai"):
        self.ai_cmd = ai_cmd
        self.input_command_router = InputCommandRouter(self.ai_cmd)
        self.output_reviewer = OutputAnalysisAgent()
        self.suggestion_agent = SuggestionAgent(self.ai_cmd)
        self.graph = self.create_graph()
        self.runnable = self.graph.compile()

    def set_ai_stream_callback(self, callback):
        self.suggestion_agent.set_stream_callback(callback)
        self.output_reviewer.set_stream_callback(callback)

    def set_strout_stream_callback(self, callback):
        self.input_command_router.set_stream_callback_stdout(callback)

    def set_stderr_stream_callback(self, callback):
        self.input_command_router.set_stream_callback_stderr(callback)

    def set_command_stream_callback(self, callback):
        self.suggestion_agent.set_command_stream_callback(callback)
        self.output_reviewer.set_command_stream_callback(callback)

    def create_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("command_input", self.input_command_router.command_input)
        graph.add_node("output_reviewer", self.output_reviewer.analyze)
        graph.add_node("suggestion_agent", self.suggestion_agent.make_suggestion)

        # graph.set_entry_point("command")
        graph.add_edge(START, "command_input")
        graph.add_edge("output_reviewer", END)
        graph.add_edge("suggestion_agent", END)

        # conditional edges for input_command_router
        graph.add_conditional_edges(
            "command_input", 
            self.input_command_router.route, 
            {
                self.ai_cmd: "suggestion_agent",
                "review_output": "output_reviewer",
                "unknown_command": END,
                "exit": END
            }
        )
        return graph

    def run(self, command):
        if (verbose): print("> running command: ", command)
        return self.runnable.invoke(command)


if __name__ == "__main__":
    agent = TerminalAgent("askai")
    
    ai_output = ""
    def ai_stream_callback(x):
        global ai_output
        if "\n" in x or len(ai_output) > 100:
            ai_output += x
            print(colorama.Fore.MAGENTA, ai_output.strip())
            ai_output = ""
        else:
            ai_output += x

    agent.set_ai_stream_callback(ai_stream_callback)
    agent.set_strout_stream_callback(lambda x: print(colorama.Fore.YELLOW + "stdout: ", x.strip()))
    agent.set_stderr_stream_callback(lambda x: print(colorama.Fore.RED + "stderr: ", x.strip()))
    agent.set_command_stream_callback(lambda x: print(colorama.Fore.GREEN + "command: ", x.strip()))
    command = ""
    # verbose = True
    print("Welcome to the AI Terminal")
    # read command from stdin, until user types "exit"
    while command != "exit":
        command = input(colorama.Fore.RESET + "Command: ")
        out = agent.run({"command": command})
        print(colorama.Fore.CYAN, out, colorama.Fore.RESET)

