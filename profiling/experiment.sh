#!/bin/bash
TOTAL_CORES=$(nproc)

A_CORES=$(( TOTAL_CORES * 25 / 100 ))
B_CORES=$(( TOTAL_CORES * 50 / 100 ))
C_CORES=$(( TOTAL_CORES * 75 / 100 ))
D_CORES=$(( TOTAL_CORES * 100 / 100 ))

A_MAX_PD=25
B_MAX_PD=50
D_MAX_PD=100

F_MAX=100 #just checking all combinations, since using 75% cores we cannot get all combinations. Therefore
#we are checking combinations with this pattern 0, 0.75, 1.5, 2.25, 3, 3.75

CMDS=()

#####################################
# A (25% cores)
#####################################
for PD in $(seq 0 $A_MAX_PD); do
  E=$(( PD * TOTAL_CORES / A_CORES ))
  CMDS+=("stress-ng --cpu $A_CORES --cpu-load $E --timeout 60s --quiet|$PD|A")
done

#####################################
# B (50% cores)
#####################################
for PD in $(seq 0 $B_MAX_PD); do
  E=$(( PD * TOTAL_CORES / B_CORES ))
  CMDS+=("stress-ng --cpu $B_CORES --cpu-load $E --timeout 60s --quiet|$PD|B")
done

#####################################
# C (75% cores)
#####################################
for F in $(seq 0 $F_MAX); do
    CMDS+=("stress-ng --cpu $C_CORES --cpu-load $F --timeout 60s --quiet|$F|C")
done

#####################################
# D (100% cores)
#####################################
for PD in $(seq 0 $D_MAX_PD); do
  E=$(( PD * TOTAL_CORES / D_CORES ))
  CMDS+=("stress-ng --cpu $D_CORES --cpu-load $E --timeout 60s --quiet|$PD|D")
done

#####################################
# HEADER (IMPORTANT: printed to stdout)
#####################################
echo "command,cpu_utilization,date,start_time,end_time"

#####################################
# RUN 3 TIMES SHUFFLED
#####################################
for run in {1..3}; do
  echo "# RUN $run" >&2

  printf "%s\n" "${CMDS[@]}" | shuf | while IFS='|' read -r CMD X CLASS; do

    DATE=$(date +%F)
    START=$(date +%H:%M:%S)

   	bash -c "$CMD" >/dev/null 2>&1

    END=$(date +%H:%M:%S)

    if [[ "$CLASS" == "C" ]]; then
      H=$(echo "scale=2; ($X * $C_CORES) / $TOTAL_CORES" | bc)
    else
      H=$X
    fi

    echo "$CMD,$H,$DATE,$START,$END"
    sleep 60
  done

done

echo "# DONE" >&2
