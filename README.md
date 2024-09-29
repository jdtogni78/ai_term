# Ai Terminal

*** *DISCLAIMER: This project is in early stages, features were tested with basic use cases, in a single environment as of now.* ***

Ai Terminal enables direct interaction with LLMs from the terminal.

It integrates with the terminal in a seamless way, adding AI capabilities to the terminal:
* Requests AI suggestions for command corrections based on the last error automatically collected from stderr
* Requests AI for command suggestions to fulfill user requests
* Requests AI creating full scripts to automate complex tasks

## Commands

* `aihelp <question/request>` - Shows the available commands
* `aierr <error_number>` - Request AI for command suggestions for some recent command & errors
* `ailast` - Request AI for command suggestions based on the last command & errors
* `askai <question/request>` - Request AI for any kind of assistant, focusing on solutions with python or shell scripting
* `aiscript <request/question>` - Request AI for creating a script to fulfill a request in python or shell scripting
* `aiprops` - Show the AI assistant properties
* `aihelp` - Show the help message

## Examples

The following examples were generated using **llama3.1-8b-versatile** model via **Groq**.

### aiask
![aiask example](https://github.com/user-attachments/assets/2db4f234-9fea-47cb-8900-a9eaa8143a48)

### aierr
![aierr example](https://github.com/user-attachments/assets/8af2f088-af22-49db-999d-0f1220309539)

### aiscript
![aiscript example](https://github.com/user-attachments/assets/93bc17c0-9692-4738-a34a-008684c76615)


* **DISCLAIMER:** The quality of the results depends heavily on the **prompt** and the **capabilities of the LLM**.

## LLM Setup

The terminal assumes **Ollama** is running locally, and the model **lama3.1** is available.
1) Download and install ollama from https://ollama.com/download.

2) Install the lama3.1 model with the command:
    ```
    ollama pull lama3.1
    ollama serve
    ```

3) *Optional*: To use groq for faster responses set the **GROQ_API_KEY** environment variable or in the **.env** file.
Create a key at https://console.groq.com/keys.

3) Python dependencies:

    ```
    python3 -m venv .env
    source .env/bin/activate
    pip install -r requirements.txt
    ```

4) Run the terminal:

    ```
    source .env/bin/activate
    ./ai_term.sh
    ```

## What is next?

There are many ways to extend this project, here are some ideas:

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

