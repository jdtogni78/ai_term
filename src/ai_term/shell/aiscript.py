#!/usr/bin/env python3

import sys
import colorama
from ai_term.ai.agents.scripts import ScriptAgent

def main(args):
    # Initialize the SuggestionAgent
    agent = ScriptAgent()
    agent.set_stream_callback(lambda x: print(x, end="", flush=True))
    
    # Get all command-line arguments except the script name
    user_input = " ".join(args)
    if user_input == "":
        user_input = input("askai: ")

    # If no arguments were provided, prompt the user for input
    if not user_input:
        user_input = input("askai: ")

    print(colorama.Fore.MAGENTA, end="", flush=True)
    # Make a suggestion based on the input
    response = agent.run(user_input)
    
    # Print the suggestion
    print(colorama.Fore.RESET, end="", flush=True)

if __name__ == "__main__":
    main(sys.argv[1:])
