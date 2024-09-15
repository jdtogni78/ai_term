from prompt_toolkit import Application
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window, FormattedTextControl
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.containers import WindowAlign
from terminal_agent import TerminalAgent
import asyncio
import time
import threading

agent = TerminalAgent("askai")

def splash(output_field):
    output_field.text = "Welcome to the AI Terminal"

def run_command(app, output_field, aicmd, command):
    if command.startswith("aicmd"):
        if len(command.split(" ")) > 1:
            pos = int(command.split(" ")[1]) + 1
            command = aicmd.split("\n")[pos]
        else:
            command = aicmd
        output_field.text += f"> {command}\n"
    # run agent on background thread

    global stop_threads
    stop_threads = False
    def show_progress():
        # print a . every second
        global stop_threads
        while True:
            output_field.text += "."
            time.sleep(1)
            if stop_threads:
                break
        output_field.text += "done!\n"

    def run_agent(input):
        agent.run(input)
        global stop_threads
        stop_threads = True
        progress.join()

    progress = threading.Thread(target=show_progress)
    progress.start()
    input = {"command": command}
    threading.Thread(target=run_agent, args=(input,)).start()
    
    return

def setup_terminal():
    output_field = TextArea(read_only=True, style="fg:ansigreen")
    side_review = TextArea(read_only=True, width=50, style="fg:ansiyellow")
    side_suggestion = TextArea(read_only=True, width=50, style="fg:ansipurple", height=4)

    input_buffer = Buffer()
    input_field = Window(
        content=BufferControl(buffer=input_buffer),
        height=1,
        align=WindowAlign.LEFT
    )
    
    root_container = VSplit([
        HSplit([
            output_field,
            Window(height=1, char='-'),  # Separator
            VSplit([
                Window(
                    content=FormattedTextControl('> '), 
                    width=2),
                input_field
            ])
        ]),
        Window(width=1, char='|'),  # Separator
        HSplit([
            side_review,
            Window(height=1, char='-'),  # Separator
            side_suggestion
        ])
    ])
    
    layout = Layout(root_container)
    
    # Create key bindings
    kb = KeyBindings()
    
    @kb.add('c-c', eager=True)
    def _(event):
        "Quit application on Ctrl+C"
        event.app.exit()
    
    @kb.add(Keys.Enter)
    def _(event):
        command = input_buffer.text
        last_aicmd = side_suggestion.text
        output_field.text = f"> {command}\n"
        input_buffer.text = ''
        side_review.text = ''
        side_suggestion.text = ''
        
        run_command(app, output_field, last_aicmd, command)

    def stream_to_text(field, part):
        field.text += part

    def setup_stream_callbacks():
        agent.set_ai_stream_callback(lambda part: stream_to_text(side_review, part))
        agent.set_strout_stream_callback(lambda part: stream_to_text(output_field, part))
        agent.set_stderr_stream_callback(lambda part: stream_to_text(output_field, part))
        agent.set_command_stream_callback(lambda part: stream_to_text(side_suggestion, part))

    @kb.add(Keys.Any)
    def _(event):
        input_buffer.insert_text(event.data)
        
    #process backspace
    @kb.add(Keys.Backspace)
    def _(event):
        input_buffer.delete_before_cursor()

    @kb.add('n')
    def _(event):
        input_buffer.insert_text('n')

    # Create and return the application
    app = Application(layout=layout, key_bindings=kb, full_screen=True)
    app.layout.focus(input_field)
    setup_stream_callbacks()
    return app, input_buffer, output_field, side_review, side_suggestion

if __name__ == "__main__":
    app, input_buffer, output_field, side_review, side_suggestion = setup_terminal()
    splash(output_field)
    app.run()