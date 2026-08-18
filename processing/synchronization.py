from pathlib import Path
import pandas as pd


# ============================================================
# Configuration
# ============================================================

INPUT_DIR = Path("data")
OUTPUT_DIR = Path("data")

RESULTS_FILE = INPUT_DIR / "edge_results.csv" # Or server_results.csv
USAGE_FILE = INPUT_DIR / "edge_usage.csv" # Or server_usage.csv 
POWER_FILE = INPUT_DIR / "edge_power_readings.csv" # Or server_power_readings.csv

OUTPUT_FILE = OUTPUT_DIR / "edge_synchronized_data.csv" # OR server_synchronized_data.csv


# ============================================================
# Load datasets
# ============================================================

results_df = pd.read_csv(RESULTS_FILE)
usage_df = pd.read_csv(USAGE_FILE)
power_df = pd.read_csv(POWER_FILE)


# ============================================================
# Normalize column names
# ============================================================

def normalize_columns(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("\t", "")
    )
    return df


results_df = normalize_columns(results_df)
usage_df = normalize_columns(usage_df)
power_df = normalize_columns(power_df)


# ============================================================
# Identify time columns in monitoring datasets
# ============================================================

def find_time_column(df):
    for column in df.columns:
        if "time" in column:
            return column
    raise ValueError("No time column found")


usage_time_col = find_time_column(usage_df)
power_time_col = find_time_column(power_df)


# ============================================================
# Create unified datetime values
# ============================================================

results_df["start_dt"] = pd.to_datetime(
    results_df["date"].astype(str) + " " +
    results_df["start_time"]
)

results_df["end_dt"] = pd.to_datetime(
    results_df["date"].astype(str) + " " +
    results_df["end_time"]
)

usage_df["datetime"] = pd.to_datetime(
    usage_df["date"].astype(str) + " " +
    usage_df[usage_time_col]
)

power_df["datetime"] = pd.to_datetime(
    power_df["date"].astype(str) + " " +
    power_df[power_time_col]
)


# ============================================================
# Resolve duplicate resource measurements
# ============================================================

usage_df = (
    usage_df
    .sort_values(
        by=["datetime", "cpu_percent", "mem_percent"],
        ascending=[True, False, False]
    )
    .drop_duplicates("datetime", keep="first")
)


# ============================================================
# Resolve duplicate power measurements
# ============================================================

power_df = (
    power_df
    .sort_values(
        by=["datetime", "power_watts"],
        ascending=[True, False]
    )
    .drop_duplicates("datetime", keep="first")
)


# ============================================================
# Synchronize measurements for each experiment
# ============================================================

final_parts = []

for _, experiment in results_df.iterrows():

    # Create one-second timeline for the experiment
    timestamps = pd.date_range(
        experiment["start_dt"],
        experiment["end_dt"],
        freq="1s"
    )

    block = pd.DataFrame({"datetime": timestamps})

    # Associate workload information with each timestamp
    block["command"] = experiment["command"]
    block["cpu_utilization"] = experiment["cpu_utilization"]

    # Align CPU and memory measurements
    block = block.merge(
        usage_df[
            ["datetime", "cpu_percent", "mem_percent"]
        ],
        on="datetime",
        how="left"
    )

    # Align power measurements
    block = block.merge(
        power_df[
            ["datetime", "power_watts"]
        ],
        on="datetime",
        how="left"
    )

    # Interpolate missing measurements
    for column in [
        "cpu_percent",
        "mem_percent",
        "power_watts"
    ]:
        block[column] = block[column].interpolate(
            method="linear",
            limit_direction="both"
        )

    final_parts.append(block)


# ============================================================
# Combine synchronized experiments
# ============================================================

final_df = pd.concat(
    final_parts,
    ignore_index=True
)


# ============================================================
# Format final dataset
# ============================================================

final_df["date"] = final_df["datetime"].dt.date
final_df["time"] = final_df["datetime"].dt.time

final_df = final_df[
    [
        "command",
        "cpu_utilization",
        "date",
        "time",
        "cpu_percent",
        "mem_percent",
        "power_watts",
    ]
]


# ============================================================
# Save output
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

final_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print(f"Synchronized dataset saved to: {OUTPUT_FILE}")

