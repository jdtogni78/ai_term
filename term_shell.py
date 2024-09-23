#!/usr/bin/env python3

import os
import re
import signal
import sys
import time
import threading
from collections import deque
from terminal_agent import OutputAnalysisAgent
import colorama

verbose = False
from symbols import SYMBOL_CMD, SYMBOL_PROMPT, SYMBOL_CHOICE, SYMBOL_QUESTION

class StderrBuffer:
    # will contain [{key : value}, {key : value}, {key : value}]
    def __init__(self, max_size=20):
        self.max_size = max_size
        self.array = []
    
    def append(self, key, value):
        # ignore when value or key is empty or empty string
        if not key or not value: return
        if not key.strip() or not value.strip(): return
        self.array.append({key : value})
        # check how many entries for that key, tracking oldest
        # remove oldest if max_size is reached
        found = None
        first = True
        count = 0
        for entry in self.array:
            if entry.get(key) == value:
                count += 1
                if first:
                    first = False
                    found = entry
        if found and count >= self.max_size:
            self.array.remove(found)
        
    def pop(self): return self.array.pop()
    def __str__(self): return str(self.array)
    def __iter__(self): return iter(self.array)
    def __len__(self): return len(self.array)
    def __getitem__(self, index): return self.array[index]

class StderrCollector:
    def __init__(self, max_entries):
        self.collected_content = ""
        self.collecting = False
        self.stderr_lines = StderrBuffer(max_entries)

    def has_key(self, key): return any(line.get(key) for line in self.stderr_lines)
    
    def stop(self):
        self.collecting = False
        self.add()

    def add(self):
        if self.collecting and self.collected_content:
            self.stderr_lines.append("err", self.collected_content)
        self.collected_content = ""

    def append(self, line):
        self.collecting = True
        if (verbose): print("collecting")
        self.collected_content += line

    def add_other(self, key, value):
        if key and value:
            self.stderr_lines.append(key, value)

    def last_error(self, n):
        # get the last err element + all following elements, 
        # plus the previous n-1 elements
        # return a list of entries
        result = []
        found = -1
        for i in range(len(self.stderr_lines)-1, -1, -1):
            # print(i, found, n, found + n, self.stderr_lines[i])
            result.append(self.stderr_lines[i])
            if found == -1 and "err" in self.stderr_lines[i]:
                found = i
            if found != -1 and i <= found + n:
                break
        return result
    

def process_input(fifo):
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
            time.sleep(0.5)
            if collector.collecting and time.time() - last_change_time >= 2:
                # ignore if no commands were ran, if stderr_lines has not 'cmd' key
                if not collector.has_key(SYMBOL_CMD): continue
                collector.stop()
                call_ai(collector)
                force_prompt()

    def call_ai(collector):
        if (verbose): print("collected")
        print("\n" + colorama.Fore.MAGENTA, end="", flush=True) # prompt for ai
        # print(collector.stderr_lines)
        lines = collector.last_error(-2)
        state = agent.run(lines)
        # print(state)
        print("\n" + colorama.Fore.CYAN, end="", flush=True) # prompt for a

        # write the predicted commands a file, /tmp/predicted_commands.txt
        print(colorama.Fore.RESET, end="", flush=True)
        
            
    threading.Thread(target=process_collected_content).start()

    while True:
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
                # print("col", collected_content)
            partial_line = ""
        else:
            # Partial line, store for later
            partial_line += chunk
    

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fifo = open(sys.argv[1], 'rb')

        process_input(fifo)
    else:
        process_input(sys.stdin)
