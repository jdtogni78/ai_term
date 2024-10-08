#!/bin/bash

# Set up prompt to include exit status
# The unicode symbol allow us to segregate prompt and commands from regular stderr
export PS1='👤 \[\033[01;32m\]\u@\h\[\033[00m\] - \[\033[01;34m\]\w\[\033[00m\]\n⚡'
export BASH_SILENCE_DEPRECATION_WARNING=1
# capture the directory of the script
AITERM_DIR="$( $( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ../.. ) &> /dev/null && pwd )"
export PYTHONPATH="$AITERM_DIR/src:$PYTHONPATH"

# TODO: activate the virtual environment
# source "$AITERM_DIR/.env/bin/activate"
# Source the AI commands library
source "$AITERM_DIR/src/shell/ai_commands.sh"

# start the stderr collector
aicollect start

# display help message
aihelp "splash"

# Function to clean up FIFO on exit
cleanup() {
    ai_stop_monitor
    echo "Exiting"
}
trap cleanup EXIT



