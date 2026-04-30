"""
Usage:
    $ poetry run python sport_analysis/sketches/glucose/plot_glucose.py
"""

import csv
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import datetime_utils
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CURR_DIR = Path(__file__).parent
CSV_FILE = CURR_DIR / "2026.04.28 data.csv"


fields = (
    "Device",
    "Serial Number",
    "Device Timestamp",
    "Record Type",
    "Historic Glucose mg/dL",
    "Scan Glucose mg/dL",
    "Non-numeric Rapid-Acting Insulin",
    "Rapid-Acting Insulin (units)",
    "Non-numeric Food",
    "Carbohydrates (grams)",
    "Carbohydrates (servings)",
    "Non-numeric Long-Acting Insulin",
    "Long-Acting Insulin (units)",
    "Notes",
    "Strip Glucose mg/dL",
    "Ketone mmol/L",
    "Meal Insulin (units)",
    "Correction Insulin (units)",
    "User Change Insulin (units)",
)


def main():
    m = Main()
    m.parse_data(
        from_date=datetime(2026, 4, 28, 0, 0, 0),
        to_date=datetime(2026, 4, 28, 23, 59, 59),
    )
    m.plot()


class Main:
    def __init__(self):
        self.data: pd.DataFrame | None = None
        self.glucose: pd.DataFrame | None = None

    def parse_data(
        self,
        from_date: datetime | str | None = None,
        to_date: datetime | str | None = None,
    ):

        self.data = pd.read_csv(
            CSV_FILE,
            skiprows=1,  # Skip the first row.
            parse_dates=["Device Timestamp"],
            dayfirst=True,
        )
        self.data = self.data.sort_values(by="Device Timestamp")

        # Filter by the given range.
        from_date = datetime_utils.parse_datetime_arg(from_date, is_naive_allowed=True)
        to_date = datetime_utils.parse_datetime_arg(to_date, is_naive_allowed=True)
        if from_date:
            self.data = self.data[
                self.data["Device Timestamp"] >= np.datetime64(from_date)
            ]
        if to_date:
            self.data = self.data[
                self.data["Device Timestamp"] <= np.datetime64(to_date)
            ]

        # Parse glucose.
        self.glucose = pd.DataFrame(columns=["ts", "glucose"])
        self.glucose = self.glucose.set_index("ts")
        for _, row in self.data.iterrows():
            # There are 2 types of reading:
            #  - automatic: those are the readings that the device periodically performs;
            #  - manual: those are the readings performed by me via NFC.
            glucose_value = None
            # Eg. "FreeStyle LibreLink,2503b210-032b-468a-a87d-a92e547a8552,23-04-2026 11:45,0,130,,,,,,,,,,,,,,".
            if row["Record Type"] == 0:
                glucose_value = int(row["Historic Glucose mg/dL"])
            # Eg. "FreeStyle LibreLink,2503b210-032b-468a-a87d-a92e547a8552,23-04-2026 11:48,1,,143,,,,,,,,,,,,,".
            elif row["Record Type"] == 1:
                glucose_value = int(row["Scan Glucose mg/dL"])

            if glucose_value is not None:
                self.glucose.loc[row["Device Timestamp"]] = [glucose_value]
        # Now all the glucose reading, either historic or manually scanned, are added
        #  to self.glucose and sorted by timestamp.

        for ts, row in self.glucose.iterrows():
            print(ts, row["glucose"])

    def plot(self):
        fig, ax = plt.subplots(layout="constrained")
        ax.plot(self.glucose.index, self.glucose.glucose)

        formatter = mpl.dates.ConciseDateFormatter(ax.xaxis.get_major_locator())
        ax.xaxis.set_major_formatter(formatter)

        path = CURR_DIR / "img.png"
        plt.savefig(path)
        print(path.resolve())


if __name__ == "__main__":
    print("START")
    main()
    print("END")

# TODO
#  - 70-180 intervallo di glicemia normale
