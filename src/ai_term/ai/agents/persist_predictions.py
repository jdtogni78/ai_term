import re
from pydantic import BaseModel, Field
from typing import List, Optional
import colorama
from ai_term.symbols import SYMBOL_CHOICE

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
                print("")
                for i, cmd in enumerate(state["predictions"].commands):
                    f.write(cmd.command + "\n")
                    print(SYMBOL_CHOICE + " " + str(i+1), cmd.command)
            print("NOTE: run 'aicmd <number>' to execute the command\n")
        return state

    @staticmethod
    def print_predictions(state):
        if "predictions" in state:
            print("\nSuggestions:")
            print("* ", state["predictions"].summary)
            for suggestion in state["predictions"].commands:
                print("* Reasoning: ", suggestion.reasoning)
                print("* Command: ", suggestion.command)
                print("***************")
        return state

    @staticmethod
    def parse(raw_output):
        commands = []
        summary = "".join(CommandPredictions.extract_all_xml("summary", raw_output))
        cmds = CommandPredictions.extract_all_xml("command", raw_output)
        reasonings = CommandPredictions.extract_all_xml("reasoning", raw_output)
        
        for cmd, reason in zip(cmds, reasonings):
            if cmd is None or reason is None:
                print(colorama.Fore.YELLOW + "WARNING: cmd or reason is None - the model may not have created the output correctly")
                print("* cmd: ", cmd)
                print("* reason: ", reason)
                print("* raw_output: ", raw_output, colorama.Fore.RESET)
                break
            cp = CommandPrediction(reasoning=reason, command=cmd)
            commands.append(cp)
        
        return CommandPredictions(summary=summary, commands=commands)
    
    @staticmethod
    def extract_all_xml(xml_tag, raw_output):
        # Find all XML tags of the form <xml_tag>...</xml_tag> in the raw output
        # Capture the content between the tags, including multi-line content
        pattern = re.compile(f'<{re.escape(xml_tag)}>(.*?)</{re.escape(xml_tag)}>', re.DOTALL)
        matches = pattern.findall(raw_output)
        return matches

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