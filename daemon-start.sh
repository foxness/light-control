#!/bin/bash

SESSION="light-control"
CMD="/Users/river/my/projects/light-control/run.sh"

tmux has-session -t $SESSION 2>/dev/null

if [ $? != 0 ]; then
  tmux new-session -d -s $SESSION "$CMD"
  echo "session '$SESSION' spawned. it lives in the walls now."
else
  echo "session '$SESSION' already exists."
  echo "attach with: tmux a -t $SESSION"
fi
