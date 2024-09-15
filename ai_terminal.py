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
    start_time = time.time()
    main_out = agent.run({"command": command})
    end_time = time.time()
    execution_time = end_time - start_time
    output_field.text += f"\nExecution time: {execution_time:.2f} seconds\n"
    return main_out

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
        
        out = run_command(app, output_field, last_aicmd, command)
        update_text(out)

    def update_text(out):
        if 'stdout' in out and out['stdout'] != '':
            output_field.text += out['stdout']
        if 'stderr' in out and out['stderr'] != '':
            output_field.text += "ERROR:\n" + out['stderr']
        if 'output_review' in out and out['output_review'] != '':
            side_review.text = out['output_review']
        if 'predicted_command' in out and out['predicted_command'] != '':
            side_suggestion.text = out['predicted_command']

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
    
    return app, input_buffer, output_field, side_review, side_suggestion

if __name__ == "__main__":
    app, input_buffer, output_field, side_review, side_suggestion = setup_terminal()
    splash(output_field)
    app.run()