#!/bin/bash
# K3 wrapper: starts the guarded heartbeat detached, then reports itself alive every 10 s until killed.
D=/home/user/wt-a/scripts/stack/studies/mc04_s16b_l0301_continuation/checkpoints/k3
echo "wrapper_start $(date +%s.%N) pid $$" > $D/wrapper.txt
setsid nohup /home/user/venv312/bin/python /home/user/wt-a/scripts/stack/studies/mc04_s15_no_growth_moves/guard15.py $D/guard.json -- /home/user/venv312/bin/python /home/user/wt-a/scripts/stack/studies/mc04_s16b_l0301_continuation/k3_heartbeat.py $D/heartbeat.txt > /dev/null 2>&1 < /dev/null &
echo "child_started $(date +%s.%N)" >> $D/wrapper.txt
while true; do echo "wrapper_alive $(date +%s.%N)" >> $D/wrapper.txt; sleep 10; done
