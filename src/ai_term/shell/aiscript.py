#!/usr/bin/env python3

import sys
import colorama
from ai_term.ai.agents.scripts import ScriptAgent
from ai_term.config import Colors, Config

def main(args):
    # Initialize the SuggestionAgent
    agent = ScriptAgent()
    if Config.PRINT_STREAM: 
        agent.set_stream_callback(lambda x: print(x, end="", flush=True))
    
    # Get all command-line arguments except the script name
    user_input = " ".join(args)
    if user_input == "":
        user_input = input("askai: ")

    # If no arguments were provided, prompt the user for input
    if not user_input:
        user_input = input("askai: ")

    Colors.set_color("ai_output")
    response = agent.run(user_input)
    Colors.set_color("reset")

if __name__ == "__main__":
    main(sys.argv[1:])
