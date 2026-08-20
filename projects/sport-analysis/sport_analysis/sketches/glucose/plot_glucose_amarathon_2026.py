"""
Usage:
    $ poetry run python sport_analysis/sketches/glucose/plot_glucose_amarathon_2026.py
"""

from datetime import date, datetime, timedelta
from pathlib import Path

import datetime_utils
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure

CURR_DIR = Path(__file__).parent

COL_DARK_RED = "#9A2D2D"
COL_DARK_GRAY = "#3B3B3B"
COL_LONDON_GRAY = "#666677"
COL_DARK_BLUE = "#000134"
COL_VERY_DARK_BLUE = "#01025f"

# Important constants.
CSV_FILE = CURR_DIR / "2026.05.08 data.csv"
EVENT_DATE = date(2026, 5, 1)
RACE_START_DATE_STR = "2026-05-01T09:32:00"
RACE_START_DATE = datetime_utils.iso_string_to_datetime(RACE_START_DATE_STR)
RACE_END_DATE_STR = "2026-05-01T11:07:30"
RACE_END_DATE = datetime_utils.iso_string_to_datetime(RACE_END_DATE_STR)
TITLE = "Amarathon 1/5/2026"
DAY_ANNOTATIONS = [
    dict(
        text="Tea,\nrusks,\nhoney,\npeanut butt.,\ncoffee",
        ts="2026-05-01T05:55:00",
        is_y_top_pos=True,
        x_offset=0,
        y_offset=-5.5,
    ),
    dict(
        text="2 dates,\nalmonds",
        ts="2026-05-01T07:50:00",
        is_y_top_pos=True,
        x_offset=0,
        y_offset=-9,
    ),
    dict(
        text="2 dates",
        ts="2026-05-01T08:40:00",
        is_y_top_pos=True,
        x_offset=0,
        y_offset=-1.5,
    ),
    dict(
        text="Coffee,\n30g gel,\nhoney,\nlemon j.",
        ts="2026-05-01T09:15:00",
        is_y_top_pos=False,
        x_offset=0,
        y_offset=7,
    ),
    dict(
        text="Banana, orange, choc. cake,\nlentils chips, sweet wine,\nprotein shake, electolytes",
        ts="2026-05-01T11:11:00",
        is_y_top_pos=True,
        x_offset=0,
        y_offset=-3.5,
    ),
    dict(
        text="Pasta, olives, tomato sauce,\nstuffed courg., salad, tomat.,\nstracchino, bread",
        ts="2026-05-01T14:07:00",
        is_y_top_pos=True,
        x_offset=0,
        y_offset=-8,
    ),
    dict(
        text="Smoothie banana, blueb.,\nstrawb., greek yog.,\nmilk, almonds, oatmeal",
        ts="2026-05-01T17:40:00",
        is_y_top_pos=True,
        x_offset=0,
        y_offset=-12.5,
    ),
    dict(
        text="Veg. soup, chicken\n tights,\nblack rice,\nsalad",
        ts="2026-05-01T19:48:00",
        is_y_top_pos=False,
        x_offset=0,
        y_offset=2,
    ),
]

RACE_ANNOTATIONS = [
    dict(
        text="Alanine,\ncitrulline",
        # ts="2026-05-01T09:45:00",
        ts=(RACE_START_DATE + timedelta(minutes=15)).isoformat(),
        is_y_top_pos=True,
        x_offset=0,
        y_offset=-4.5,
    ),
    dict(
        text="36g gel,\nhoney,\nlemon j.,\nelectrolytes",
        ts=(RACE_START_DATE + timedelta(minutes=30)).isoformat(),
        is_y_top_pos=True,
        x_offset=0,
        y_offset=-6.5,
    ),
    dict(
        text="25g gel,\nhoney,\nlemon j.,\nelectrolytes",
        ts=(RACE_START_DATE + timedelta(minutes=50)).isoformat(),
        is_y_top_pos=True,
        x_offset=0,
        y_offset=-4.5,
    ),
    dict(
        text="14g gel,\nhoney,\nlemon j.,\nelectrolytes",
        ts=(RACE_START_DATE + timedelta(minutes=65)).isoformat(),
        is_y_top_pos=True,
        x_offset=0,
        y_offset=-4.5,
    ),
]


def main():
    m = Main()
    m.parse_data(
        from_date=datetime(EVENT_DATE.year, EVENT_DATE.month, EVENT_DATE.day, 0, 0, 0),
        to_date=datetime(EVENT_DATE.year, EVENT_DATE.month, EVENT_DATE.day, 23, 59, 59),
    )
    m.plot()


