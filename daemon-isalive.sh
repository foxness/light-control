#!/bin/bash

SESSION="light-control"
tmux has-session -t $SESSION 2>/dev/null && echo "Still alive" || echo "He's dead, Jim"
