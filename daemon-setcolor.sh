#!/bin/bash

SESSION="light-control"
COLOR="$1"

tmux has-session -t $SESSION 2>/dev/null

if [ $? -eq 0 ]; then
    tmux send-keys -t $SESSION "$COLOR" Enter
    echo "sent color $COLOR to session '$SESSION'."
else
    echo "session '$SESSION' not found."
fi
