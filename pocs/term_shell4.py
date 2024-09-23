#!/usr/bin/env python3

import os
import subprocess
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

def get_bash_path():
    return '/bin/bash'

def create_key_bindings(bash_process):
    kb = KeyBindings()

    @kb.add('c-c')
    def _(event):
        bash_process.terminate()
        event.app.exit()

    @kb.add(Keys.ControlR)
    def _(event):
        event.app.layout.focus(event.app.layout.search_buffer)

    @kb.add(Keys.ControlW)
    def _(event):
        print("ControlW")
        event.current_buffer.delete_before_cursor(count=len(event.current_buffer.document.get_word_before_cursor()))

    @kb.add(Keys.ControlLeft)
    def _(event):
        event.current_buffer.cursor_left(count=len(event.current_buffer.document.get_word_before_cursor()))

    @kb.add(Keys.ControlRight)
    def _(event):
        event.current_buffer.cursor_right(count=len(event.current_buffer.document.get_word_after_cursor()))

    @kb.add(Keys.ControlA)
    def _(event):
        event.current_buffer.cursor_position = 0

    @kb.add(Keys.ControlE)
    def _(event):
        event.current_buffer.cursor_position = len(event.current_buffer.text)

    return kb

def main():
    bash_path = get_bash_path()
    bash_process = subprocess.Popen(
        [bash_path, '-i'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ,
        universal_newlines=True,
        bufsize=0
    )

    # Set up prompt
    bash_process.stdin.write("export PS1='\\[\\033[01;32m\\]\\u@\\h\\[\\033[00m\\]:\\[\\033[01;34m\\]\\w\\[\\033[00m\\]\\$ '\n")
    bash_process.stdin.flush()

    history = InMemoryHistory()
    session = PromptSession(
        history=history,
        auto_suggest=AutoSuggestFromHistory(),
        key_bindings=create_key_bindings(bash_process),
        enable_history_search=True
    )

    while True:
        try:
            user_input = session.prompt('', multiline=False)
            
            if user_input.strip() == 'exit':
                break

            bash_process.stdin.write(user_input + '\n')
            bash_process.stdin.flush()

            while True:
                output = bash_process.stdout.readline()
                if output == '' and bash_process.poll() is not None:
                    break
                if output:
                    print(output.strip())

        except KeyboardInterrupt:
            continue
        except EOFError:
            break

    bash_process.terminate()
    print("\nExiting the emulated terminal.")

if __name__ == "__main__":
    main()
