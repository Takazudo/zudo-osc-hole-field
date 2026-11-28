#!/bin/bash
# C13 wrapper: starts the guarded heartbeat detached, then reports itself alive every 10 s until it is killed.
S=/home/user/wt-a/scripts/stack/studies/mc04_s16_l0301_replan
W=$S/checkpoints/c13/wrapper.txt
echo "wrapper_start $(date +%s.%N) pid $$" > $W
setsid nohup /home/user/venv312/bin/python $S/../mc04_s15_no_growth_moves/guard15.py $S/checkpoints/c13/guard.json -- /home/user/venv312/bin/python $S/c13_heartbeat.py $S/checkpoints/c13/heartbeat.txt > /dev/null 2>&1 < /dev/null &
echo "child_started $(date +%s.%N)" >> $W
while true; do echo "wrapper_alive $(date +%s.%N)" >> $W; sleep 10; done
