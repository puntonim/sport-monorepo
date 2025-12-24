import re
from collections import Counter

import datetime_utils
from matplotlib.axes import Axes

from ...base_cli_view import ConsoleAdapter
from .stats_base import BAR_MARGIN_R, COLORS_TEAL_TO_RED, BaseStats

console = ConsoleAdapter()

PRS = {
    "PR bench press": "105 kg",
    "PR deadlift": "160 kg",
    "PR squat": "110 kg",
    "PR shoulder press": "62 kg",
    "PR pull-up": "40 kg",  # TODO
    "PR pull-up max rep": "15",  # TODO
    # "PR dip": "??? kg",  # TODO
    # "PR dip max rep": "???",  # TODO
}


class WeightTrainingStats(BaseStats):
    def __init__(self, n_days_in_period: int):
        self.n_days_in_period = n_days_in_period
        self.n_weeks_in_period = n_days_in_period / 7
        self.target_counter: dict | Counter = Counter()
        self.activities_count = 0
        self.moving_time_count = 0

    def add_activity_summary(self, summary):
        # target_counter stat: # times I trained that target.
        # Eg. {'calisthenics': 112, 'legs': 44, 'back': 40, 'chest': 35, 'forearms': 33, 'powerlifting': 28, 'triceps': 24, 'biceps': 22, 'shoulders': 14, 'left elbow': 6}
        if summary["type"].lower() != "weighttraining":
            return
        self.activities_count += 1
        self.moving_time_count += summary["moving_time"]
        name = summary["name"]

        # Clean-up the prefix.
        if name.lower().startswith("weight training: "):
            name = name[17:]
        if name.lower().startswith("powerbuilding class: "):
            name = name[21:]

        targets = [x.lower().strip() for x in name.split(",")]

        # Clean-up names.
        for i in range(len(targets)):
            target = targets[i]

            # "powerlifting class" -> "powerlifting".
            if "powerlifting" in target:
                targets[i] = "powerlifting"
            # "calisthenics class" -> "calisthenics".
            elif "calisthenics" in target:
                targets[i] = "calisthenics"
            # "pr bench press: 105 kg💪🏆" -> "powerlifting".
            elif "bench press" in target:
                targets[i] = "powerlifting"
            # "ring muscle-up progression day #10" -> "calisthenics".
            elif target.startswith("ring muscle-up progression"):
                targets[i] = "calisthenics"
            # "triceps 🦠" -> "triceps".
            elif target.endswith(" 🦠"):
                targets[i] = target[:-2]
            # "left elbow isometrics" -> "left elbow".
            elif re.match(r"^left elbow .*$", target):
                targets[i] = "left elbow"
            # "legs isometrics" -> "legs".
            elif re.match(r"^legs .*$", target):
                targets[i] = "legs"
            # "chest (push&pull party 🎉)" -> "chest".
            elif res := re.match(r"^(.*) \(.*\)$", target):
                targets[i] = res.group(1)

        self.target_counter.update(targets)

    def finalize_stats(self):
        # Sort target_counter.
        self.target_counter = dict(
            sorted(self.target_counter.items(), key=lambda item: item[1], reverse=True)
        )

    def print_stats(self):
        console.print("[bold on green] > Weight training target[/]")
        activities_count = sum(self.target_counter.values())
        for k, v in self.target_counter.items():
            console.print(f"{k}: {v} ({round(v*100/activities_count)}%)")

    def plot(self, ax0: Axes, ax1: Axes):
        self._plot_target(ax0)
        self._plot_text(ax1)

    def _plot_target(self, ax: Axes):
        width = 1
        bottom = 0
        i = 0
        remaining_labels = list()
        for k, v in self.target_counter.items():
            bar = ax.bar(
                "Target",
                height=v,
                width=width,
                bottom=bottom,
                color=COLORS_TEAL_TO_RED[-1 * (i + 1)],
                # alpha=1,
            )
            bottom += v

            # Show only the first 9 labels, otherwise they overlap. We will show the
            #  remaining labels in a separate box.
            text = f"{k} #{v}"
            if i >= 9:
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
                xytext=(BAR_MARGIN_R, -0.3),
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
            xytext=(BAR_MARGIN_R, 0),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=8,
            # fontweight="bold",
        )
        # Title.
        ax.annotate(
            text="Weight Training",
            # Point to annotate: the top right of the bar.
            xy=(0.5, bottom),
            # Position of the text, a tuple made of:
            #  - a number big enough to center vertically;
            #  - a number to move it just under the bar.
            xytext=(12.3, -0.5),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=9,
            fontweight="bold",
        )

    def _plot_text(self, ax: Axes):
        text = f"#{self.activities_count} activities"
        text += f"\n{round(self.activities_count/self.n_weeks_in_period, 1)} activities / week"
        text += f"\n{datetime_utils.seconds_to_hh_mm(round(self.moving_time_count / self.activities_count))} time / activity"
        text += f"\n{datetime_utils.seconds_to_hh_mm(round(self.moving_time_count / self.n_weeks_in_period))} time / week"
        text += "\n"
        for k, v in PRS.items():
            text += f"\n{k}: {v}"
        ax.annotate(
            text=text,
            # Point to annotate: the bottom left of the bar.
            xy=(0.5, 0.5),
            # Position of the text, a tuple made of:
            #  - a number big enough to align vertically under the tile;
            #  - a number to move it just under the title.
            xytext=(-6.2, -4.6),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=8,
            # fontweight="bold",
        )
