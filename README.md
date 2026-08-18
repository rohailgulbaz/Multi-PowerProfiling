# Multi-PowerProfiling
Code and data for resource profiling and power prediction

A workload-aware power profiling framework for Edge and Server systems that constructs multiple power profiles across different CPU core configurations and utilization levels, enabling accurate workload power and energy estimation.

## Overview

Traditional power models often rely on a single power profile for an entire machine. However, identical system-wide CPU utilization can be achieved through different combinations of active cores and per-core load, resulting in different power characteristics.

**Multi-PowerProfiling** addresses this issue by creating separate statistical power profiles for different CPU-capacity configurations and utilization levels. These profiles can later be used to estimate power consumption of arbitrary workloads and validate results against ground-truth measurements obtained from PDUs and power meters.

The framework supports:

- Edge devices
- Servers
- MQTT-based power monitoring
- SNMP/PDU-based power monitoring
- Automated workload generation using stress-ng
- Statistical power profile construction
- Energy estimation from workload traces
- Ground-truth validation

Our experimental evaluation demonstrated approximately **84% average accuracy**, outperforming several state-of-the-art approaches under diverse workload conditions. Details regarding evaluation methodology, benefits, and comparisons are available in the accompanying research paper.

---

# Methodology

The complete workflow follows the sequence below:

```text
Monitoring Setup
       ↓
Profile Generation Experiments
       ↓
Synchronization
       ↓
Grouping
       ↓
Statistics Generation
       ↓
Workload Power Prediction
       ↓
Ground Truth Validation
       ↓
Model Comparison
```

---

# Repository Workflow

## Phase 1: Monitoring Setup

Start resource monitoring and power monitoring before running experiments.

### Resource Monitoring

The monitoring framework captures:

- CPU utilization
- Memory utilization
- Timestamped measurements

Monitoring operates at a default sampling interval of **1 second**.

### Power Monitoring

Two monitoring mechanisms are supported.

#### Edge Devices

MQTT-based smart plug measurements.

#### Servers

SNMP-based PDU measurements.

---

## Phase 2: Workload Profiling

Profiling experiments are executed using **stress-ng**.

The experiment framework automatically:

- Detects available logical CPU cores
- Creates workload classes using:
  - 25% of logical cores
  - 50% of logical cores
  - 75% of logical cores
  - 100% of logical cores
- Sweeps CPU utilization levels
- Randomizes execution order
- Repeats each workload configuration three times

---

## Phase 3: Synchronization

Algorithm 3 synchronizes:

- experiment logs
- usage logs
- power measurements

into a unified per-second dataset.

---

## Phase 4: Grouping

Algorithm 4 groups synchronized observations according to:

- CPU-capacity level
- CPU utilization

creating separate datasets for:

```text
Baseline
25% Cores
50% Cores
75% Cores
100% Cores
```

---

## Phase 5: Statistics Generation

Algorithm 5 generates workload-independent statistical power profiles.

The resulting statistics include:

- Mean
- Median
- Mode
- KDE Mode
- KDE Mean
- KDE Median
- P25
- P75
- P90
- Standard Deviation

These statistics are later used as prediction models.

---

# Directory Relationships

Some scripts are wrappers around other scripts and must remain in the same directory.

### Experiment Scripts

```text
edge_experiment.sh
└── requires experiment.sh

server_experiment.sh
└── requires experiment.sh
```

### Monitoring Scripts

```text
edge_usage.sh
└── requires monitor_usage.sh

server_usage.sh
└── requires monitor_usage.sh
```

---

# Prerequisites

## Linux

Tested on Linux systems with:

- Bash
- SSH

---

## stress-ng

Used for workload generation.

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install stress-ng
```

### Fedora

```bash
sudo dnf install stress-ng
```

### Arch

```bash
sudo pacman -S stress-ng
```

---

## Python

Recommended:

```text
Python 3.9+
```

Install required packages:

```bash
pip install pandas numpy scipy
```

---

## MQTT Utilities

Required for Edge power monitoring:

```bash
sudo apt install mosquitto-clients
```

---

## SNMP Utilities

Required for Server power monitoring:

```bash
sudo apt install snmp
```

---

# Running Monitoring

## Edge Usage Monitoring

```bash
systemd-inhibit --what=sleep --why="monitoring overnight" \
bash ~/monitor.sh > ~/usage.csv
```

---

## Edge Power Monitoring

```bash
systemd-inhibit --what=sleep --why="MQTT logging" bash -c '
mosquitto_sub -u USER -P PASSWORD \
-h MQTT_BROKER -p MQTT_PORT \
-t "TOPIC" |
while read power; do
    echo "$(date +%Y-%m-%d),$(date +%H:%M:%S),$power"
done >> ~/power_readings.csv
'
```

---

## Server Usage Monitoring

```bash
systemd-inhibit --what=sleep --why="Usage Monitoring" \
ssh USER@SERVER 'bash -s' < monitorServerUsage.sh \
| tee -a ~/usage.csv
```

---

## Server Power Monitoring

```bash
systemd-inhibit --what=sleep --why="Power Monitoring" \
ssh USER@SERVER '
echo "date,time,power_watts"
while true; do
    POWER=$(snmpget ...)
    echo "$(date +%Y-%m-%d),$(date +%H:%M:%S),$POWER"
    sleep 1
done
' | tee -a ~/power_readings.csv
```

---

# Running Profiling Experiments

## Edge Profiling

```bash
systemd-inhibit --what=sleep --why="stress-ng experiment" \
ssh <REMOTE_USER>@<REMOTE_HOST> \
'cd /tmp && bash -s' < experiment.sh \
| tee -a ~/data/edge_results.csv
```

---

## Server Profiling

```bash
systemd-inhibit --what=sleep --why="stress-ng experiment" \
ssh <REMOTE_USER>@<REMOTE_HOST> \
'cd /tmp && bash -s' < experiment.sh \
| tee -a ~/data/server_results.csv
```

---



# Citation

The accompanying research paper is currently under publication.

A complete BibTeX entry and citation information will be added upon publication.

If you use this repository, methodology, code, datasets, or generated profiles, please cite the paper once it becomes available.

```bibtex
% Citation information will be added after publication
```

---

# Recommended Workflow

```text
1. Start Usage Monitoring
2. Start Power Monitoring
3. Run Profiling Experiments
4. Execute Synchronization
5. Execute Grouping
6. Execute Statistics Generation
7. Run Target Workload
8. Use Statistical Profiles for Power Prediction
9. Calculate Energy Consumption
10. Compare Against Ground Truth
11. Compare Against Alternative Models
12. Report Results
```
