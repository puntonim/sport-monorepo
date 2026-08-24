from collections import namedtuple
from enum import StrEnum
from functools import lru_cache
from math import floor
from pathlib import Path
from statistics import mean

import datetime_utils
import matplotlib as mpl
import numpy as np
from matplotlib.axes import Axes
from rich import box
from rich.table import Table

from ..base_cli_view import ConsoleAdapter
from ..conf import settings

console = ConsoleAdapter()

COL_HR_MAIN = "red"
COL_PACE_MAIN = "#580F41"  # Plum.

COL_DARK_RED = "#9A2D2D"
COL_DARK_GRAY = "#3B3B3B"
COLS_SECONDARY = (
    ("gray", 0.5),
    ("#7B751D", 0.5),  # Gold.
    ("black", 0.4),
    ("#541d69", 0.5),  # Violet.
    ("#1b5026", 0.4),  # Green.
    ("#1c1c7b", 0.5),  # Blue.
    ("#4c2929", 0.6),  # Brown.
)


class PERCENTILE_TO_DRAW_ENUM(StrEnum):
    P80 = "P80"
    P98 = "P98"


class BasePlot:
    @staticmethod
    def print_activity_urls(
        # `original_activity_id_arg` comes from base_cli_view.ACTIVITY_ID_TYPE.
        original_activity_id_arg: str | tuple[str, int],
        garmin_activity_id,
        activity_txt_to_print="run",
        # strava_activity_id,
    ):
        activity_url_text = f"Garmin {activity_txt_to_print} activity:"
        if isinstance(original_activity_id_arg, tuple):
            # self.garmin_activity_id is a tuple like ("LATEST", 0) or ("LATEST", -3).
            activity_url_text = "LATEST"
            if original_activity_id_arg[1] != 0:
                activity_url_text += str(original_activity_id_arg[1])
            activity_url_text += f" {activity_txt_to_print} found in Garmin:"
        console.print(
            f":link: {activity_url_text} https://connect.garmin.com/app/activity/{garmin_activity_id}"
        )

    @staticmethod
    def print_created_image_path(file_path):
        console.print(
            f"\n:floppy_disk: Created image: [blue underline]{file_path}[/]",
            highlight=False,
        )
        console.print(
            f":open_file_folder: Dir: [blue underline]{Path(file_path).parent}[/]",
            highlight=False,
        )

    @staticmethod
    def print_activity_date(date_str: str):
        console.print(f":calendar: {date_str}\n", highlight=False)


