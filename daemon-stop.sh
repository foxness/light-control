#!/bin/bash

SESSION="light-control"

tmux has-session -t $SESSION 2>/dev/null

if [ $? -eq 0 ]; then
    # send Ctrl+c interrupt
    tmux send-keys -t $SESSION C-c
    sleep 0.1
    tmux kill-session -t $SESSION
    echo "session '$SESSION' has bowed out gracefully. your conscience is clean."
else
    echo "session '$SESSION' not found. you can't kill a ghost."
fi
