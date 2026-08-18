from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde


# ============================================================
# Configuration
# ============================================================

INPUT_DIR = Path("data")
OUTPUT_DIR = Path("results")

INPUT_FILES = {
    "baseline": INPUT_DIR / "edge_baseline.csv",  # OR server_baseline.csv
    25: INPUT_DIR / "edge_25percent_cores.csv",   # OR server_25percent_cores.csv
    50: INPUT_DIR / "edge_50percent_cores.csv",   # OR server_50percent_cores.csv
    75: INPUT_DIR / "edge_75percent_cores.csv",   # OR server_75percent_cores.csv
    100: INPUT_DIR / "edge_100percent_cores.csv", # OR server_100percent_cores.csv
}

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# Preprocess
# ============================================================

def preprocess(df):

    df = df.copy()

    df["datetime"] = pd.to_datetime(
        df["date"].astype(str)
        + " "
        + df["time"].astype(str)
    )

    df = df.sort_values(
        by=["cpu_utilization", "datetime"]
    ).reset_index(drop=True)

    return df


# ============================================================
# Extract continuous one-second segments
# ============================================================

def extract_segments(group):

    if group.empty:
        return []

    segments = []

    current = [group.iloc[0]]

    for i in range(1, len(group)):

        diff = (
            group.iloc[i]["datetime"]
            - group.iloc[i - 1]["datetime"]
        ).total_seconds()

        if diff == 1:

            current.append(
                group.iloc[i]
            )

        else:

            segments.append(
                pd.DataFrame(current)
            )

            current = [
                group.iloc[i]
            ]

    segments.append(
        pd.DataFrame(current)
    )

    return segments


# ============================================================
# Compute power statistics
# ============================================================

def compute_statistics(values):

    values = np.asarray(values)

    # --------------------------------------------------------
    # Empirical statistics
    # --------------------------------------------------------

    mean = np.mean(values)

    median = np.median(values)

    # Power measurements are floating-point values.
    # Round to two decimal places before calculating mode.
    mode = (
        pd.Series(
            np.round(values, 2)
        )
        .mode()
        .iloc[0]
    )

    p25 = np.percentile(
        values,
        25
    )

    p75 = np.percentile(
        values,
        75
    )

    p90 = np.percentile(
        values,
        90
    )

    sd = np.std(
        values,
        ddof=1
    )

    # --------------------------------------------------------
    # KDE statistics
    # --------------------------------------------------------

    if len(values) < 2:

        return {
            "Mean": mean,
            "Median": median,
            "Mode": mode,

            "KDE_Mode": mean,
            "KDE_Mean": mean,
            "KDE_Median": mean,

            "P25": p25,
            "P75": p75,
            "P90": p90,

            "SD": sd
        }

    kde = gaussian_kde(values)

    x_grid = np.linspace(
        values.min(),
        values.max(),
        2000
    )

    density = kde(x_grid)

    # Normalize KDE so that its integral is 1
    density = (
        density
        /
        np.trapz(
            density,
            x_grid
        )
    )

    # KDE mode: point of maximum density
    kde_mode = x_grid[
        np.argmax(density)
    ]

    # KDE mean
    kde_mean = np.trapz(
        x_grid * density,
        x_grid
    )

    # KDE median
    dx = (
        x_grid[1]
        - x_grid[0]
    )

    cdf = (
        np.cumsum(density)
        * dx
    )

    cdf = (
        cdf
        /
        cdf[-1]
    )

    kde_median = np.interp(
        0.5,
        cdf,
        x_grid
    )

    return {
        "Mean": mean,
        "Median": median,
        "Mode": mode,

        "KDE_Mode": kde_mode,
        "KDE_Mean": kde_mean,
        "KDE_Median": kde_median,

        "P25": p25,
        "P75": p75,
        "P90": p90,

        "SD": sd
    }


# ============================================================
# Process one CPU-capacity configuration
# ============================================================

def process(
    df,
    capacity_label
):

    all_rows = []

    filtered_rows = []

    # Analyze each target CPU-utilization level
    for cpu_util, group in df.groupby(
        "cpu_utilization"
    ):

        segments = extract_segments(
            group
        )

        valid_segments = []

        for segment in segments:

            # Require more than 10 samples
            if len(segment) > 10:

                # Remove first and last five samples
                # to exclude workload transients
                segment = segment.iloc[5:-5]

                # Keep measurements within ±1% of target
                filtered = segment[
                    (segment["cpu_percent"]
                     >= cpu_util - 1)
                    &
                    (segment["cpu_percent"]
                     <= cpu_util + 1)
                ]

                if not filtered.empty:

                    valid_segments.append(
                        filtered
                    )

        if valid_segments:

            combined = pd.concat(
                valid_segments,
                ignore_index=True
            )

            filtered_rows.append(
                combined
            )

            statistics = compute_statistics(
                combined["power_watts"].values
            )

            row = {
                "cpu_capacity": capacity_label,
                "cpu_utilization": cpu_util
            }

            row.update(
                statistics
            )

            all_rows.append(
                row
            )

    # --------------------------------------------------------
    # Save all filtered measurements
    # --------------------------------------------------------

    if filtered_rows:

        filtered_df = pd.concat(
            filtered_rows,
            ignore_index=True
        )

        output_file = (
            OUTPUT_DIR
            /
            f"edge_{capacity_label}_filtered_valid_rows.csv"
            # OR f"server_{capacity_label}_filtered_valid_rows.csv"
        )

        filtered_df.to_csv(
            output_file,
            index=False
        )

        print(
            f"{output_file}: "
            f"{len(filtered_df)} records"
        )

    return pd.DataFrame(
        all_rows
    )


# ============================================================
# Load and preprocess datasets
# ============================================================

baseline = preprocess(
    pd.read_csv(
        INPUT_FILES["baseline"]
    )
)

capacity_data = {}

for capacity in [
    25,
    50,
    75,
    100
]:

    capacity_data[capacity] = preprocess(
        pd.read_csv(
            INPUT_FILES[capacity]
        )
    )


# ============================================================
# Process each CPU-capacity level
#
# Baseline is included for every configuration, as in the
# original analysis.
# ============================================================

summary_parts = []

for capacity in [
    25,
    50,
    75,
    100
]:

    combined_df = pd.concat(
        [
            baseline,
            capacity_data[capacity]
        ],
        ignore_index=True
    )

    result = process(
        combined_df,
        f"{capacity}percent"
    )

    summary_parts.append(
        result
    )


# ============================================================
# Final summary
# ============================================================

final_df = pd.concat(
    summary_parts,
    ignore_index=True
)

summary_file = (
    OUTPUT_DIR
    /
    "edge_statistics.csv"
    # OR "server_statistics.csv"
)

final_df.to_csv(
    summary_file,
    index=False
)

print(
    f"Saved: {summary_file}"
)
