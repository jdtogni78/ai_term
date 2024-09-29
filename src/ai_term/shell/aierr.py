import json
import sys

from ai_term.utils.stderr_buffer import StderrBuffer
from ai_term.ai.agents.output_analisys import OutputAnalysisAgent
from ai_term.config import Colors, Config

class AIErr:
    def __init__(self):
        self.stderr_buffer = StderrBuffer()

    def prepare_groups(self):
        self.stderr_buffer.load()

        with open('/tmp/stderr_buffer.json', 'r') as f:
            errors = [json.loads(line) for line in f]
    
        groups = self.stderr_buffer.get_groups()
        groups = groups[-5:]  # Keep only the last 5 groups
        groups.reverse()
        groups = groups[1:] # remove 1st group as its aierr command
        return groups
    
    def select_group(self, groups):
        """
        Show a numbered list of errors for each line in /tmp/stderr_buffer.json
        """
        for i, group in enumerate(groups, 1):
            print(f"{i})")
            for line in group:
                print(f"  {line}")

        # read a number from stdin and show the error
        try:
            num = int(input("Which collection to send? "))
            if num == 0:
                return None
            return groups[num-1]
        except (ValueError, IndexError):
            print("Invalid input")

    def call_ai_agent(self, error):
        agent = OutputAnalysisAgent()
        if Config.PRINT_STREAM: 
            agent.set_stream_callback(lambda x: print(x, end="", flush=True))

        Colors.set_color("ai_output")
        response = agent.run(error)
        Colors.set_color("reset")

    def main(self, args):
        if len(args) > 1:
            print("Usage: aierr <error_number>")
            return
        selected = None
        if len(args) == 1 and args[0].isdigit():
            groups = self.prepare_groups()
            selected = groups[int(args[0])-1]
        else:
            groups = self.prepare_groups()
            selected = self.select_group(groups)
        if selected:
            self.call_ai_agent(selected)
        else:
            print("No error selected")

if __name__ == "__main__":
    AIErr().main(sys.argv[1:])
