#!/bin/bash

SESSION="light-control"

case $1 in
  "1") COLOR="#c5c45f" ;;
  "2") COLOR="#60d997" ;;
  "3") COLOR="#3752ff" ;;
  "4") COLOR="#8962e0" ;;
  "anki") COLOR="#9fff56 immunity1" ;;
  *) COLOR="#BE3E82" ;;
esac

# #3752ff (55, 82, 255) - nice blue
# #9fff56 (159, 255, 86) - anki green
# #162180 (22, 33, 128) - radioactive blue
# #ff9b42 - sandy

# case $SPACE in
#   "1") COLOR="#ffff99" ;;
#   "2") COLOR="#99ff99" ;;
#   "3") COLOR="#6666ff" ;;
#   "4") COLOR="#D1495B" ;;
#   *) COLOR="#BE3E82" ;;
# esac

# case $SPACE in
#   "1") COLOR="#ff9b42" ;;
#   "2") COLOR="#9fff56" ;;
#   "3") COLOR="#00798C" ;;
#   "4") COLOR="#D1495B" ;;
#   *) COLOR="#BE3E82" ;;
# esac

tmux has-session -t $SESSION 2>/dev/null

if [ $? -eq 0 ]; then
    tmux send-keys -t $SESSION "$COLOR" Enter
    echo "sent color $COLOR to session '$SESSION'."
else
    echo "session '$SESSION' not found."
fi