class Main:
    def __init__(self):
        self.data: pd.DataFrame | None = None
        self.glucose: pd.DataFrame | None = None
        self.fig: Figure | None = None
        self.axes: dict[str, Axes] | None = None

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
        # Docs for subplot_mosaic():
        #  https://matplotlib.org/stable/users/explain/axes/arranging_axes.html#variable-widths-or-heights-in-a-grid
        #  https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplot_mosaic.html#matplotlib.pyplot.subplot_mosaic
        self.fig, self.axes = plt.subplot_mosaic(
            # fmt: off
            [
                # 2 rows, 1 col.
                ["day", ],
                ["race", ],
                ["."],  # Just some empty space for the text at the bottom.
            ],
            # fmt: on
            gridspec_kw=dict(
                # The relative sizes of the subplots.
                width_ratios=[1],
                height_ratios=[1, 0.7, 0.1],
            ),
            figsize=(7, 6),
            layout="constrained",
        )

        self._plot_day()
        self._plot_day_annotations()
        self._plot_race()
        self._plot_race_annotations()

        self.fig.suptitle(TITLE)
        # Footer note.
        plt.figtext(
            0.01,
            0.01,
            "Safe glucose range: 70-180 mg/dL",
            # wrap=True,
            # horizontalalignment="center",
            fontsize=9,
            style="italic",
        )

        path = CURR_DIR / f"{Path(__file__).stem}.png"
        plt.savefig(path)
        print(path.resolve())

    def _plot_day(self):
        self.axes["day"].plot(
            self.glucose.index,
            self.glucose.glucose,
            # label="HR",
            color=COL_DARK_BLUE,
            alpha=0.6,
            linewidth=2.5,
        )
        self.axes["day"].set_ylabel("Glucose [mg/dL]")

        # formatter = mpl.dates.ConciseDateFormatter(
        #     self.axes["day"].xaxis.get_major_locator()
        # )
        # %-H means hour without zero-padding.
        formatter = mpl.dates.DateFormatter("%-H:%M")
        self.axes["day"].xaxis.set_major_formatter(formatter)
        # Force y to use only integers.
        self.axes["race"].yaxis.get_major_locator().set_params(integer=True)

        # Highlight the RACE time range.
        self.axes["day"].axvspan(
            np.datetime64(RACE_START_DATE_STR),
            np.datetime64(RACE_END_DATE_STR),
            color="red",
            alpha=0.2,
        )
        self.axes["day"].annotate(
            "RACE\n   ⬇",
            (np.datetime64(RACE_START_DATE_STR), self.axes["day"].get_ylim()[0]),
            xytext=(0.8, 0.5),
            textcoords="offset fontsize",
            color=COL_DARK_RED,
            alpha=0.9,
            fontsize=8,
            fontweight="bold",
        )
        # Draw horizontal line at 120 mg/dL.
        self.axes["day"].axhline(
            y=120,
            color=COL_DARK_GRAY,
            alpha=0.2,
            linestyle="--",
            linewidth=1,
        )

    def _plot_race(self):
        # Adding 5 minutes to the race interval, so as to show how the glucose was in
        #  5 minutes before and after the race.
        race_end_date_plus_5_mins_str = (
            RACE_END_DATE + timedelta(minutes=5)
        ).isoformat()
        race_start_date_minus_5_mins_str = (
            RACE_START_DATE - timedelta(minutes=5)
        ).isoformat()
        race_data = self.glucose.loc[
            race_start_date_minus_5_mins_str:race_end_date_plus_5_mins_str
        ]

        self.axes["race"].plot(
            race_data.index,
            race_data.glucose,
            # label="HR",
            color=COL_DARK_RED,
            alpha=0.6,
            linewidth=2.5,
        )
        self.axes["race"].set_ylabel("Glucose [mg/dL]")

        # formatter = mpl.dates.ConciseDateFormatter(
        #     self.axes["race"].xaxis.get_major_locator()
        # )
        # %-H means hour without zero-padding.
        formatter = mpl.dates.DateFormatter("%-H:%M")
        self.axes["race"].xaxis.set_major_formatter(formatter)
        self.axes["race"].yaxis.get_major_locator().set_params(integer=True)
        # Force y to use only integers.
        self.axes["race"].yaxis.get_major_locator().set_params(integer=True)

        # Draw horizontal line at 120 mg/dL.
        if max(race_data.glucose) >= 120:
            self.axes["race"].axhline(
                y=120,
                color=COL_DARK_GRAY,
                alpha=0.2,
                linestyle="--",
                linewidth=1,
            )

    def _plot_day_annotations(self):
        line_col = COL_DARK_BLUE
        text_col = COL_DARK_BLUE
        line_alpha = 0.5
        text_alpha = 0.8
        ax = self.axes["day"]

        for annotation in DAY_ANNOTATIONS:
            x_ts = np.datetime64(annotation["ts"])
            ax.axvline(
                x=x_ts,
                color=line_col,
                alpha=line_alpha,
                linestyle=":",
            )
            # Text annotation.
            _ = 1 if annotation["is_y_top_pos"] else 0
            ax.annotate(
                annotation["text"],
                (x_ts, ax.get_ylim()[_]),
                xytext=(annotation["x_offset"], annotation["y_offset"]),
                textcoords="offset fontsize",
                color=text_col,
                alpha=text_alpha,
                fontsize=8,
                fontweight="bold",
            )

    def _plot_race_annotations(self):
        line_col = COL_DARK_RED
        text_col = COL_DARK_RED
        line_alpha = 0.5
        text_alpha = 1
        ax = self.axes["race"]

        for annotation in RACE_ANNOTATIONS:
            x_ts = np.datetime64(annotation["ts"])
            ax.axvline(
                x=x_ts,
                color=line_col,
                alpha=line_alpha,
                linestyle=":",
            )
            # Text annotation.
            _ = 1 if annotation["is_y_top_pos"] else 0
            ax.annotate(
                annotation["text"],
                (x_ts, ax.get_ylim()[_]),
                xytext=(annotation["x_offset"], annotation["y_offset"]),
                textcoords="offset fontsize",
                color=text_col,
                alpha=text_alpha,
                fontsize=8,
                fontweight="bold",
            )


if __name__ == "__main__":
    print("START")
    main()
    print("END")
