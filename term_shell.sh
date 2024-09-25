#!/bin/bash

# Set up prompt to include exit status
# The unicode symbol allow us to segregate prompt and commands from regular stderr
export PS1='👤 \[\033[01;32m\]\u@\h\[\033[00m\] - \[\033[01;34m\]\w\[\033[00m\]\n⚡ '
export BASH_SILENCE_DEPRECATION_WARNING=1
# capture the directory of the script
AITERM_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
export PYTHONPATH="$AITERM_DIR/src:$PYTHONPATH"

CHOICE_SYMBOL="🔘"
QUESTION_SYMBOL="❓"

# Set up FIFO for stderr
STDERR_FIFO="/tmp/stderr_fifo_$$"
CAT_PID=""

start_monitor() {
    stop_monitor
    echo "Starting stderr monitor"
    
    rm -f /tmp/stderr_fifo_*
    mkfifo "$STDERR_FIFO"

    # redirect stderr to fifo, and to python script
    cat "$STDERR_FIFO" | python $AITERM_DIR/src/ai_term/shell/term_shell.py &
    export CAT_PID=$!
    exec 3>&2
    exec 2> "$STDERR_FIFO"
}

stop_monitor() {
    if [ -z "$CAT_PID" ]; then
        return
    fi
    echo "Stopping stderr monitor"
    kill $CAT_PID
    export CAT_PID=""
    exec 2>&3-
    rm -f "$STDERR_FIFO"
}

# send questions to AI
aiask() {
    python $AITERM_DIR/src/ai_term/shell/aiask.py "$*"
}

# ask AI to generate scripts
aiscript() {
    python $AITERM_DIR/src/ai_term/shell/aiscript.py "$*"
}

# execute command generated by AI
aicmd() {
    # if no args, print all commands
    if [ -z "$1" ]; then
        # Print a numbered list of commands
        awk '{print NR ". " $0}' /tmp/predicted_commands.txt
        # ask user to select a command
        read -p "$QUESTION_SYMBOL " selection
        cmd=$(sed -n "${selection}p" /tmp/predicted_commands.txt)
    else
        cmd=$(sed -n "${1}p" /tmp/predicted_commands.txt)
    fi

    # Confirm before executing
    read -p "$QUESTION_SYMBOL $cmd (y/n) " confirm
    if [[ $confirm != [yY] ]]; then
        echo "Command execution cancelled."
        return
    fi
    $cmd
}

aihelp() {
    echo "AI assistant"
    echo "============"
    echo "aiask <question>: ask AI a question"
    echo "aiscript <request>: create scripts to automate tasks"
    echo "aicmd: execute a command generated by AI via aiask/stderr collector"
    echo "start_monitor: start the stderr collector"
    echo "stop_monitor: stop the stderr collector"
    echo "aihelp: show this help message"
}

# start the stderr collector if .env file contains START_MONITOR=1
if [ -f .env ] && grep -q '^START_MONITOR=1' .env; then
    start_monitor
else
    echo "To activate the AI assistant, set START_MONITOR=1 in .env file" 
fi
aihelp

# Function to clean up FIFO on exit
cleanup() {
    stop_monitor
    echo "Exiting"
}
trap cleanup EXIT



