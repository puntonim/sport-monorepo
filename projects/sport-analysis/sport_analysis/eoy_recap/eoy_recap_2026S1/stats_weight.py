r"""
Plot my weight history, by monthly average.

The file with the weight data `weight.csv` was exported from my scale
 Renpho ES-CS20M.
To extract the weights from the scale see:
 /Volumes/home/Drive/DOCUMENTI-SYNC/IT/WEARABLE,\ FITNESS/Bilancia\ Renpho\ ES-CS20M/EXPORT/How\ to
"""

import csv
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean

import datetime_utils
import numpy as np
import pandas as pd
from matplotlib.axes import Axes

from ...base_cli_view import ConsoleAdapter
from .stats_base import BAR_MARGIN_R, COLORS_TEAL_TO_RED, BaseStats

CURR_DIR = Path(__file__).parent
CSV_FILE = CURR_DIR / "weight.csv"

console = ConsoleAdapter()

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


class WeightStats:
    def __init__(self):
        # Eg: 77.5.
        self.weight_avg_2023: float = None
        self.weight_avg_2024: float = None
        self.weight_avg_2025: float = None
        # TODO add the new year, if necessary.
        # Eg:
        #                weight
        # date
        # 2025-01-01  80.830769
        # 2025-02-01  80.427273
        # 2025-03-01  81.400000
        # 2025-04-01  80.868182
        # 2025-05-01  80.985484
        # 2025-06-01  81.643548
        # 2025-07-01  81.047826
        # 2025-08-01  81.460417
        # 2025-09-01  81.015517
        # 2025-10-01  81.313793
        # 2025-11-01  82.533871
        # 2025-12-01  83.840323
        # TODO rename this and all occurrences, if necessary.
        self.weights_2026S1_df: pd.DataFrame = None

    def _load_weights(self, do_backfill_data: bool = True):
        # Load only the specific columns
        df = pd.read_csv(CSV_FILE, usecols=["Date", "Weight(kg)"])
        df.rename(columns={"Date": "date", "Weight(kg)": "weight"}, inplace=True)
        df["date"] = pd.to_datetime(df["date"])
        # Sort by date ascending.
        df.sort_values(by="date", ascending=True, inplace=True)
        df.set_index("date", inplace=True)

        if do_backfill_data:
            first_date = df.iloc[0].name.to_pydatetime().date()
            d = date(first_date.year, 1, 1)
            while d < first_date:
                df.loc[pd.Timestamp(d)] = None
                d += timedelta(days=1)
            df = df.sort_index()

        return df

    def _aggregate_weight(
        self,
        df: pd.DataFrame,
        start_date: date | None = None,
        end_date: date | None = None,
        months_to_aggregate: int = 1,
    ):
        if not start_date and not end_date:
            raise ValueError("You must provide either or both start_date and end_date")
        if start_date and end_date:
            df = df.loc[start_date:end_date]  # The intervals are inclusive.
        if start_date and not end_date:
            df = df.loc[start_date:]  # The intervals are inclusive.
        if not start_date and end_date:
            df = df.loc[:end_date]  # The intervals are inclusive.

        df = df.resample(f"{months_to_aggregate}MS").mean()
        # Alternative.
        # monthly_avg = (
        #     df.groupby(df["Date"].dt.to_period("M"))["Weight(kg)"].mean().reset_index()
        # )
        # monthly_avg.columns = ["Month", "Average Weight"]
        return df

    def finalize_stats(self):
        df = self._load_weights(do_backfill_data=False)
        self.weight_avg_2023 = float(df["2023-01-01":"2023-12-31"].mean().iloc[0])
        self.weight_avg_2024 = float(df["2024-01-01":"2024-12-31"].mean().iloc[0])
        self.weight_avg_2025 = float(df["2025-01-01":"2025-12-31"].mean().iloc[0])
        # TODO add the new year, if necessary.
        df = self._aggregate_weight(
            df,
            # TODO edit the dates, if necessary.
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30),
            months_to_aggregate=1,
        )
        self.weights_2026S1_df = df

    def print_stats(self):
        console.print("[bold on green] > Weight[/]")
        for day, w in self.weights_2026S1_df.iterrows():
            console.print(f"{str(day)[:7]}: {round(w.weight, 1)} kg avg")

    def plot(self, ax: Axes):
        self._plot_chart(ax)
        self._plot_text(ax)

    def _plot_chart(self, ax: Axes):
        width = 1
        # y = np.array(tuple(self.month__avg_weight.values()))
        # x = np.arange(len(self.month__avg_weight))
        # x_labels = self.month__avg_weight.keys()
        y = self.weights_2026S1_df["weight"]
        x = np.arange(len(self.weights_2026S1_df))
        # TODO edit the months, if necessary.
        x_labels = (
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            # "Jul",
            # "Aug",
            # "Sep",
            # "Oct",
            # "Nov",
            # "Dec",
        )
        rects = ax.bar(
            x,
            height=y,
            width=width,
            color=COLORS_TEAL_TO_RED[0],
            label="Weight",
        )
        ax.set_ylim(bottom=min(y) - 0.3, top=max(y))
        ax.set_xlim(left=-0.5, right=len(x) - 0.5)
        # Write the weight on top of each bar, like "80.8".
        ax.bar_label(
            rects,
            padding=3,
            fmt=lambda x: f"{round(x, 1)}",
            fontsize=8,
        )
        # Switch the axes on otherwise the tick labels (like "Feb, "Mar") are not visible.
        ax.set_axis_on()
        # Add the tick labels like "Jan\n2025", "Feb", etc.
        ax.set_xticks(
            x,
            x_labels,
            fontsize=8,
        )
        # Move the tick labels closer to the axis.
        ax.tick_params(axis="x", which="major", pad=-1)
        # Hide the x ticks.
        for x in ax.xaxis.get_ticklines():
            x.set_visible(False)
        # Hide the y axis.
        ax.yaxis.set_visible(False)
        # Hide all the spines (the lines that compose the chart rectangle, like the borders in Word's tables).
        ax.spines[["top", "bottom", "right", "left"]].set_visible(False)
        # Title.
        ax.annotate(
            text="Body weight",
            # Point to annotate: the top center of the chart.
            xy=(
                (len(self.weights_2026S1_df) / 2) - 2,
                max(self.weights_2026S1_df["weight"]),
            ),
            # TODO edit to reposition the title.
            # Position of the text, a tuple made of:
            #  - a number big enough to center vertically;
            #  - a number to move it just under the bar.
            xytext=(-7, 0),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=9,
            fontweight="bold",
        )

    def _plot_text(self, ax: Axes):
        text = f"2023 mean: {round(self.weight_avg_2023, 1)} kg"
        text += f"\n2024 mean: {round(self.weight_avg_2024, 1)} kg (+{round(self.weight_avg_2024-self.weight_avg_2023, 1)})"
        text += f"\n2025 mean: {round(self.weight_avg_2025, 1)} kg (+{round(self.weight_avg_2025-self.weight_avg_2024, 1)})"
        # TODO add the new year, if necessary.
        # TODO edit this for the new year, if necessary.
        weight_avg_2026S1 = self.weights_2026S1_df.mean().iloc[0]
        text += f"\n2026S1 mean: {round(weight_avg_2026S1, 1)} kg (+{round(weight_avg_2026S1-self.weight_avg_2025, 1)})"
        ax.annotate(
            text=text,
            # Point to annotate: the top center of the chart.
            xy=(
                (len(self.weights_2026S1_df) / 2) - 2,
                max(self.weights_2026S1_df["weight"]),
            ),
            # TODO edit to reposition the text.
            # Position of the text, a tuple made of:
            #  - a number big enough to align vertically under the tile;
            #  - a number to move it just under the title.
            xytext=(6, -9),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=8,
            # fontweight="bold",
            color="white",
        )
