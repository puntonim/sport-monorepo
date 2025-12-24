import re

import datetime_utils
from matplotlib.axes import Axes

from ...base_cli_view import ConsoleAdapter
from .stats_base import BAR_MARGIN_R, COLORS_TEAL_TO_RED, BaseStats

console = ConsoleAdapter()

# TODO manually edit this dictionary. The source is Strava website:
#  - go to the page where you can filter all your activities
#  - and search for the word "PR".
#  - then mind to consider PRs only within the correct date range.
PRS = {
    # "PR 200m": "29.77s (3 Oct)",
    # "PR 300m": "46.73s (16 Oct)",
    "PR 1000m": "3:27 (4 Apr)",
    "PR 5km": "19:11 (22 May, ESET Melegnano)",
    "PR 10km": "40:43 (22 Mar, Monza)",
    "PR HM": "1:29:37 (12 Apr, Due Laghi)",
    # TODO find it with:
    #  $ san search-strava --start-date-after 2026-01-01T00:00:00+01:00 --activity-type Run --distance-range 22000 100000 --no-questions
    "Longest km": "30km (31 May, Cortina-Dobbiaco)",
    # TODO find it with:
    #  $ san search-strava --start-date-after 2026-01-01T00:00:00+01:00 --activity-type Run --moving-time-range 120 999 --no-questions
    "Longest mov time": "2:42 (31 May, Cortina-Dobbiaco)",
    # TODO find it with:
    #  $ san search-strava --start-date-after 2026-01-01T00:00:00+01:00 --activity-type Run --elevation-gain-range 300 9999 --no-questions
    "Highest elev gain": "589m (15 Feb, Teglio Winter Run)",
}

# TODO find it with:
#  $ san search-strava --start-date-after 2026-01-01T00:00:00+01:00 --activity-type Run --hr-max-range 165 999 --with-hr-band-only --no-questions
HR_MAX = "174 bpm (8 Mar, Monza)"


