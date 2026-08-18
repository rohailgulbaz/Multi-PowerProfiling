from pathlib import Path
import re
import pandas as pd


# ============================================================
# Configuration
# ============================================================

INPUT_FILE = Path("data/synchronized_data.csv")
OUTPUT_DIR = Path("data/cpu_groups")

TOTAL_CORES = 32

CORE_LEVELS = {
    25: int(TOTAL_CORES * 0.25),
    50: int(TOTAL_CORES * 0.50),
    75: int(TOTAL_CORES * 0.75),
    100: int(TOTAL_CORES * 1.00),
}


# ============================================================
# Load dataset
# ============================================================

df = pd.read_csv(INPUT_FILE)


# ============================================================
# Create datetime for chronological sorting
# ============================================================

df["datetime"] = pd.to_datetime(
    df["date"].astype(str) + " " + df["time"].astype(str),
    errors="coerce"
)


# ============================================================
# Extract CPU workers from stress-ng command
# ============================================================

def extract_cpu_cores(command):
    match = re.search(r"--cpu\s+(\d+)", str(command))
    return int(match.group(1)) if match else None


df["cpu_cores"] = df["command"].apply(
    extract_cpu_cores
)


# ============================================================
# Convert utilization to numeric
# ============================================================

df["cpu_utilization"] = pd.to_numeric(
    df["cpu_utilization"],
    errors="coerce"
)


OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# Baseline: CPU utilization = 0
# ============================================================

baseline_df = df[
    df["cpu_utilization"] == 0
].copy()

baseline_df = baseline_df.sort_values(
    by="datetime"
)

baseline_df.drop(
    columns=["datetime", "cpu_cores"],
    errors="ignore"
).to_csv(
    OUTPUT_DIR / "baseline.csv",
    index=False
)


# ============================================================
# Process CPU-capacity groups
# ============================================================

for level, core_count in CORE_LEVELS.items():

    subset = df[
        (df["cpu_cores"] == core_count)
        &
        (df["cpu_utilization"] >= 1)
        &
        (df["cpu_utilization"] <= 100)
    ].copy()


    # ========================================================
    # Special integer-bin mapping for 75% core configuration
    # ========================================================

    if level == 75:

        selected_parts = []

        for target in range(1, 101):

            if target % 3 == 0:

                values = [float(target)]

            elif target % 2 == 0:

                values = [
                    target - 0.5,
                    target + 0.25
                ]

            else:

                values = [
                    target - 0.25
                ]


            part = subset[
                subset["cpu_utilization"].isin(values)
            ].copy()


            # Map the selected floating-point values
            # to the corresponding integer utilization bin
            part["cpu_utilization"] = target

            selected_parts.append(part)


        subset = pd.concat(
            selected_parts,
            ignore_index=True
        )


    # ========================================================
    # Sort and save
    # ========================================================

    subset = subset.sort_values(
        by=["cpu_utilization", "datetime"]
    )

    output_file = OUTPUT_DIR / f"{level}percent_cores.csv"

    subset.drop(
        columns=["datetime", "cpu_cores"],
        errors="ignore"
    ).to_csv(
        output_file,
        index=False
    )

    print(
        f"{output_file} done: {len(subset)} records"
    )
