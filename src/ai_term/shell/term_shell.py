#!/usr/bin/env python3

import os
import re
import signal
import sys
import time
import threading

from ai_term.ai.agents.output_analisys import OutputAnalysisAgent
from ai_term.utils.stderr_collector import StderrCollector
from ai_term.symbols import SYMBOL_CMD, SYMBOL_PROMPT, SYMBOL_CHOICE, SYMBOL_QUESTION
from src.ai_term.config import Colors

verbose = False

class TermShell:
    def process_input(self, fifo):
        # will contain [{key : value}, {key : value}, {key : value}]
        max_entries = 20
        collector = StderrCollector(max_entries)
        last_change_time = time.time()
        partial_line = ""
        agent = OutputAnalysisAgent()
        agent.set_stream_callback(lambda x: print(x, end="", flush=True))

        def force_prompt():
            # send a kill signal to the parent process
            os.kill(os.getppid(), signal.SIGWINCH)

        def process_collected_content():
            nonlocal last_change_time, collector
            while True: 
                try:
                    time.sleep(0.5)
                    if collector.collecting and time.time() - last_change_time >= 2:
                        # ignore if no commands were ran, if stderr_lines has not 'cmd' key
                        if not collector.has_key(SYMBOL_CMD): continue
                        collector.stop()
                        call_ai(collector)
                        force_prompt()
                except Exception as e:
                    Colors.print("error", str(e))

        def call_ai(collector):
            if (verbose): print("collected")
            Colors.set_color("ai_output")
            print("\n")
            lines = collector.last_error(-2)
            agent.run(lines)
            Colors.set_color("reset")
            
                
        threading.Thread(target=process_collected_content).start()

        while True:
            try:
                chunk = fifo.read(1)  # Read up to 1024 bytes at a time
                print(chunk, end='', flush=True)

                last_change_time = time.time()
                if chunk == '\n':
                    line = partial_line + chunk

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
                        collector.add()
                        key, value = match.groups()
                        collector.add_other(key, value)
                    else:
                        # ignore empty lines
                        collector.append(line)
                    partial_line = ""
                else:
                    # Partial line, store for later
                    partial_line += chunk
            except Exception as e:
                Colors.print("error", str(e))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fifo = open(sys.argv[1], 'rb')
        TermShell().process_input(fifo)
    else:
        TermShell().process_input(sys.stdin)
