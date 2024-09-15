# Ai Terminal

This is as project to create an AI supported terminal.

It uses langgraph agents to interface with the AI models.

The terminal should has an ai side bar, the ai reviews all terminal output and is capable of:
* suggesting corrections based on the last error
* making predictions for the next commands

The terminal user can request for ai suggestions with a command "aihelp <question/request>". 

The system runs the terminal commands, capturing the stdout and stderr, and command.
When an error occurs the AI is called to review the output and make a suggestion for the next command.
You can also request for AI help with a command "askai <question/request>".

## Improvements

* Use groq for faster responses
* Use streaming so UI doesnt freeze

 