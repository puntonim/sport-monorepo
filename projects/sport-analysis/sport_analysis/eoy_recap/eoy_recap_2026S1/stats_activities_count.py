from collections import Counter, defaultdict
from statistics import mean

import datetime_utils
from matplotlib.axes import Axes

from ...base_cli_view import ConsoleAdapter
from .stats_base import BAR_MARGIN_R, COLORS_TEAL_TO_RED, BaseStats

console = ConsoleAdapter()


class ActivitiesCountStats(BaseStats):
    def __init__(self, n_days_in_period: int):
        self.n_days_in_period = n_days_in_period
        self.n_weeks_in_period = n_days_in_period / 7

        # Eg. {'WeightTraining': 211, 'Run': 60, 'Ride': 37, 'Snowboard': 7, 'Snowshoe': 3, 'Walk': 2, 'NordicSki': 2, 'Hike': 1, 'RockClimbing': 1}
        self.types_counter: dict | Counter = Counter()
        # Eg.
        # {
        #     "WeightTraining": [6263, 5321, ...],
        #     "Ride": [7984, 6788, ...],
        #     "Run": [4340, 4462, ...],
        #     "Snowboard": [8473, 7246, ...],
        #     "Snowshoe": [5183, 6258, 7381],
        #     "NordicSki": [7942, 7776],
        #     "RockClimbing": [10800],
        #     "Walk": [4232, 4494],
        #     "Hike": [2935],
        # }
        self.types_hours: dict = defaultdict(list)
        self.activities_count = 0
        self.time_tot = 0

        # Eg. {0: 63, 1: 249, 2: 36, 3: 1}
        self.n_activities_in_same_day__count__counter: dict | Counter = Counter()
        # Eg.
        # {
        #     "2025-01-10": 3,
        #     "2025-12-09": 2,
        #     "2025-11-20": 2,
        #     "2025-11-05": 1,
        #     ...
        # }
        self._day_str__n_activities__counter = Counter()

    def add_activity_summary(self, summary):
        self.activities_count += 1

        # types_counter stat: # activities by type.
        activity_type = summary["type"]
        self.types_counter.update([activity_type])

        # types_hours stat: # hours by type.
        self.types_hours[activity_type].append(summary["moving_time"])
        self.time_tot += summary["moving_time"]

        # n_activities_in_same_day__count__counter: # days by # activities in the same day.
        day_str = (
            datetime_utils.iso_string_to_datetime(summary["start_date_local"])
            .date()
            .isoformat()
        )
        self._day_str__n_activities__counter.update([day_str])

    def finalize_stats(self):
        # Sort types_counter.
        self.types_counter = dict(
            sorted(self.types_counter.items(), key=lambda item: item[1], reverse=True)
        )

        # Sort types_hours.
        self.types_hours = dict(
            sorted(
                self.types_hours.items(), key=lambda item: sum(item[1]), reverse=True
            )
        )

        # Build n_activities_in_same_day__count__counter and sort it.
        self.n_activities_in_same_day__count__counter.update(
            self._day_str__n_activities__counter.values()
        )
        # Rest days.
        rest_days_count = self.n_days_in_period - sum(
            self.n_activities_in_same_day__count__counter.values()
        )
        self.n_activities_in_same_day__count__counter[0] = rest_days_count
        # Sort n_activities_in_same_day__count__counter.
        self.n_activities_in_same_day__count__counter = dict(
            sorted(
                self.n_activities_in_same_day__count__counter.items(),
                key=lambda item: item[0],
                reverse=False,
            )
        )

    def print_stats(self):
        rest_days_count = self.n_activities_in_same_day__count__counter[0]
        active_days_count = self.n_days_in_period - rest_days_count

        console.print("[bold on green] > Activity types[/]")
        console.print(
            f"[dim bright_black]TOT activities: {self.activities_count}"
            f" in {self.n_days_in_period} days[/]"
        )
        for k, v in self.types_counter.items():
            console.print(f"{k}: {v} ({round(v*100/self.activities_count)}%)")

        console.print("[bold on green] > Duration (moving time)[/]")
        avg_time_per_activity = self.time_tot / self.activities_count
        avg_time_per_active_day = self.time_tot / active_days_count
        avg_time_per_week = self.time_tot / self.n_weeks_in_period
        _ = datetime_utils.seconds_to_hh_mm
        console.print(
            f"[dim bright_black]TOT time: {_(self.time_tot)} ({_(round(avg_time_per_activity))} per activity, {_(round(avg_time_per_active_day))} per active day, {_(round(avg_time_per_week))} per week)[/]"
        )
        for k, v in self.types_hours.items():
            console.print(
                f"{k}{' (elapsed time)' if k == 'WeightTraining' else ''}: {_(sum(v))} (avg {_(round(mean(v)))}, max {_(max(v))}, {round(sum(v)*100/self.time_tot)}%)"
            )

        console.print("[bold on green] > Activities in the same day[/]")
        console.print(
            f"[dim bright_black]rest days: {rest_days_count} days ({round(rest_days_count / self.n_weeks_in_period, 1)} per week)[/]"
        )
        console.print(
            f"[dim bright_black]active days: {active_days_count} days ({round(active_days_count / self.n_weeks_in_period, 1)} per week)[/]"
        )
        for k, v in self.n_activities_in_same_day__count__counter.items():
            if k != 0:
                console.print(
                    f"{k} activit{'y' if k < 2 else 'ies'}: {v} day{'s' if v > 1 else ''} ({round(v/self.n_weeks_in_period, 1)} per week)"
                )

    def plot(self, ax0: Axes, ax1: Axes, ax2: Axes):
        self._plot_activity_types(ax0)
        self._plot_duration(ax1)
        self._plot_daily_freq(ax2)

    def _plot_activity_types(self, ax: Axes):
        width = 1
        bottom = 0
        i = 0
        remaining_labels = list()
        for k, v in self.types_counter.items():
            bar = ax.bar(
                "Activity types",
                height=v,
                width=width,
                bottom=bottom,
                color=COLORS_TEAL_TO_RED[i],
                # alpha=1,
            )
            bottom += v

            # Show only the first 3 labels, otherwise they overlap. We will show the
            #  remaining labels in a separate box.
            text = f"{k}\n#{v} ({round(v*100/self.activities_count)}%)"
            if i >= 3:
                remaining_labels.append(f"{k} #{v}")
                text = None
            # Use annotate(), instead of bar_label(), so I can better control
            #  the positioning.
            ax.annotate(
                text=text,
                # Point to annotate: the center of the bar.
                xy=(0.5, bottom - (v / 2)),
                # Position of the text, a tuple made of:
                #  - right margin between the bar and the text, keep it to BAR_MARGIN_R;
                #  - = # text line * -0.5 (eg -1.5 if the text has 3 lines).
                xytext=(BAR_MARGIN_R, -1),
                textcoords="offset fontsize",  # Coord system of xytext.
                # color=COL_DARK_RED,
                fontsize=8,
                # fontweight="bold",
            )
            i += 1

        # Add the remaining labels.
        ax.annotate(
            text="\n".join(remaining_labels[::-1]),
            # Point to annotate: the center of the bar.
            xy=(0.5, bottom),
            # Position of the text, a tuple made of:
            #  - right margin between the bar and the text, keep it to BAR_MARGIN_R;
            #  - a number big enough to avoid the overlap.
            xytext=(BAR_MARGIN_R, -0.6),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=8,
            # fontweight="bold",
        )
        # Title.
        ax.annotate(
            text="Activity types",
            # Point to annotate: the bottom left of the bar.
            xy=(-0.5, 0),
            # Position of the text, a tuple made of:
            #  - a number big enough to center vertically;
            #  - a number to move it just under the bar.
            xytext=(-1.5, -1),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=9,
            fontweight="bold",
        )
        # Totals.
        ax.annotate(
            text=f"TOT activities:\n  #{self.activities_count} in {self.n_days_in_period} days\n{round(self.activities_count/self.n_weeks_in_period, 1)} activities / week",
            # Point to annotate: the bottom left of the bar.
            xy=(-0.5, 0),
            # Position of the text, a tuple made of:
            #  - a number big enough to align vertically under the tile;
            #  - a number to move it just under the title.
            xytext=(-2.0, -4.3),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=8,
            # fontweight="bold",
        )

    def _plot_duration(self, ax: Axes):
        width = 1
        bottom = 0
        i = 0
        remaining_labels = list()
        _ = datetime_utils.seconds_to_hh_mm
        for k, v in self.types_hours.items():
            sum_v = sum(v)
            bar = ax.bar(
                "Duration (moving time)",
                height=sum_v,
                width=width,
                bottom=bottom,
                color=COLORS_TEAL_TO_RED[i],
                # alpha=1,
            )
            bottom += sum_v

            # Show only the first 3 labels, otherwise they overlap. We will show the
            #  remaining labels in a separate box.
            tot_time = _(sum_v).replace("days", "dd").replace("day", "dd")
            text = k
            text += f"\n{_(round(mean(v)))} avg"
            text += f"\nTOT {tot_time} ({round(sum_v * 100 / self.time_tot)}%)"
            if i >= 3:
                text = None
                remaining_labels.append(f"{k} {_(round(mean(v)))} avg")
            # Use annotate(), instead of bar_label(), so I can better control
            #  the positioning.
            ax.annotate(
                text=text,
                # Point to annotate: the center of the bar.
                xy=(0.5, bottom - (sum_v / 2)),
                # Position of the text, a tuple made of:
                #  - right margin between the bar and the text, keep it to BAR_MARGIN_R;
                #  - = # text line * -0.5 (eg -1.5 if the text has 3 lines).
                xytext=(BAR_MARGIN_R, -1.5),
                textcoords="offset fontsize",  # Coord system of xytext.
                # color=COL_DARK_RED,
                fontsize=8,
                # fontweight="bold",
            )
            i += 1

        # Add the remaining labels.
        ax.annotate(
            text="\n".join(remaining_labels[::-1]),
            # Point to annotate: the center of the bar.
            xy=(0.5, bottom),
            # Position of the text, a tuple made of:
            #  - right margin between the bar and the text, keep it to BAR_MARGIN_R;
            #  - a number big enough to avoid the overlap.
            xytext=(BAR_MARGIN_R, -0.3),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=8,
            # fontweight="bold",
        )
        # Title.
        ax.annotate(
            text="Duration",
            # Point to annotate: the bottom left of the bar.
            xy=(-0.5, 0),
            # Position of the text, a tuple made of:
            #  - a number big enough to center vertically;
            #  - a number to move it just under the bar.
            xytext=(-0.8, -1),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=9,
            fontweight="bold",
        )

        # Totals.
        text = f"TOT time: {_(self.time_tot).replace('days', 'dd')}"
        rest_days_count = self.n_activities_in_same_day__count__counter[0]
        active_days_count = self.n_days_in_period - rest_days_count
        avg_time_per_activity = self.time_tot / self.activities_count
        avg_time_per_active_day = self.time_tot / active_days_count
        avg_time_per_week = self.time_tot / self.n_weeks_in_period
        text += f"\n{_(round(avg_time_per_activity))} per activity"
        text += f"\n{_(round(avg_time_per_active_day))} / active day"
        text += f"\n{_(round(avg_time_per_week))} / week"
        ax.annotate(
            text=text,
            # Point to annotate: the bottom left of the bar.
            xy=(-0.5, 0),
            # Position of the text, a tuple made of:
            #  - a number big enough to align vertically under the tile;
            #  - a number to move it just under the title.
            xytext=(-2.2, -5.35),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=8,
            # fontweight="bold",
        )

    def _plot_daily_freq(self, ax: Axes):
        # Plot n_activities_in_same_day__count__counter.
        width = 1
        bottom = 0
        i = 0
        remaining_labels = list()
        for k, v in self.n_activities_in_same_day__count__counter.items():
            bar = ax.bar(
                "Activities in the same day",
                height=v,
                width=width,
                bottom=bottom,
                color=COLORS_TEAL_TO_RED[i],
                # alpha=1,
            )
            bottom += v

            # Show only the first 3 labels, otherwise they overlap. We will show the
            #  remaining labels in a separate box.
            if k == 0:
                text = f"Rest day\n#{v} ({round(v / self.n_weeks_in_period, 1)}/wk)"
            elif k == 1:
                text = (
                    f"1 activity/dd\n#{v} ({round(v / self.n_weeks_in_period, 1)}/wk)"
                )
            else:
                text = f"{k} activities/dd\n#{v} ({round(v / self.n_weeks_in_period, 1)}/wk)"
            if i >= 3:
                remaining_labels.append(text)
                text = None
            # Use annotate(), instead of bar_label(), so I can better control
            #  the positioning.
            ax.annotate(
                text=text,
                # Point to annotate: the center of the bar.
                xy=(0.5, bottom - (v / 2)),
                # Position of the text, a tuple made of:
                #  - right margin between the bar and the text, keep it to BAR_MARGIN_R;
                #  - = # text line * -0.5 (eg -1.5 if the text has 3 lines).
                xytext=(BAR_MARGIN_R, -1.0),
                textcoords="offset fontsize",  # Coord system of xytext.
                # color=COL_DARK_RED,
                fontsize=8,
                # fontweight="bold",
            )
            i += 1

        # Add the remaining labels.
        if remaining_labels:
            ax.annotate(
                text="\n".join(remaining_labels[::-1]),
                # Point to annotate: the center of the bar.
                xy=(0.5, bottom),
                # Position of the text, a tuple made of:
                #  - right margin between the bar and the text, keep it to BAR_MARGIN_R;
                #  - a number big enough to avoid the overlap.
                xytext=(BAR_MARGIN_R, 0.2),
                textcoords="offset fontsize",  # Coord system of xytext.
                fontsize=8,
                # fontweight="bold",
            )
        # Title.
        ax.annotate(
            text="Daily freq",
            # Point to annotate: the bottom left of the bar.
            xy=(-0.5, 0),
            # Position of the text, a tuple made of:
            #  - a number big enough to center vertically;
            #  - a number to move it just under the bar.
            xytext=(-0.8, -1),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=9,
            fontweight="bold",
        )

        # Totals.
        rest_days_count = self.n_activities_in_same_day__count__counter[0]
        active_days_count = self.n_days_in_period - rest_days_count
        text = f"Active days: #{active_days_count}"
        text += (
            f"\n{round(active_days_count / self.n_weeks_in_period, 1)} active dd / week"
        )
        ax.annotate(
            text=text,
            # Point to annotate: the bottom left of the bar.
            xy=(-0.5, 0),
            # Position of the text, a tuple made of:
            #  - a number big enough to align vertically under the tile;
            #  - a number to move it just under the title.
            xytext=(-2.2, -3.3),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=8,
            # fontweight="bold",
        )
