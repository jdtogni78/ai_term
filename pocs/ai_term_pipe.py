#!/usr/bin/env python3

import os
import sys
import signal
import subprocess
import select
import fcntl
import termios
import time
import colorama
import pty
from terminal_agent import TerminalAgent, AgentOutput

CMD_SYMBOL = "⚡"
PROMPT_SYMBOL = "⚘"
verbose = True

class OutputCollector:
    def __init__(self, max_elements=20):
        self.collection = []
        self.max_elements = max_elements
        self.current_type = None
        self.current_content = ""
        self.last_command_id = None

    def add_to_collection(self, type, content):
        if content.strip():
            if (verbose): print(f"DEBUG: Received {type}: {content.strip()}")
            self.collection.append({type: content.strip()})
            # If it's stderr, start a background process to delay and print
            if type == 'stderr':
                content_to_print = content.strip()
                def delayed_print():
                    import time
                    import colorama
                    time.sleep(2)
                    print(f"{colorama.Fore.RED}stderr: {content_to_print}{colorama.Fore.RESET}")
                
                from threading import Thread
                Thread(target=delayed_print, daemon=True).start()

            if len(self.collection) > self.max_elements:
                self.collection.pop(0)

    def get_last_commands(self):
        try:
            result = subprocess.run(['bash', '-c', 'history | tail -n 3'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                # Get the second to last command (ignoring the very last one)
                last_line = lines[-2]
                parts = last_line.split(None, 1)
                if len(parts) == 2:
                    command_id, command = parts
                    return int(command_id), command
            return None, None
        except Exception:
            return None, None

    def process_output(self, type, output):
        # Check if a new command has been entered
        new_command_id, new_command = self.get_last_commands()
        if (verbose): print(f"DEBUG: Last command ID: {self.last_command_id}, New command ID: {new_command_id}")
        if new_command_id and new_command_id != self.last_command_id:
            self.add_to_collection(CMD_SYMBOL, f"{new_command_id}: {new_command}")
            self.last_command_id = new_command_id
            # Reset current content after a new command
            self.current_content = ""
            self.current_type = None

        # Process the output as a stream
        lines = output.splitlines(True)  # Keep the newline characters
        for line in lines:
            if type != self.current_type:
                if self.current_content:
                    self.add_to_collection(self.current_type, self.current_content)
                self.current_type = type
                self.current_content = line
            else:
                self.current_content += line



# Create named pipes for stdout and stderr
stdout_pipe = '/tmp/ai_stdout_pipe'
stderr_pipe = '/tmp/ai_stderr_pipe'

def create_pipe(pipe_path):
    if not os.path.exists(pipe_path):
        os.mkfifo(pipe_path)

def set_non_blocking(fd):
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

def read_pipe(pipe_fd):
    try:
        return os.read(pipe_fd, 4096)
    except BlockingIOError:
        return b''

def create_pipes():
    create_pipe(stdout_pipe)
    create_pipe(stderr_pipe)

    # Open pipes
    stdout_fd = os.open(stdout_pipe, os.O_RDONLY | os.O_NONBLOCK)
    stderr_fd = os.open(stderr_pipe, os.O_RDONLY | os.O_NONBLOCK)

    set_non_blocking(stdout_fd)
    set_non_blocking(stderr_fd)

    print("Pipes created. You can now run commands in another terminal using:")
    print(colorama.Fore.YELLOW + f"exec > {stdout_pipe} 2> {stderr_pipe}" + colorama.Fore.RESET)
    return stdout_fd,stderr_fd

def cleanup_pipes(stdout_fd, stderr_fd):
    print("\nCleaning up pipes...")
    try:
        os.close(stdout_fd)
        os.close(stderr_fd)
        print("Pipes closed and removed successfully.")
    except Exception as e:
        print(f"Error during cleanup: {e}")

def main():
    stdout_fd, stderr_fd = create_pipes()
    # Set up signal handler for graceful shutdown
    def signal_handler(signum, frame):
        print("\nReceived termination signal. Cleaning up...")
        cleanup_pipes(stdout_fd, stderr_fd)
        sys.exit(0)

    # Register the signal handler for SIGINT (Ctrl+C) and SIGTERM
    signal.signal(signal.SIGINT, signal_handler)
    # signal.signal(signal.SIGTERM, signal_handler)

    # Initialize the OutputCollector
    collector = OutputCollector()

    print(colorama.Fore.MAGENTA + "\nAI Terminal started. Listening for output...\n" + colorama.Fore.RESET)
    while True:
        rlist, _, _ = select.select([stdout_fd, stderr_fd], [], [], 0.1)
        
        if stdout_fd in rlist:
            output = read_pipe(stdout_fd)
            # ignore if output is empty
            if not output:
                continue
            sys.stdout.buffer.write(output)
            sys.stdout.buffer.flush()
            output = output.decode('utf-8', errors='replace')
            collector.process_output('stdout', output)
        
        if stderr_fd in rlist:
            output = read_pipe(stderr_fd)
            # ignore if output is empty
            if not output:
                continue
            output = output.decode('utf-8', errors='replace')
            print(colorama.Fore.RED + output + colorama.Fore.RESET)
            collector.process_output('stderr', output)

if __name__ == "__main__":
    main()
