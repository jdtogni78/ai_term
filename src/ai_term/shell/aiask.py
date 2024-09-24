#!/usr/bin/env python3

import sys
from ai_term.ai.agents.suggestions import SuggestionAgent
import colorama

def main(args):
    # Initialize the SuggestionAgent
    agent = SuggestionAgent()
    agent.set_stream_callback(lambda x: print(x, end="", flush=True))

    # Get all command-line arguments except the script name
    user_input = " ".join(args)

    # If no arguments were provided, prompt the user for input
    if not user_input:
        user_input = input("aiask: ")


    print(colorama.Fore.MAGENTA, end="", flush=True)
    # Make a suggestion based on the input
    response = agent.run(user_input)

    # Print the suggestion
    print(colorama.Fore.RESET, end="", flush=True)

if __name__ == "__main__":
    main(sys.argv[1:])
