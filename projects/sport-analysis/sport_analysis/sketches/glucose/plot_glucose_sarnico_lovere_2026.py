"""
Usage:
    $ poetry run python sport_analysis/sketches/glucose/plot_glucose_sarnico_lovere_2026.py
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
CSV_FILE = CURR_DIR / "2026.04.28 data.csv"
EVENT_DATE = date(2026, 4, 26)
RACE_START_DATE_STR = "2026-04-26T09:30:00"
RACE_END_DATE_STR = "2026-04-26T11:25:30"
TITLE = "Sarnico Lovere Run 26/4/2026"


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

    def _plot_race(self):
        # Adding 5 minutes to the end of the race, so as to show how the glucose was in
        #  5 minutes after the race.
        race_end_date_plus_5_mins_str = (
            datetime_utils.iso_string_to_datetime("2026-04-26T11:25:30")
            + timedelta(minutes=5)
        ).isoformat()
        race_data = self.glucose.loc[RACE_START_DATE_STR:race_end_date_plus_5_mins_str]

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

    def _plot_day_annotations(self):
        line_col = COL_DARK_BLUE
        text_col = COL_DARK_BLUE
        line_alpha = 0.5
        text_alpha = 0.8
        ax = self.axes["day"]

        ## Wake up.
        # Vertical line.
        x_ts = np.datetime64("2026-04-26T05:00:00")
        ax.axvline(
            x=x_ts,
            color=line_col,
            alpha=line_alpha,
            linestyle=":",
        )
        # Text annotation.
        ax.annotate(
            f"Wake up",
            (x_ts, ax.get_ylim()[1]),
            xytext=(0, -1.2),
            textcoords="offset fontsize",
            color=text_col,
            alpha=text_alpha,
            fontsize=8,
            fontweight="bold",
        )

        ## Breakfast.
        # Vertical line.
        x_ts = np.datetime64("2026-04-26T05:30:00")
        ax.axvline(
            x=x_ts,
            color=line_col,
            alpha=line_alpha,
            linestyle=":",
        )
        # Text annotation.
        ax.annotate(
            f"Milk,\nwhole gr. oatmeal,\nrusks,\ncoffee",
            (x_ts, ax.get_ylim()[1]),
            xytext=(0, -6),
            textcoords="offset fontsize",
            color=text_col,
            alpha=text_alpha,
            fontsize=8,
            fontweight="bold",
        )

        ## Pane e burro arachidi.
        # Vertical line.
        x_ts = np.datetime64("2026-04-26T07:30:00")
        ax.axvline(
            x=x_ts,
            color=line_col,
            alpha=line_alpha,
            linestyle=":",
        )
        # Text annotation.
        ax.annotate(
            f"Bread,\npeanut butt.",
            (x_ts, ax.get_ylim()[1]),
            xytext=(0, -9),
            textcoords="offset fontsize",
            color=text_col,
            alpha=text_alpha,
            fontsize=8,
            fontweight="bold",
        )

        ## Junk after race.
        # Vertical line.
        x_ts = np.datetime64("2026-04-26T11:30:00")
        ax.axvline(
            x=x_ts,
            color=line_col,
            alpha=line_alpha,
            linestyle=":",
        )
        # Text annotation.
        ax.annotate(
            f"Cookies,\nand junk",
            (x_ts, ax.get_ylim()[1]),
            xytext=(0, -2.2),
            textcoords="offset fontsize",
            color=text_col,
            alpha=text_alpha,
            fontsize=8,
            fontweight="bold",
        )

        ## Lunch.
        # Vertical line.
        x_ts = np.datetime64("2026-04-26T14:00:00")
        ax.axvline(
            x=x_ts,
            color=line_col,
            alpha=line_alpha,
            linestyle=":",
        )
        # Text annotation.
        ax.annotate(
            f"Rice,\nstracchino,\nbread,\nsalad,\nhummus,\napple",
            (x_ts, ax.get_ylim()[1]),
            xytext=(0, -9),
            textcoords="offset fontsize",
            color=text_col,
            alpha=text_alpha,
            fontsize=8,
            fontweight="bold",
        )

        ## Frullato.
        # Vertical line.
        x_ts = np.datetime64("2026-04-26T18:16:00")
        ax.axvline(
            x=x_ts,
            color=line_col,
            alpha=line_alpha,
            linestyle=":",
        )
        # Text annotation.
        ax.annotate(
            f"Smoothie w/ banana,\nstrawberries,\nblueberries,\nwhole gr. oatmeal,\nalmonds,\nkefir,\nmilk",
            (x_ts, ax.get_ylim()[1]),
            xytext=(0, -7.5),
            textcoords="offset fontsize",
            color=text_col,
            alpha=text_alpha,
            fontsize=8,
            fontweight="bold",
        )

        ## Dinner.
        # Vertical line.
        x_ts = np.datetime64("2026-04-26T20:00:00")
        ax.axvline(
            x=x_ts,
            color=line_col,
            alpha=line_alpha,
            linestyle=":",
        )
        # Text annotation.
        ax.annotate(
            "Balck rice,\negg,\nshrimps,\npeas,\nbread,\nchicken,\nsalad",
            (x_ts, ax.get_ylim()[1]),
            xytext=(0, -15.7),
            textcoords="offset fontsize",
            color=text_col,
            alpha=text_alpha,
            fontsize=8,
            fontweight="bold",
        )

        ## High glucose during night.
        # Text annotation.
        ax.annotate(
            "Slept poorly and felt\nbloated, glucose was\nhigh (~80 flat usually),\nprobably due to the\ncarbs load at dinner",
            (np.datetime64("2026-04-26T00:00:00"), 110),
            xytext=(-2, 0),
            textcoords="offset fontsize",
            # color=text_col,
            alpha=text_alpha,
            fontsize=8.2,
            # fontweight="bold",
            style="italic",
        )

    def _plot_race_annotations(self):
        line_col = COL_DARK_RED
        text_col = COL_DARK_RED
        line_alpha = 0.5
        text_alpha = 1
        ax = self.axes["race"]

        ## Gel 30g pre-gara.
        # Vertical line.
        x_ts = np.datetime64(RACE_START_DATE_STR)
        ax.axvline(
            x=x_ts,
            color=line_col,
            alpha=line_alpha,
            linestyle=":",
        )
        # Text annotation.
        ax.annotate(
            "Gel 30g maltodex,\nhoney,\ncoke,\ncitrulline,\nalanine,\nlemon ju.",
            (x_ts, ax.get_ylim()[1]),
            xytext=(0, -7),
            textcoords="offset fontsize",
            color=text_col,
            alpha=text_alpha,
            fontsize=8,
            fontweight="bold",
        )

        ## Gel 30g dopo 1 ora.
        # Vertical line.
        x_ts = np.datetime64("2026-04-26T10:30:00")
        ax.axvline(
            x=x_ts,
            color=line_col,
            alpha=line_alpha,
            linestyle=":",
        )
        # Text annotation.
        ax.annotate(
            "Gel 30g maltodex,\nhoney,\ncoke,\nelectrolytes,\nlemon ju.",
            (x_ts, ax.get_ylim()[1]),
            xytext=(0, -6),
            textcoords="offset fontsize",
            color=text_col,
            alpha=text_alpha,
            fontsize=8,
            fontweight="bold",
        )

        ## Gel 20g al km 17.
        # Vertical line.
        x_ts = np.datetime64("2026-04-26T10:47:00")
        ax.axvline(
            x=x_ts,
            color=line_col,
            alpha=line_alpha,
            linestyle=":",
        )
        # Text annotation.
        ax.annotate(
            "Gel 20g maltodex,\nhoney,\ncoke,\nelectrolytes,\nlemon ju.",
            (x_ts, ax.get_ylim()[1]),
            xytext=(0, -12.5),
            textcoords="offset fontsize",
            color=text_col,
            alpha=text_alpha,
            fontsize=8,
            fontweight="bold",
        )

        ## Gel 10g al km 21.
        # Vertical line.
        x_ts = np.datetime64("2026-04-26T11:07:00")
        ax.axvline(
            x=x_ts,
            color=line_col,
            alpha=line_alpha,
            linestyle=":",
        )
        # Text annotation.
        ax.annotate(
            "Gel 10g maltodex,\nhoney,\ncoke,\nelectrolytes,\nlemon ju.",
            (x_ts, ax.get_ylim()[1]),
            xytext=(0, -6),
            textcoords="offset fontsize",
            color=text_col,
            alpha=text_alpha,
            fontsize=8,
            fontweight="bold",
        )

        ## Gels effect.
        # Text annotation.
        ax.annotate(
            "The 1st gel (right before start)\nworked great. The next ones\nkicked in too late. Move 2nd\ngel to 30 mins in.",
            (np.datetime64("2026-04-26T10:00:00"), ax.get_ylim()[0]),
            xytext=(-3, 0.8),
            textcoords="offset fontsize",
            # color=text_col,
            alpha=text_alpha,
            fontsize=8.2,
            # fontweight="bold",
            style="italic",
        )


if __name__ == "__main__":
    print("START")
    main()
    print("END")
