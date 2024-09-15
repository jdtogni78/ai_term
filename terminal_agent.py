from colorama import Fore, Back, Style
import colorama
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, create_openai_tools_agent
from langchain.prompts import PromptTemplate, StringPromptTemplate
from langchain_community.chat_models import ChatOllama
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
    return found_keys

# Define your agents
class OutputAnalysisAgent:
    def __init__(self):
        self.prompt = PromptTemplate.from_file("prompt_output_review.md")
        self.llm = ChatOllama(model="llama3.1")
        self.chain = self.prompt | self.llm | StrOutputParser()
        self.color = colorama.Fore.GREEN
        self.ai_color = colorama.Fore.YELLOW

    def analyze(self, state):
        if (verbose): print(self.color + "> analyzing stdout and stderr")
        stdout = state["stdout"]
        stderr = state["stderr"]
        command = state["command"]
        review = self.chain.invoke({
            "stdout": stdout, 
            "stderr": stderr,
            "command": command,
        })
        # sample prediction: **Command:** `cut -d, --complement -f1; cut -d, -f2-4 file.csv`
        # check if the review contains "**Command:** "
        predicted_cmd = ""
        if "<next_command>" in review and "</next_command>" in review:
            # extract the command from the review
            parts1 = review.split("<next_command>")
            parts2 = parts1[1].split("</next_command>")
            predicted_cmd = parts2[0]

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
        self.llm = ChatOllama(model="llama3.1")
        self.chain = self.prompt | self.llm | StrOutputParser()
        self.color = colorama.Fore.GREEN
        self.ai_color = colorama.Fore.YELLOW

    def make_suggestion(self, state):
        # remove the ai_cmd from the command
        command = state["command"]
        if command.startswith(self.ai_cmd + " "):
            command = command[len(self.ai_cmd):]
        if (verbose): print(self.color + "> requesting ai help: ", command)
        # Generate suggestions based on context
        suggestion = self.chain.invoke({"request": command, "scratchpad": state["scratchpad"]})
        # check if the suggestion contains "**Next Command:** "
        predicted_cmd = ""
        cmds = extract_all_xml_from_string(suggestion, "command")
        if len(cmds) > 0:
            predicted_cmd = "\n".join(cmds)

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

    def command_input(self, state: list):
        if (verbose): print(self.color + "> command input")
        command = state["command"]
        stdout = ""
        stderr = ""
        if not command.startswith(self.ai_cmd + " ") and not command == "exit":
            # execute command on terminal
            out = subprocess.run(command, shell=True, capture_output=True, text=True)
            stdout = out.stdout
            stderr = out.stderr
            if (verbose): 
                print(self.color + "# running command: ", command)
                if stdout != "":
                    print(self.stdout_color + "# stdout: ")
                    print(stdout)
                if stderr != "":
                    print(self.stderr_color + "# stderr: ")
                    print(stderr)
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
        self.graph = self.create_graph()
        self.runnable = self.graph.compile()

    def create_graph(self):
        input_command_router = InputCommandRouter(self.ai_cmd)
        review_output = OutputAnalysisAgent()
        suggestion_agent = SuggestionAgent(self.ai_cmd)

        graph = StateGraph(AgentState)
        graph.add_node("command_input", input_command_router.command_input)
        graph.add_node("output_reviewer", review_output.analyze)
        graph.add_node("suggestion_agent", suggestion_agent.make_suggestion)

        # graph.set_entry_point("command")
        graph.add_edge(START, "command_input")
        graph.add_edge("output_reviewer", END)
        graph.add_edge("suggestion_agent", END)

        # conditional edges for input_command_router
        graph.add_conditional_edges(
            "command_input", 
            input_command_router.route, 
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
    command = ""
    verbose = True
    print("Welcome to the AI Terminal")
    # read command from stdin, until user types "exit"
    while command != "exit":
        command = input(colorama.Fore.RESET + "Command: ")
        out = agent.run({"command": command})
        print(colorama.Fore.MAGENTA, out, colorama.Fore.RESET)

