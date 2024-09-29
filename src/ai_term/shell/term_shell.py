#!/usr/bin/env python3

import os
import re
import signal
import socket
import sys
import time
import threading

from ai_term.ai.agents.output_analisys import OutputAnalysisAgent
from ai_term.utils.stderr_collector import StderrCollector
from ai_term.symbols import SYMBOL_CMD, SYMBOL_PROMPT, SYMBOL_CHOICE, SYMBOL_QUESTION
from ai_term.config import Colors, Config

verbose = False

class TermShell:

    def __init__(self):
        self.max_entries = 20
        self.collector = StderrCollector(self.max_entries)
        self.last_change_time = time.time()
        self.partial_line = ""
        self.agent = OutputAnalysisAgent(verbose=True)
        self.ai_thread = None

    def force_prompt(self):
        # send a kill signal to the parent process
        os.kill(os.getppid(), signal.SIGWINCH)

    def process_collected_content(self):
        while True: 
            try:
                time.sleep(0.5)
                if self.collector.collecting and time.time() - self.last_change_time >= 2:
                    # ignore if no commands were ran, if stderr_lines has not 'cmd' key
                    if not self.collector.has_key(SYMBOL_CMD): continue
                    self.collector.stop()
                    if Config.AUTO_SUGGESTIONS:
                        self.call_ai(self.collector.last_error(-2))
                        
            except Exception as e:
                Colors.print("error", str(e))

    def call_ai(self, lines):
        if (verbose): print("collected")
        Colors.set_color("ai_output")
        print("\n")

        if Config.PRINT_STREAM:
            self.agent.set_stream_callback(lambda x: print(x, end="", flush=True))
        else:
            self.agent.set_stream_callback(None)
            
        self.agent.run(lines)
        Colors.set_color("reset")
        self.force_prompt()
            
    def process_input(self, fifo):
        # will contain [{key : value}, {key : value}, {key : value}]

        self.ai_thread = threading.Thread(target=self.process_collected_content).start()

        show_aierr = False
        while True:
            try:
                chunk = fifo.read(1)  # Read up to 1024 bytes at a time
                print(chunk, end='', flush=True)

                self.last_change_time = time.time()
                if chunk == '\n':
                    line = self.partial_line + chunk

                    # Process complete line
                    # Remove color escape sequences
                    line = re.sub(r'\x1b\[[0-9?;]*[hmK]', '', line)
                    # using <|cmd|>, <|prompt|> : 
                    # match = re.match(r"<\|(.+?)\|>(.+)", line)
                    # using unicode characters to match the symbols
                    match = re.match(r"^(" + SYMBOL_PROMPT + 
                                    r"|" + SYMBOL_CMD + 
                                    r"|" + SYMBOL_CHOICE + 
                                    r"|" + SYMBOL_QUESTION + 
                                    r")(.*)", line)
                    if match:
                        self.collector.add()
                        key, value = match.groups()
                        self.collector.add_other(key, value)
                    else:
                        # ignore empty lines
                        self.collector.append(line)
                    self.partial_line = ""
                else:
                    # Partial line, store for later
                    self.partial_line += chunk
            except Exception as e:
                Colors.print("error", str(e))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fifo = open(sys.argv[1], 'rb')
        TermShell().process_input(fifo)
    else:
        TermShell().process_input(sys.stdin)
