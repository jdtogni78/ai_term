from pydantic import BaseModel
from typing import List

from ai_term.symbols import SYMBOL_CHOICE

verbose = False

class CommandPrediction(BaseModel):
    reasoning: str
    command: str

class CommandPredictions(BaseModel):
    reasoning: str
    commands: List[CommandPrediction]

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
            print("* ", state["predictions"].reasoning)
            for suggestion in state["predictions"].commands:
                print("* Reasoning: ", suggestion.reasoning)
                print("* Command: ", suggestion.command)
                print("***************")
        return state