class MixinBarHPlot(BasePlot):
    def __init_vars(self, n_bars_per_group: int):
        """
        Init all vars used in the methods.
        """
        # Compute the size of each bar and the space between them.
        n_secondary_bars = n_bars_per_group - 1
        group_bottom_padding = 0.2  # It's the space between groups.
        # 1 is by definition the height of a whole group.
        self._group_content_height = 1 - group_bottom_padding
        self._bars_bottom_margin = 0.05  # It's the space between bars.
        self._secondary_bar_height = (
            1  # 1 is by definition the height of a whole group.
            - group_bottom_padding
            - n_secondary_bars * self._bars_bottom_margin
        ) / (
            n_secondary_bars + 2  # +2 cause the main bar's height is 2x the secondary.
        )
        self._main_bar_height = self._secondary_bar_height * 2

    def _ydata_for_barh_mixin(
        self, ydata: np.ndarray, cur_bar_index: int, n_bars_per_group: int
    ) -> np.ndarray:
        """
        Return the y data to be used in a horizontal bars plot.
        In a horizontal bars plot there are bar GROUPS, where a group matches a y data.
        For example if we want to display the avg height for 2 groups (males and
         females) then we would have 2 groups (males and females).
        Each bar groups has 1 or more BARS.
        The first bar (index 0) is always the MAIN BAR.
        All the other bars (index 1+) are the SECONDARY BARS.
        Secondary bars have the same height, the main bar has 2x height of sec bars.

        Args:
            ydata: numpy array to be used as y data.
            cur_bar_index: the index of the current bar, starting with 0.
            n_bars_per_group: number of bars in each group.

        Example:
            # Plot main bar.
            bar = plt.barh(
                self._ydata_for_barh(np.arange(len(xdata)), 0, 5),
                xdata,
                self._bar_height_for_barh(0, 5),
                label="2025-03-25",
                color=["tab:red" for _ in range(len(xdata) - 1)] + [COL_DARK_GRAY],
                alpha=0.8,
            )
        """
        self.__init_vars(n_bars_per_group)

        if cur_bar_index == 0:
            return (
                ydata - (self._group_content_height / 2) + (self._main_bar_height / 2)
            )
        return (
            ydata
            - (self._group_content_height / 2)
            + self._main_bar_height
            + (self._bars_bottom_margin + self._secondary_bar_height)
            * (cur_bar_index - 1)
            + self._bars_bottom_margin
            + self._secondary_bar_height / 2
        )

    def _bar_height_for_barh_mixin(
        self, cur_bar_index: int, n_bars_per_group: int
    ) -> float:
        """
        Return the bar height to be used in a horizontal bars plot.
        In a horizontal bars plot there are bar GROUPS, where a group matches a y data.
        For example if we want to display the avg height for 2 groups (males and
         females) then we would have 2 groups.
        Each bar groups has 1 or more BARS.
        The first bar (index 0) is always the MAIN BAR.
        All the other bars (index 1+) are the SECONDARY BARS.
        Secondary bars have the same height, the main bar has 2x height of sec bars.

        Args:
            cur_bar_index: the index of the current bar, starting with 0.
            n_bars_per_group: number of bars in each group.

        Example:
            # Plot the 3rd secondary bar.
            bar = plt.barh(
                self._ydata_for_barh(np.arange(len(xdata)), 3, 5),
                xdata,
                self._bar_height_for_barh(3, 5),
                label="2025-03-25",
                color=["tab:red" for _ in range(len(xdata) - 1)] + [COL_DARK_GRAY],
                alpha=0.8,
            )
        """
        self.__init_vars(n_bars_per_group)

        if cur_bar_index == 0:
            return self._main_bar_height
        return self._secondary_bar_height

    def _fix_overlapping_bar_labels_mixin(self, axes: list[Axes]):
        """
        Fix overlapping bar labels. Bar labels are printed to the right of each bar,
         for instance for the HR avg and max, pace avg and max. In some cases, the
         avg and max values are close and the bar labels overlaps. This method
         is meant to fix this issue.

        Screenshot: docs/fix-overlapping-bar-labels.png

        Note: invoke this method as late as possible, as the figure changes every
         time you add new things, and so the position of the bar labels also changes.
        """
        for a in axes:
            a: Axes

            # Count the number of bar groups, which is = integers in the y-axis, as
            #  bar groups are centered on every integer in the y-axis.
            n_bar_groups = floor(a.get_ylim()[0] - a.get_ylim()[1])  # 7

            # Possible BUG: this only works if no other text or annotation was
            #  added, apart from the bar labels. And if each bar in a group has
            #  2 labels: avg and max.
            #  Note that bar labels are just regular Text got via Axes.texts.
            for j in range(0, len(a.texts), 2):
                # Get all the bar labels for the avg and max values.
                max_bar_lbls = a.texts[
                    j * n_bar_groups : j * n_bar_groups + n_bar_groups
                ]
                avg_bar_lbls = a.texts[
                    j * n_bar_groups
                    + n_bar_groups : j * n_bar_groups
                    + (n_bar_groups * 2)
                ]
                for i in range(len(avg_bar_lbls)):
                    # If the bar labels overlaps, then fix them.
                    if (
                        avg_bar_lbls[i]
                        .get_window_extent()
                        .overlaps(max_bar_lbls[i].get_window_extent())
                    ):
                        avg_bar_lbls[i].set_text(
                            avg_bar_lbls[i].get_text()
                            + "-"
                            + max_bar_lbls[i].get_text()
                        )
                        max_bar_lbls[i].set_text("")