class RunStats(BaseStats):
    def __init__(self, n_days_in_period: int):
        self.n_days_in_period = n_days_in_period
        self.n_weeks_in_period = n_days_in_period / 7
        self.run_type = {
            "interval run 100m": 0,
            "interval run 200m": 0,
            "interval run 300m": 0,
            "interval run 400m": 0,
            "interval run 500m": 0,
            "interval run 600m": 0,
            "interval run 800m": 0,
            "interval run 1000m": 0,
            "interval run 1500m": 0,
            "interval run 2000m": 0,
            "interval run 2500m": 0,
            "interval run 3000m": 0,
            "interval run 4000m": 0,
            "interval run 5000m": 0,
            "run <10km": 0,
            "run 10km": 0,
            "run 10-21km": 0,
            "run HM 21km": 0,
            "run 21-30km": 0,
            "run >30km": 0,
            "trail run <250m elevation": 0,
            "trail run 250-500m elevation": 0,
            "trail run 500-1000m elevation": 0,
            "trail run 1000-1500m elevation": 0,
            "trail run 1500-2000m elevation": 0,
            "trail run >2000m elevation": 0,
        }
        self.activities_count = 0
        self.moving_time_tot = 0
        self.distance_tot = 0
        self.elevation_gain_tot = 0

    def add_activity_summary(self, summary):
        if summary["type"].lower() != "run":
            return
        self.activities_count += 1
        name = summary["name"]
        distance = summary["distance"]
        self.distance_tot += distance
        elevation_gain = summary["total_elevation_gain"]
        self.elevation_gain_tot += elevation_gain
        self.moving_time_tot += summary["moving_time"]

        # run_type stat: # activities by run type, distance, elevation.
        # Split run, trail run, interval run.
        key = "run"
        if summary["sport_type"].lower() == "trailrun":
            key = "trail run"
        elif res := re.match(r"^\d{1,2}x(\d{3,4}m)$", name):
            key = f"interval run {res.group(1)}"

        # Split run by distance and trail run by elevation.
        if key == "run":
            if distance <= 9_500:
                key = "run <10km"
            elif 9_500 < distance <= 10_500:
                key = "run 10km"
            elif 10_500 < distance <= 20_500:
                key = "run 10-21km"
            elif 20_500 < distance <= 21_500:
                key = "run HM 21km"
            elif 21_500 < distance <= 30_500:
                key = "run 21-30km"
            elif distance > 30_500:
                key = "run >30km"
        elif key == "trail run":
            if elevation_gain < 250:
                key = "trail run <250m elevation"
            elif 250 <= elevation_gain < 500:
                key = "trail run 250-500m elevation"
            elif 500 <= elevation_gain < 1000:
                key = "trail run 500-1000m elevation"
            elif 1000 <= elevation_gain < 1500:
                key = "trail run 1000-1500m elevation"
            elif 1500 <= elevation_gain <= 2000:
                key = "trail run 1500-2000m elevation"
            elif elevation_gain > 2000:
                key = "trail run >2000m elevation"

        self.run_type[key] += 1

    def finalize_stats(self): ...

    def print_stats(self):
        console.print("[bold on green] > Run[/]")
        console.print(
            f"[dim bright_black]TOT runs: {self.activities_count} ({round(self.activities_count / self.n_weeks_in_period, 1)} per week)[/]"
        )
        console.print(
            f"[dim bright_black]TOT distance: {round(self.distance_tot/1000)}km ({round(self.distance_tot/1000 / self.n_weeks_in_period)}km per week)[/]"
        )
        console.print(
            f"[dim bright_black]TOT elevation gain: {round(self.elevation_gain_tot)}m[/]"
        )
        for k, v in self.run_type.items():
            if v:
                console.print(f"{k}: {v}")

    def plot(self, ax0: Axes, ax1: Axes):
        self._plot_category(ax0)
        self._plot_text(ax1)

    def _plot_category(self, ax: Axes):
        width = 1
        bottom = 0
        i = 0
        remaining_labels = list()
        for k, v in self.run_type.items():
            if not v:
                continue
            bar = ax.bar(
                "Run category",
                height=v,
                width=width,
                bottom=bottom,
                # color=COLORS_TEAL_TO_RED[i],
                color=COLORS_TEAL_TO_RED[-1 * (i + 1)],
                # alpha=1,
            )
            bottom += v

            # Show only the first few labels, otherwise they overlap. We will show the
            #  remaining labels in a separate box.
            text = f"{k.replace('elevation', 'elev')} #{v}"
            # TODO change this number so the labels at the top do not overlap.
            if i >= 6:
                remaining_labels.append(text)
                text = None
            # Use annotate(), instead of bar_label(), so I can better control
            #  the positioning.
            ypos = bottom - (v / 2)
            # TODO comment out if the 2 labels at the bottom do NOT overlap: it moves
            #  the 2nd label from the bottom a little bit higher to avoid the overlap
            #  with the last.
            if i == 1:
                ypos = bottom + (v / 1.5)
            ax.annotate(
                text=text,
                # Point to annotate: the center of the bar.
                xy=(0.5, ypos),
                # Position of the text, a tuple made of:
                #  - right margin between the bar and the text, keep it to BAR_MARGIN_R;
                #  - = # text line * -0.5 (eg -1.5 if the text has 3 lines).
                xytext=(-3, -0.5),
                textcoords="offset fontsize",  # Coord system of xytext.
                # color=COL_DARK_RED,
                fontsize=8,
                # fontweight="bold",
                horizontalalignment="right",
            )
            i += 1

        # Add the remaining labels.
        ax.annotate(
            text="\n".join(remaining_labels[::-1]),
            # Point to annotate: the center of the bar.
            xy=(0.5, bottom - (v / 2)),
            # Position of the text, a tuple made of:
            #  - right margin between the bar and the text, keep it to BAR_MARGIN_R;
            #  - a number big enough to avoid the overlap.
            xytext=(-3, -1.8),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=8,
            # fontweight="bold",
            horizontalalignment="right",
        )
        # Title.
        ax.annotate(
            text="Run",
            # Point to annotate: the top right of the bar.
            xy=(0.5, bottom),
            # TODO edit to reposition the title.
            # Position of the text, a tuple made of:
            #  - a number big enough to center vertically;
            #  - a number to move it just under the bar.
            xytext=(-3.5, 3),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=9,
            fontweight="bold",
        )

    def _plot_text(self, ax: Axes):
        text = f"#{self.activities_count} activities"
        text += f"\n{round(self.activities_count/self.n_weeks_in_period, 1)} activities / week"
        text += f"\n{datetime_utils.seconds_to_hh_mm(round(self.moving_time_tot/self.activities_count))} moving time / activity"
        text += f"\n{datetime_utils.seconds_to_hh_mm(round(self.moving_time_tot/self.n_weeks_in_period))} moving time / week"
        text += f"\n{round(self.distance_tot/1000)} km TOT"
        text += f"\n{round(self.elevation_gain_tot)} m elevation gain TOT"
        text += "\n"
        for k, v in PRS.items():
            text += f"\n{k}: {v}"
        text += "\n"
        text += f"\nHR max: {HR_MAX}"
        ax.annotate(
            text=text,
            # Point to annotate: the bottom left of the bar.
            xy=(0.5, 0.5),
            # TODO edit to reposition the text.
            # Position of the text, a tuple made of:
            #  - a number big enough to align vertically under the tile;
            #  - a number to move it just under the title.
            xytext=(-13, -7),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=8,
            # fontweight="bold",
        )
