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
    "PR 20km Adda": "25.9km/h (18 Apr)",
    # "PR Selvino MTB": "0:51 (12 Apr)",
    # "PR Selvino road": "N/A",
    # "PR Stelvio road": "1:56:38 (13 Jul,\n  Re Stelvio Mapei)",
    # TODO find it with:
    #  $ san search-strava --start-date-after 2026-01-01T00:00:00+01:00 --activity-type Ride --distance-range 40000 100000 --no-questions
    "Longest km": "64km (30 Mar,\n  Arenzano)",
    # TODO find it with:
    #  $ san search-strava --start-date-after 2026-01-01T00:00:00+01:00 --activity-type Ride --moving-time-range 120 999 --no-questions
    "Longest mov time": "3:55 (26 Jun,\n  Stelvio Night)",
    # TODO find it with:
    #  $ san search-strava --start-date-after 2026-01-01T00:00:00+01:00 --activity-type Ride --elevation-gain-range 1500 9999 --no-questions
    "Highest elev gain": "1857m (26 Jun,\n  Stelvio Night)",
}

# TODO find it with:
#  $ san search-strava --start-date-after 2026-01-01T00:00:00+01:00 --activity-type Ride --hr-max-range 150 999 --with-hr-band-only --no-questions
HR_MAX = "157 bpm (29 Jun,\n  Val Vertova)"


class RideStats(BaseStats):
    def __init__(self, n_days_in_period: int):
        self.n_days_in_period = n_days_in_period
        self.n_weeks_in_period = n_days_in_period / 7
        self.ride_distance = {
            "<20km": 0,
            "20-50km": 0,
            ">50km": 0,
        }
        self.ride_elevation = {
            "<500m elevation": 0,
            "500-1000m elevation": 0,
            "1000-2000m elevation": 0,
            ">2000m elevation": 0,
        }
        self.activities_count = 0
        self.moving_time_tot = 0
        self.distance_tot = 0
        self.elevation_gain_tot = 0

    def add_activity_summary(self, summary):
        if summary["type"].lower() != "ride":
            return
        self.activities_count += 1
        # name = activity["name"]
        distance = summary["distance"]
        self.distance_tot += distance
        elevation_gain = summary["total_elevation_gain"]
        self.elevation_gain_tot += elevation_gain
        self.moving_time_tot += summary["moving_time"]

        # ride_distance stat: # rides by distance.
        # Split ride by distance.
        if distance <= 19_500:
            key = "<20km"
        elif 19_500 < distance <= 50_500:
            key = "20-50km"
        elif distance > 50_500:
            key = ">50km"
        self.ride_distance[key] += 1

        # ride_elevation stat: # rides by elevation gain.
        # Split ride by elevation.
        if elevation_gain < 500:
            key = "<500m elevation"
        elif 500 <= elevation_gain < 1000:
            key = "500-1000m elevation"
        elif 1000 <= elevation_gain <= 2000:
            key = "1000-2000m elevation"
        elif elevation_gain > 2000:
            key = ">2000m elevation"
        self.ride_elevation[key] += 1

    def finalize_stats(self): ...

    def print_stats(self):
        console.print("[bold on green] > Ride[/]")
        console.print(f"[dim bright_black]TOT rides: {self.activities_count}[/]")
        console.print(
            f"[dim bright_black]TOT distance: {round(self.distance_tot/1000)}km ({round(self.distance_tot / 1000 / self.activities_count)}km per ride)[/]"
        )
        console.print(
            f"[dim bright_black]TOT elevation gain: {round(self.elevation_gain_tot)}m[/]"
        )
        for k, v in self.ride_distance.items():
            if v:
                console.print(f"{k}: {v}")
        for k, v in self.ride_elevation.items():
            if v:
                console.print(f"{k}: {v}")

    def plot(self, ax0: Axes, ax1: Axes):
        self._plot_category(ax0)
        self._plot_text(ax1)

    def _plot_category(self, ax: Axes):
        width = 1
        bottom = 0
        i = 0
        for k, v in self.ride_distance.items():
            if not v:
                continue
            bar = ax.bar(
                "Ride category",
                height=v,
                width=width,
                bottom=bottom,
                color=COLORS_TEAL_TO_RED[i],
                # color=COLORS_TEAL_TO_RED[-1 * (i + 1)],
                # alpha=1,
            )
            bottom += v

            # Use annotate(), instead of bar_label(), so I can better control
            #  the positioning.
            ax.annotate(
                text=f"{k} dist: {v}",
                # Point to annotate: the center of the bar.
                xy=(0.5, bottom - (v / 2)),
                # Position of the text, a tuple made of:
                #  - right margin between the bar and the text, keep it to BAR_MARGIN_R;
                #  - = # text line * -0.5 (eg -1.5 if the text has 3 lines).
                xytext=(BAR_MARGIN_R, -0.5),
                textcoords="offset fontsize",  # Coord system of xytext.
                # color=COL_DARK_RED,
                fontsize=8,
                # fontweight="bold",
            )
            i += 1

        # Add an empty space to divide the bar charts.
        bottom += 10

        for k, v in self.ride_elevation.items():
            if not v:
                continue
            bar = ax.bar(
                "Ride category",
                height=v,
                width=width,
                bottom=bottom,
                # color=COLORS_TEAL_TO_RED[i],
                color=COLORS_TEAL_TO_RED[-1 * (i + 1)],
                # alpha=1,
            )
            bottom += v

            # Use annotate(), instead of bar_label(), so I can better control
            #  the positioning.
            ax.annotate(
                text=f"{k.replace('elevation', 'elev gain')} #{v}",
                # Point to annotate: the center of the bar.
                xy=(0.5, bottom - (v / 2)),
                # Position of the text, a tuple made of:
                #  - right margin between the bar and the text, keep it to BAR_MARGIN_R;
                #  - = # text line * -0.5 (eg -1.5 if the text has 3 lines).
                xytext=(BAR_MARGIN_R, -0.5),
                textcoords="offset fontsize",  # Coord system of xytext.
                # color=COL_DARK_RED,
                fontsize=8,
                # fontweight="bold",
            )
            i += 1

        # Title.
        ax.annotate(
            text="Ride",
            # Point to annotate: the top right of the bar.
            xy=(0.5, bottom),
            # TODO edit to reposition the title.
            # Position of the text, a tuple made of:
            #  - a number big enough to center vertically;
            #  - a number to move it just under the bar.
            xytext=(28, -1),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=9,
            fontweight="bold",
        )

    def _plot_text(self, ax: Axes):
        text = f"#{self.activities_count} activities"
        text += f"\n{round(self.activities_count/self.n_weeks_in_period, 1)} activities / week"
        text += f"\n{datetime_utils.seconds_to_hh_mm(round(self.moving_time_tot/self.n_weeks_in_period))} moving time / week"
        text += f"\n{round(self.distance_tot/1000)} km TOT"
        text += f"\n{round(self.distance_tot/1000/self.activities_count)} km and {datetime_utils.seconds_to_hh_mm(round(self.moving_time_tot/self.activities_count))} / ride avg"
        text += f"\n{round(self.elevation_gain_tot)} m elev gain TOT"
        text += "\n"
        for k, v in PRS.items():
            text += f"\n{k}: {v}"
        text += "\n"
        text += f"\nHR max: {HR_MAX}"
        ax.annotate(
            text=text,
            # Point to annotate: the bottom left of the bar.
            xy=(0.5, 0.5),
            # Position of the text, a tuple made of:
            #  - a number big enough to align vertically under the tile;
            #  - a number to move it just under the title.
            xytext=(-2, -10),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=8,
            # fontweight="bold",
        )
