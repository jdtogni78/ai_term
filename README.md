# Ai Terminal

Ai Terminal enables direct interaction with LLMs from the terminal.

It integrates with the terminal in a seamless way, adding AI capabilities to the terminal:
* Requests AI suggestions for command corrections based on the last error automatically collected from stderr
* Requests AI for command suggestions to fulfill user requests
* Requests AI creating full scripts to automate complex tasks

## Commands

* `aihelp <question/request>` - Shows the available commands
* `aierr <error_number>` - Request AI for command suggestions based on the last command & stderr
* `askai <question/request>` - Request AI for any kind of assistant, focusing on solutions with python or shell scripting
* `aiscript <request/question>` - Request AI for creating a script to fulfill a request in python or shell scripting

## Examples

### aiask
![aiask](https://github.com/user-attachments/assets/2db4f234-9fea-47cb-8900-a9eaa8143a48)

### aierr
![aierr](https://github.com/user-attachments/assets/8af2f088-af22-49db-999d-0f1220309539)

### aiscript
![aiscript](https://github.com/user-attachments/assets/a412e0f7-f616-4be7-95e8-3daae910095b)


## LLM Setup

The terminal assumes **Ollama** is running locally, and the model **lama3.1** is available.
Download and install ollama from https://ollama.com/download.
Install the lama3.1 model with the command: `ollama pull lama3.1`.

To use groq for faster responses set the **GROQ_API_KEY** environment variable or in the **.env** file.

Create a new key at https://console.groq.com/keys.

## Run the terminal

```
pip install -r requirements.txt
pip install -e .
./ai_term.sh
```

## Ideas

* Review the current state of the art in AI terminals and compare to this project.
    * https://www.warp.dev/
    * https://github.com/nvbn/thefuck
* Integrate with other LLMs
* Send more history of commands to the AI
* Support multiple shells, powers shell, etc...
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

