"""
Plot my weight history.

The file with the weight data `2025.11.04` was exported from my scale
 Renpho ES-CS20M.
To extract the weights from the scale see:
 /Volumes/home/Drive/DOCUMENTI-SYNC/IT/WEARABLE,\ FITNESS/Bilancia\ Renpho\ ES-CS20M/EXPORT/How\ to

Usage:
    $ poetry run python sport_analysis/sketches/weight/plot_weight.py
"""

import csv
from datetime import datetime
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

CURR_DIR = Path(__file__).parent
CSV_FILE = CURR_DIR / "2025.11.04.csv"


fields = (
    "Date",
    "Time",
    "Weight",
    "BMI",
    "Body Fat(%)",
    "Skeletal Muscle(%)",
    "Fat-Free Mass(kg)",
    "Subcutaneous Fat(%)",
    "Visceral Fat",
    "Body Water(%)",
    "Muscle Mass(kg)",
    "Bone Mass(kg)",
    "Protein(%)",
    "BMR(kcal)",
    "Metabolic Age",
    "Optimal Weight(kg)",
    "Target to optimal weight(kg)",
    "Target to optimal fat mass(kg)",
    "Target to optimal muscle mass(kg)",
    "Body Type",
    "Remarks",
)


def main():
    print("MAIN")
    weights = list()
    days = list()
    with open(CSV_FILE, newline="") as csvfile:
        # reader = csv.reader(csvfile, delimiter=",")
        reader = csv.DictReader(csvfile, fieldnames=fields, delimiter=",")
        for i, row in enumerate(reader):
            if i == 0:
                continue
            weights.append(float(row["Weight"]))
            days.append(datetime.strptime(row["Date"], "%Y.%m.%d").date())

    if len(weights) != len(days):
        raise Exception("BUG: the collected weights and days have different count!")

    weights.reverse()
    days.reverse()

    fig, ax = plt.subplots(layout="constrained")
    ax.plot(days, weights)

    formatter = mpl.dates.ConciseDateFormatter(ax.xaxis.get_major_locator())
    ax.xaxis.set_major_formatter(formatter)

    # Try to force labels for the first and last date, but te result is bad.
    # xticks = list(ax.get_xticks())
    # xticks[0] = mpl.dates.date2num(dates[0])
    # xticks[-1] = mpl.dates.date2num(dates[-1])
    # ax.set_xticks(xticks)

    path = CURR_DIR / "img.png"
    plt.savefig(path)
    print(path.resolve())


if __name__ == "__main__":
    print("START")
    main()
    print("END")
