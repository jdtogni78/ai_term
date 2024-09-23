#!/usr/bin/env python3

import os
import subprocess
import sys
import threading
import time

def get_current_shell():
    return '/bin/bash'
    # return os.environ.get('SHELL', '/bin/sh')

def launch_subshell():
    current_shell = get_current_shell()
    print(f"Launching subshell using: {current_shell}")
    print(f"Current shell: {os.environ.get('PS1')}")

    try:
        class OutputAccumulator:
            def __init__(self, max_lines=10):
                self.stdout = []
                self.stderr = []
                self.max_lines = max_lines

            def add_stdout(self, line):
                self.stdout.append(line)
                if len(self.stdout) > self.max_lines:
                    self.stdout.pop(0)

            def add_stderr(self, line):
                self.stderr.append(line)
                if len(self.stderr) > self.max_lines:
                    self.stderr.pop(0)

        # Launch the subshell, inheriting the current environment
        process = subprocess.Popen([current_shell, '-i'], 
                                   env=os.environ, 
                                   stdin=sys.stdin,
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE,
                                   text=True,
                                   shell=True,
                                   bufsize=1
                                   )
        accumulator = OutputAccumulator()

        def delayed_stderr_collection():
            nonlocal last_stderr_time, process, accumulator
            print(f"Starting delayed_stderr_collection")
            while time.time() - last_stderr_time < 2:
                time.sleep(0.1)
            print(f"Finished delayed_stderr_collection")
            
            # run history inside the subshell
            # cmd = "history\n"
            # stdout, stderr = process.communicate(input=cmd.encode(), timeout=1)
            # print(f"STDOUT: {stdout}")
            # print(f"STDERR: {stderr}")
            
            print(f"\n\033[91mRESPONSE: STDERR: {accumulator.stderr}\033[0m")

        last_stderr_time = 0
        stderr_thread = None

        def stdout_thread():
            while True:
                out = process.stdout.readline()
                if out == '' and process.poll() is not None:
                    break
                if out:
                    if isinstance(out, bytes):
                        out = out.decode()
                    accumulator.add_stdout(out.strip())
                    print(f"\033[92m{out}\033[0m", end='')  # Print stdout in green

        stdout_thread = threading.Thread(target=stdout_thread)
        stdout_thread.daemon = True
        stdout_thread.start()

        while True:
            err = process.stderr.readline()
            if err == '' and process.poll() is not None:
                break
            if err:
                if isinstance(err, bytes):
                    err = err.decode()
                accumulator.add_stderr(err.strip())
                print(f"\033[91m{err}\033[0m", end='')  # Print stderr in red
                last_stderr_time = time.time()
                if stderr_thread is None or not stderr_thread.is_alive():
                    stderr_thread = threading.Thread(target=delayed_stderr_collection)
                    stderr_thread.daemon = True
                    stderr_thread.start()
                    
            if stderr_thread and stderr_thread.is_alive():
                stderr_thread.join(timeout=30)
                print(f"joined thread")

    except KeyboardInterrupt:
        print("\nSubshell terminated.")
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    launch_subshell()
