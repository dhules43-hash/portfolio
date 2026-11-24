#!/bin/bash
# resumable full render of all reference-style shots
cd "$(dirname "$0")"; export SAMPLES=${SAMPLES:-14}
for i in $(seq 1 18); do s=$(date +%s); python3 shots.py $i render > /tmp/shot$i.log 2>&1; echo "shot $i exit=$? $(ls ../renders/shots/sh$(printf %02d $i) 2>/dev/null | wc -l) frames $(( $(date +%s)-s ))s" >> /tmp/render_shots.log; done
echo DONE >> /tmp/render_shots.log