class MixinHrPlot(BasePlot):
    def _plot_hr_histogram_mixin(
        self,
        axes: Axes,
        hr_stream: list,
        secondary_hr_streams: list[list] | None = None,
        hr_min_ever: int = settings.HR_MIN,
        hr_max_ever: int = settings.HR_MAX_EVER_RUN,
        elevation_stream: list | None = None,
        time_stream: list | None = None,
        percentile_to_draw: PERCENTILE_TO_DRAW_ENUM | str | None = None,
        segment_title: str | None = None,
    ):
        """
        Plot the HR histogram.
        The HR stream can be a segment.
        Optionally, plot also secondary HR streams from other activities to compare.
        Optionally, plot also elevation over time.

        Args:
            axes: the Axes.
            hr_stream: the HR stream; it can be a segment like:
             response.get_heartrate_stream(
                do_remove_none_values=False,
                segment_start_meters=0,
                segment_end_meters=21110,
            )
            secondary_hr_streams: optional, secondary HR streams from other activities
             to compare.
            hr_max_ever: the max HR ever recorded for this type of activity.
            elevation_stream: optional, to plot also elevation over time.
            time_stream: optional, to plot also elevation over time.
            percentile_to_draw: either P80 or P98 to draw as vertical line on the
             histogram. Note that both percentiles are always written as text under the
             histogram.
            segment_title: optional, if the hr_stream is a segment then you can
             add a title to highlight that.
        """
        ## MAIN activity.
        ## Data.
        # Compute HR avg and max.
        hr_avg = mean(hr_stream)
        hr_max = max(hr_stream)
        hr_min = min(hr_stream)
        hr_min_all_activities = hr_min

        ## Plot data.
        # Plot HR histogram.
        _n_bins = 50
        axes.hist(
            hr_stream,
            bins=_n_bins,
            weights=1 / len(hr_stream) * np.ones(len(hr_stream)),
            color=COL_HR_MAIN,
            alpha=0.6,
        )

        if elevation_stream and time_stream:
            # Plot Elevation over time.
            # Create a new axes that shares the x-axis.
            a1 = axes.twinx()
            # Create a new axes that shares the y-axis.
            a2 = a1.twiny()
            a2.plot(
                time_stream,
                elevation_stream,
                color="gray",
                alpha=0.2,
                linewidth=0,
                linestyle="-",
                # marker=".",
                # label="Elevation",
            )
            a2.fill_between(
                x=time_stream,
                y1=elevation_stream,
                color="gray",
                alpha=0.1,
            )

        ## Format axes.
        # Ticks and labels.
        axes.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(xmax=1, decimals=0))
        axes.yaxis.grid(color="gray", alpha=0.2, linestyle="--")

        # Force the max x value to be HR_MAX_EVER_RIDE, add its tick and ensure that
        #  there are no ticks too close to it (otherwise their labels overlap).
        axes.set_xlim(right=hr_max_ever)
        xticks = list(axes.get_xticks())
        while xticks[-1] > (hr_max_ever - 9):
            xticks[:] = xticks[:-1]
        xticks.append(hr_max_ever)
        axes.set_xticks(xticks)

        axes.xaxis.set_major_formatter(
            mpl.ticker.FuncFormatter(
                # Set ticks label as bpm and as % of HR max ever.
                lambda x, pos: f"{round(x)}\n{round(x*100/hr_max_ever)}%"
            )
        )
        if elevation_stream and time_stream:
            a2.xaxis.set_major_formatter(
                mpl.ticker.FuncFormatter(
                    # Set ticks label as hh:mm.
                    lambda x, pos: datetime_utils.seconds_to_hh_mm(
                        x, do_hide_hours_and_mins_if_zero=True
                    )
                )
            )

        ## SECONDARY activities.
        if secondary_hr_streams is None:
            secondary_hr_streams = []
        for i, secondary_hr_stream in enumerate(secondary_hr_streams):
            if not secondary_hr_stream:
                continue

            if min(secondary_hr_stream) < hr_min_all_activities:
                hr_min_all_activities = min(secondary_hr_stream)

            # Plot HR.
            axes.hist(
                secondary_hr_stream,
                bins=_n_bins,
                weights=1
                / len(secondary_hr_stream)
                * np.ones(len(secondary_hr_stream)),
                # color="gray",
                color=COLS_SECONDARY[i][0],
                alpha=COLS_SECONDARY[i][1],
            )

        ## Format.
        # Force the min x value to be hr_min_all_activities, add its tick and ensure
        #  that  there are no ticks too close to it (otherwise their labels overlap).
        axes.set_xlim(left=hr_min_all_activities)
        xticks = list(axes.get_xticks())
        while (
            xticks[0] < hr_min_all_activities
            or abs(xticks[0] - hr_min_all_activities) < 9
        ):
            xticks[:] = xticks[1:]
        xticks = [hr_min_all_activities] + xticks
        axes.set_xticks(xticks)

        # Axes labels.
        axes.set_xlabel(f"Heart rate [bpm, % of max ever {hr_max_ever}]")
        axes.set_ylabel("Frequency")
        if elevation_stream and time_stream:
            a1.set_ylabel("Elevation [m]")

        # Title.
        if segment_title:
            axes.set_title(
                segment_title,
                loc="left",
                x=0.01,
                y=1.0,
                pad=-22,
                style="italic",
                fontsize=9,
                # color=COL_DARK_RED,
            )

        # Draw HR avg vertical line.
        axes.axvline(
            x=hr_avg,
            color=COL_DARK_RED,
            alpha=0.5,
            linestyle=":",
        )
        # Write text annotation for HR avg and max.
        axes.annotate(
            f"avg {round(hr_avg)}\n{round(hr_avg*100/hr_max_ever)}% max",
            (hr_avg, axes.get_ylim()[1]),
            xytext=(0, -2.2),
            textcoords="offset fontsize",
            color=COL_DARK_RED,
            fontsize=8,
            fontweight="bold",
            horizontalalignment="right",
        )
        axes.annotate(
            f"max\n{round(hr_max)}",
            (hr_max, axes.get_ylim()[1]),
            xytext=(0, -2.2),
            textcoords="offset fontsize",
            color=COL_DARK_RED,
            fontsize=8,
            fontweight="bold",
            horizontalalignment="center",
        )

        # Draw P80 vertical line.
        # With Pandas (lighter than numpy).
        # df = pd.DataFrame(hr_stream, columns=["HR"])
        # percentile80 = df["HR"].quantile(0.80)
        # With numpy (heavier than Pandas).
        p80_bpm = round(np.percentile(hr_stream, 80))
        p98_bpm = round(np.percentile(hr_stream, 98))
        # Vertical line for P80.
        # Note: draw either P80 or P98 as there isn't enough room for both.
        if percentile_to_draw:
            if percentile_to_draw.upper() == PERCENTILE_TO_DRAW_ENUM.P80:
                axes.axvline(
                    x=p80_bpm,
                    color=COL_DARK_RED,
                    alpha=0.5,
                    linestyle=":",
                )
                axes.annotate(
                    f"P80 {p80_bpm}\n{round(p80_bpm*100/hr_max_ever)}% max",
                    (p80_bpm, axes.get_ylim()[0]),
                    xytext=(0, 0.2),
                    textcoords="offset fontsize",
                    color=COL_DARK_RED,
                    fontsize=8,
                    fontweight="bold",
                    horizontalalignment="left",
                )
            # Vertical line for P98.
            # Note: draw either P80 or P98 as there isn't enough room for both.
            elif percentile_to_draw.upper() == PERCENTILE_TO_DRAW_ENUM.P98:
                axes.axvline(
                    x=p98_bpm,
                    color=COL_DARK_RED,
                    alpha=0.5,
                    linestyle=":",
                )
                axes.annotate(
                    f"P98 {p98_bpm}\n{round(p98_bpm*100/hr_max_ever)}% max",
                    (p98_bpm, axes.get_ylim()[0]),
                    xytext=(0, 0.2),
                    textcoords="offset fontsize",
                    color=COL_DARK_RED,
                    fontsize=8,
                    fontweight="bold",
                    horizontalalignment="left",
                )

        # P80 and P98 text.
        p80text = _make_percentile_text(80, p80_bpm, hr_max=hr_max_ever)
        console.print(
            p80text.plain_txt.replace("P80", ":yellow_heart: [bold red]P80[/]")
        )
        p98text = _make_percentile_text(98, p98_bpm, hr_max=hr_max_ever)
        console.print(
            p98text.plain_txt.replace("P98", ":yellow_heart: [bold red]P98[/]")
        )
        axes.annotate(
            p80text.math_text,
            ((axes.get_xlim()[0] + axes.get_xlim()[1]) / 2, axes.get_ylim()[0]),
            xytext=(0, -6.2),
            textcoords="offset fontsize",
            color=COL_DARK_RED,
            # alpha=0.8,
            fontsize=9,
            # fontweight="bold",
            style="italic",
            horizontalalignment="center",
        )
        axes.annotate(
            p98text.math_text,
            ((axes.get_xlim()[0] + axes.get_xlim()[1]) / 2, axes.get_ylim()[0]),
            xytext=(0, -7.4),
            textcoords="offset fontsize",
            color=COL_DARK_RED,
            # alpha=0.8,
            fontsize=9,
            # fontweight="bold",
            style="italic",
            horizontalalignment="center",
        )

        ## Draw HR zones as gray background areas.
        # Z0.
        hr_min = axes.get_xlim()[0]
        z0_x0, z0_x1 = _get_bpm_range_for_hr_zone(0, hr_min, hr_max_ever)
        axes.axvspan(
            z0_x0,
            z0_x1,
            color="grey",
            alpha=0.2,
        )
        if z0_x1 - axes.get_xlim()[0] > 9:
            # Draw "Z0" only if there's enough room.
            axes.annotate(
                "Z0",
                ((z0_x0 + z0_x1) / 2, axes.get_ylim()[1]),
                xytext=(0, 0.2),
                textcoords="offset fontsize",
                color="gray",
                fontsize=8,
                fontweight="bold",
                horizontalalignment="center",
            )
        axes.annotate(
            f"{50}%\n{z0_x1}",
            (z0_x1, axes.get_ylim()[1]),
            xytext=(0, 0.2),
            textcoords="offset fontsize",
            color="gray",
            fontsize=7,
            # fontweight="bold",
            horizontalalignment="center",
        )
        # Z1.
        z1_x0, z1_x1 = _get_bpm_range_for_hr_zone(1, hr_min, hr_max_ever)
        if z1_x1 - axes.get_xlim()[0] > 9:
            # Draw "Z1" only if there's enough room.
            axes.annotate(
                "Z1",
                ((z1_x0 + z1_x1) / 2, axes.get_ylim()[1]),
                xytext=(0, 0.2),
                textcoords="offset fontsize",
                color="gray",
                fontsize=8,
                fontweight="bold",
                horizontalalignment="center",
            )
        axes.annotate(
            f"{60}%\n{z1_x1}",
            (z1_x1, axes.get_ylim()[1]),
            xytext=(0, 0.2),
            textcoords="offset fontsize",
            color="gray",
            fontsize=7,
            # fontweight="bold",
            horizontalalignment="center",
        )
        # Z2.
        z2_x0, z2_x1 = _get_bpm_range_for_hr_zone(2, hr_min, hr_max_ever)
        axes.axvspan(
            z2_x0,
            z2_x1,
            color="grey",
            alpha=0.2,
        )
        if z2_x1 - axes.get_xlim()[0] > 9:
            # Draw "Z2" only if there's enough room.
            axes.annotate(
                "Z2",
                ((z2_x0 + z2_x1) / 2, axes.get_ylim()[1]),
                xytext=(0, 0.2),
                textcoords="offset fontsize",
                color="gray",
                fontsize=8,
                fontweight="bold",
                horizontalalignment="center",
            )
        axes.annotate(
            f"{70}%\n{z2_x1}",
            (z2_x1, axes.get_ylim()[1]),
            xytext=(0, 0.2),
            textcoords="offset fontsize",
            color="gray",
            fontsize=7,
            # fontweight="bold",
            horizontalalignment="center",
        )
        # Z3.
        z3_x0, z3_x1 = _get_bpm_range_for_hr_zone(3, hr_min, hr_max_ever)
        if z3_x1 - axes.get_xlim()[0] > 9:
            # Draw "Z3" only if there's enough room.
            axes.annotate(
                "Z3",
                ((z3_x0 + z3_x1) / 2, axes.get_ylim()[1]),
                xytext=(0, 0.2),
                textcoords="offset fontsize",
                color="gray",
                fontsize=8,
                fontweight="bold",
                horizontalalignment="center",
            )
        axes.annotate(
            f"{80}%\n{z3_x1}",
            (z3_x1, axes.get_ylim()[1]),
            xytext=(0, 0.2),
            textcoords="offset fontsize",
            color="gray",
            fontsize=7,
            # fontweight="bold",
            horizontalalignment="center",
        )
        # Z4.
        z4_x0, z4_x1 = _get_bpm_range_for_hr_zone(4, hr_min, hr_max_ever)
        axes.axvspan(
            z4_x0,
            z4_x1,
            color="grey",
            alpha=0.2,
        )
        if z4_x1 - axes.get_xlim()[0] > 9:
            # Draw "Z4" only if there's enough room.
            axes.annotate(
                "Z4",
                ((z4_x0 + z4_x1) / 2, axes.get_ylim()[1]),
                xytext=(0, 0.2),
                textcoords="offset fontsize",
                color="gray",
                fontsize=8,
                fontweight="bold",
                horizontalalignment="center",
            )
        axes.annotate(
            f"{90}%\n{z4_x1}",
            (z4_x1, axes.get_ylim()[1]),
            xytext=(0, 0.2),
            textcoords="offset fontsize",
            color="gray",
            fontsize=7,
            # fontweight="bold",
            horizontalalignment="center",
        )
        # Z5.
        z5_x0, z5_x1 = _get_bpm_range_for_hr_zone(5, hr_min, hr_max_ever)
        axes.annotate(
            "Z5",
            ((z5_x0 + z5_x1) / 2, axes.get_ylim()[1]),
            xytext=(0, 0.2),
            textcoords="offset fontsize",
            color="gray",
            fontsize=8,
            fontweight="bold",
            horizontalalignment="center",
        )

    def _plot_hr_zones_mixin(
        self,
        axes: Axes,
        hr_stream: list,
        hr_min_ever: int = settings.HR_MIN,
        hr_max_ever: int = settings.HR_MAX_EVER_RUN,
    ):
        """
        Plot the HR zones.

        Args:
            axes: the Axes.
            hr_stream: the HR stream.
            hr_min_ever: the min HR ever recorded (the rest HR).
            hr_max_ever: the max HR ever recorded for this type of activity.
        """
        ## Data.
        # X data.
        hr_min = min(hr_stream) if min(hr_stream) < hr_min_ever else hr_min_ever
        z0_x0, z0_x1 = _get_bpm_range_for_hr_zone(0, hr_min, hr_max_ever)
        z1_x0, z1_x1 = _get_bpm_range_for_hr_zone(1, hr_min, hr_max_ever)
        z2_x0, z2_x1 = _get_bpm_range_for_hr_zone(2, hr_min, hr_max_ever)
        z3_x0, z3_x1 = _get_bpm_range_for_hr_zone(3, hr_min, hr_max_ever)
        z4_x0, z4_x1 = _get_bpm_range_for_hr_zone(4, hr_min, hr_max_ever)
        z5_x0, z5_x1 = _get_bpm_range_for_hr_zone(5, hr_min, hr_max_ever)
        res = np.histogram(
            hr_stream,
            bins=[
                z0_x0,
                z1_x0,
                z2_x0,
                z3_x0,
                z4_x0,
                z5_x0,
                hr_max_ever,
            ],
            weights=1 / len(hr_stream) * np.ones(len(hr_stream)),
        )
        xdata_hr_zones_perc = res[0]

        ## Plot data and format.
        colors = [
            "#a6a6a6",  # Gray.
            "#e5f49c",  # Very light green.
            "#a0d669",  # Light green.
            "#3eaa59",  # Green.
            "#fba85e",  # Orange,
            "#e54d35",  # Red.
        ]
        left = 0

        # Prepare the HR zones table to be printed to the console.
        table = Table(
            # Print all emoji with: `python -m rich.emoji`.
            title=":black_heart: HR zones",
            title_style="bold black on red",
            # row_styles=["dim", ""],
            box=box.SIMPLE,
        )
        table.add_column(
            f"[dim]<50%\n{z0_x0}-{z0_x1}[/dim]\nZ0", justify="center", no_wrap=True
        )
        table.add_column(
            f"[dim]50-60%\n{z1_x0}-{z1_x1}[/dim]\nZ1", justify="center", no_wrap=True
        )
        table.add_column(
            f"[dim]60-70%\n{z2_x0}-{z2_x1}[/dim]\nZ2", justify="center", no_wrap=True
        )
        table.add_column(
            f"[dim]70-80%\n{z3_x0}-{z3_x1}[/dim]\nZ3", justify="center", no_wrap=True
        )
        table.add_column(
            f"[dim]80-90%\n{z4_x0}-{z4_x1}[/dim]\nZ4", justify="center", no_wrap=True
        )
        table.add_column(
            f"[dim]≥90%\n{z5_x0}-{z5_x1}[/dim]\nZ5", justify="center", no_wrap=True
        )
        z_perc = []

        for i, xdata_hr_zone_perc in enumerate(xdata_hr_zones_perc):
            bar = axes.barh(
                0,
                xdata_hr_zone_perc,
                left=left,
                color=colors[i],
            )
            left += xdata_hr_zone_perc

            # Print label for zones that are > 10% (if smaller then there is not enough
            #  space).
            if xdata_hr_zone_perc * 100 > 10:
                axes.bar_label(
                    bar,
                    fmt=lambda x: f"Z{i}\n{round(x*100)}%",
                    label_type="center",
                    color="white" if i != 1 else "#828b98",
                    fontsize=8,
                    fontweight="bold",
                )
            z_perc.append(round(xdata_hr_zone_perc * 100))

        txt = f"Time in zones: Z0={z_perc[0]}% Z1={z_perc[1]}% Z2={z_perc[2]}% Z3={z_perc[3]}% Z4={z_perc[4]}% Z5={z_perc[5]}%"
        axes.annotate(
            txt,
            (axes.get_xlim()[0], axes.get_ylim()[0]),
            xytext=(0, -1),
            textcoords="offset fontsize",
            # color="gray",
            fontsize=8,
            # fontweight="bold",
            style="italic",
        )

        # Color in red the 2 highest values in the HR zones table to be printed to the
        #  console.
        for i in sorted(z_perc)[-2:]:
            z_perc[z_perc.index(i)] = f"[red]{i}%[/]"
        z_perc = [f"{x}%" if isinstance(x, int) else x for x in z_perc]
        # Add the single row to the HR zones table to be printed to the console.
        table.add_row(*z_perc)
        console.print(table)

        axes.set_xlim(left=0, right=1)
        axes.set_axis_off()


