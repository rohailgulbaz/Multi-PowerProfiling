#!/usr/bin/env bash

# ================================
# System Utilization Monitor
# Works on any Linux server size
# Auto-detects logical CPU cores
# ================================

INTERVAL="${INTERVAL:-1}"   # seconds between samples

# Detect logical CPU cores
LOGICAL_CORES=$(nproc)

# --------------------------------
# Get aggregate CPU counters
# --------------------------------
get_cpu() {
    read -ra CPU < /proc/stat

    # idle + iowait
    local idle=$((CPU[4] + CPU[5]))

    # total excluding guest times
    local total=$((CPU[1] + CPU[2] + CPU[3] + CPU[4] + CPU[5] + CPU[6] + CPU[7] + CPU[8]))

    echo "$total $idle"
}

# --------------------------------
# Get memory usage %
# --------------------------------
get_mem_percent() {
    awk '
        /MemTotal/     {total=$2}
        /MemAvailable/ {avail=$2}
        END {
            printf "%.2f", ((total-avail)/total)*100
        }
    ' /proc/meminfo
}

# --------------------------------
# Initialize CPU counters
# --------------------------------
read TOTAL_PREV IDLE_PREV <<< "$(get_cpu)"

# CSV header
echo "date,time,cpu_percent,mem_percent"

# --------------------------------
# Main loop
# --------------------------------
while true; do

    date=$(date "+%Y-%m-%d")
    time=$(date "+%H:%M:%S")

    # ----- CPU -----
    read TOTAL_CUR IDLE_CUR <<< "$(get_cpu)"

    DIFF_TOTAL=$((TOTAL_CUR - TOTAL_PREV))
    DIFF_IDLE=$((IDLE_CUR - IDLE_PREV))

    if [[ "$DIFF_TOTAL" -eq 0 ]]; then
        cpu_percent="0.00"
    else
        cpu_percent=$(awk -v total="$DIFF_TOTAL" -v idle="$DIFF_IDLE" '
            BEGIN {
                printf "%.2f", 100 * (total - idle) / total
            }
        ')
    fi

    TOTAL_PREV=$TOTAL_CUR
    IDLE_PREV=$IDLE_CUR

    # ----- Memory -----
    mem_percent=$(get_mem_percent)

    # ----- Output -----
    echo "$date,$time,$cpu_percent,$mem_percent"
    sleep "$INTERVAL"
done
