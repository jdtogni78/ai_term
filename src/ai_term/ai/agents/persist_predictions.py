import re
from pydantic import BaseModel, Field
from typing import List, Optional
from ai_term.symbols import SYMBOL_CHOICE
from ai_term.config import Colors
from ai_term.utils.xml_utils import extract_all_xml

verbose = False

class CommandPrediction(BaseModel):
    reasoning: Optional[str] = Field(..., description="The step by step reasoning for this command")
    command: str = Field(..., description="The predicted/suggested command")

class CommandPredictions(BaseModel):
    summary: Optional[str] = Field(..., description="The summary, or overall reasoning for the commands")
    commands: List[CommandPrediction] = Field(..., description="A list of commands and their reasoning")

    @staticmethod
    def persist_predictions(state):
        for key, value in state.items():
            if verbose: print(" **", key, value)
        if "predictions" in state:
            with open("/tmp/predicted_commands.txt", "w") as f:
                Colors.print("system", "")
                for i, cmd in enumerate(state["predictions"].commands):
                    f.write(cmd.command + "\n")
                    Colors.print("system", SYMBOL_CHOICE, str(i+1), cmd.command)
            Colors.print("system", "NOTE: run 'aicmd <number>' to execute the command\n")
        return state

    @staticmethod
    def print_predictions(state):
        if "predictions" in state:
            print("\n\n")
            # Colors.print("system", "Suggestions:")
            # Colors.print("system", "* ",state["predictions"].summary)
            for suggestion in state["predictions"].commands:
                Colors.print("system", "* Reasoning: ", suggestion.reasoning)
                Colors.print("system", "* Command: ", suggestion.command)
                Colors.print("system", "***************")
        return state

    @staticmethod
    def parse(raw_output):
        commands = []
        summary = "".join(extract_all_xml("summary", raw_output))
        cmds = extract_all_xml("command", raw_output)
        reasonings = extract_all_xml("reasoning", raw_output)
        
        for cmd, reason in zip(cmds, reasonings):
            if cmd is None or reason is None:
                Colors.print("warning", "WARNING: cmd or reason is None - the model may not have created the output correctly")
                Colors.print("warning", "* cmd: ", cmd)
                Colors.print("warning", "* reason: ", reason)
                Colors.print("warning", "* raw_output: ", raw_output)
                break
            cp = CommandPrediction(reasoning=reason, command=cmd)
            commands.append(cp)
        
        return CommandPredictions(summary=summary, commands=commands)
    
if __name__ == "__main__":
    # test creating a CommandPredictions object
    raw_output = """
    <summary>The command was not successful in listing the contents of the current directory.</summary>
    <reasoning>You may find the correct file by running "ls -l" in the parent directory.</reasoning>
    <command>ls -l</command>
    <reasoning>Double check the directory you are in.</reasoning>
    <command>pwd</command>
    """
    predictions = CommandPredictions.parse(raw_output)
    print(predictions)