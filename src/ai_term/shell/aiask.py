#!/usr/bin/env python3

import sys
from ai_term.ai.agents.suggestions import SuggestionAgent
from src.ai_term.config import Colors, Config

def main(args):
    # Initialize the SuggestionAgent
    agent = SuggestionAgent()
    if Config.PRINT_STREAM: 
        agent.set_stream_callback(lambda x: print(x, end="", flush=True))

    # Get all command-line arguments except the script name
    user_input = " ".join(args)

    # If no arguments were provided, prompt the user for input
    if not user_input:
        user_input = input("aiask: ")

    Colors.set_color("ai_output")
    response = agent.run(user_input)
    Colors.set_color("reset")

if __name__ == "__main__":
    main(sys.argv[1:])
