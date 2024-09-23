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

## LLM Setup

The terminal assumes **Ollama** is running locally, and the model **lama3.1** is available.
Download and install ollama from https://ollama.com/download.
Install the lama3.1 model with the command: `ollama pull lama3.1`.

To use groq for faster responses set the **GROQ_API_KEY** environment variable or in the **.env** file.

Create a new key at https://console.groq.com/keys.

## Sample of current state
 
https://github.com/user-attachments/assets/49e73206-f1d6-4917-ad46-8c3609ac825f

## Run the terminal

```
pip install -r requirements.txt
pip install -e .
./ai_term_pipe.py
```

## Ideas

* Review the current state of the art in AI terminals and compare to this project.
    * https://www.warp.dev/
    * https://www.cursor.sh/
* Use instructor for structured outputs https://python.useinstructor.com/
* Create a teminal centric UX, by making it seemlessly integrated with the terminal, some ideas:
    * Automatically process stderr and stdout through ai
        * Evaluate "exec 2> some_pipe" to redirect stderr to a pipe, see https://unix.stackexchange.com/questions/81861/redirect-all-stderr-of-a-console-and-subsequent-commands-to-a-file
        * Limit the amount of data sent to the AI, for example send 20 head/tail lines for each stream
    * Get the last commands from bash history
    * Create commands for the "askai" feature
* Integrate with other LLMs
* Send more history of commands to the AI
* Add tools to the AI agent
    * Web Search
    * File Search & Indexing
* Create a suggestion / test / review cycle for commands to improve quality of results
* Adopt RAGs (Retrieval Augmented Generation) for better performance on long term memory
    * Indexing of local files
    * Indexing of web pages
    * Indexing of git repositories
* Allow for project management
    * Indexing of project files
    * Automatic generation of project structure