class BasePlotException(Exception):
    pass


@lru_cache()
def _get_bpm_range_for_hr_zone(
    zone_number: int,
    hr_min: int = settings.HR_MIN,
    hr_max: int = settings.HR_MAX_EVER_RUN,
):
    z1_start_inclusive = round(hr_max / 100 * 50)  # 87 bpm.
    z2_start_inclusive = round(hr_max / 100 * 60)  # 104 bpm.
    z3_start_inclusive = round(hr_max / 100 * 70)  # 122 bpm.
    z4_start_inclusive = round(hr_max / 100 * 80)  # 139 bpm.
    z5_start_inclusive = round(hr_max / 100 * 90)  # 157 bpm.

    ranges = [
        (hr_min, z1_start_inclusive - 1),
        (z1_start_inclusive, z2_start_inclusive - 1),
        (z2_start_inclusive, z3_start_inclusive - 1),
        (z3_start_inclusive, z4_start_inclusive - 1),
        (z4_start_inclusive, z5_start_inclusive - 1),
        (z5_start_inclusive, hr_max),
    ]
    return ranges[zone_number]


PercentileText = namedtuple("PercentileText", ["plain_txt", "math_text"])


def _make_percentile_text(
    percentile_perc: int,  # Eg. 80.
    percentile_bpm: int,  # Eg. 119.
    hr_min: int = settings.HR_MIN,  # Eg. 46.
    hr_max: int = settings.HR_MAX_EVER_RUN,  # Eg. 174.
) -> PercentileText:
    """
    Eg. "P80 125bpm (=Z2+4bpm, =P19 Z3)".
    """
    for zone_num in range(5, -1, -1):
        zone_bpm_range = _get_bpm_range_for_hr_zone(zone_num, hr_min, hr_max)
        if percentile_bpm >= zone_bpm_range[0]:
            break

    # Eg. "72% max HR".
    perc_of_max_txt = f"{round(percentile_bpm * 100 / hr_max)}% max HR"

    # Eg. "Z2+4bpm".
    bpm_diff_left = percentile_bpm - zone_bpm_range[0] + 1
    bpm_diff_right = zone_bpm_range[1] + 1 - percentile_bpm
    if bpm_diff_left < bpm_diff_right:
        bpm_diff_txt = f"Z{zone_num-1}+{bpm_diff_left}bpm"
    else:
        bpm_diff_txt = f"Z{zone_num+1}-{bpm_diff_right}bpm"

    # Eg. "P19 Z3".
    p_in_zone = round(
        (bpm_diff_left - 1) * 100 / (zone_bpm_range[1] - zone_bpm_range[0])
    )
    p_in_zone_txt = f"P{p_in_zone} Z{zone_num}"

    plain_txt = rf"P{percentile_perc} at {percentile_bpm}bpm | {perc_of_max_txt} | {p_in_zone_txt} | {bpm_diff_txt}"
    # Mathtext info: https://matplotlib.org/stable/users/explain/text/mathtext.html.
    math_txt = rf"P$_{{{percentile_perc}}}$ at {percentile_bpm}bpm | {perc_of_max_txt} | P$_{{{p_in_zone}}}$ Z{zone_num} | {bpm_diff_txt}"
    return PercentileText(plain_txt, math_txt)
