from math import floor
from statistics import mean

import datetime_utils
import matplotlib as mpl
import numpy as np
from matplotlib.axes import Axes

from ..conf import settings

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


class BasePlot:
    pass


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
        time_stream: list | None = None,
        elevation_stream: list | None = None,
        segment_title: str | None = None,
    ):
        ## Data.
        # Compute HR avg and max.
        hr_avg = mean(hr_stream)
        hr_max = max(hr_stream)
        hr_min = min(hr_stream)

        ## Plot data.
        # Plot HR histogram.
        _n_bins = 10
        axes.hist(
            hr_stream,
            bins=_n_bins,
            weights=1 / len(hr_stream) * np.ones(len(hr_stream)),
            color="red",
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
        axes.set_xlim(right=settings.HR_MAX_EVER_RIDE)
        xticks = list(axes.get_xticks())
        while xticks[-1] > (settings.HR_MAX_EVER_RIDE - 9):
            xticks[:] = xticks[:-1]
        xticks.append(settings.HR_MAX_EVER_RIDE)
        axes.set_xticks(xticks)

        # Force the min x value to be min(), add its tick and ensure
        #  that  there are no ticks too close to it (otherwise their labels overlap).
        axes.set_xlim(left=hr_min)
        while xticks[0] < hr_min or abs(xticks[0] - hr_min) < 9:
            xticks[:] = xticks[1:]
        xticks = [hr_min] + xticks
        axes.set_xticks(xticks)

        axes.xaxis.set_major_formatter(
            mpl.ticker.FuncFormatter(
                # Set ticks label as bpm and as % of HR max ever.
                lambda x, pos: f"{round(x)}\n{round(x*100/settings.HR_MAX_EVER_RIDE)}%"
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

        ## Format.
        # Axes labels.
        axes.set_xlabel(f"Heart rate [bpm, % of max ever {settings.HR_MAX_EVER_RIDE}]")
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
            f"avg\n{round(hr_avg)}\n{round(hr_avg*100/settings.HR_MAX_EVER_RIDE)}%",
            (hr_avg, axes.get_ylim()[1]),
            xytext=(-2.2, -3.2),
            textcoords="offset fontsize",
            color=COL_DARK_RED,
            fontsize=8,
            fontweight="bold",
        )
        axes.annotate(
            f"max\n{round(hr_max)}",
            (hr_max, axes.get_ylim()[1]),
            xytext=(-1.1, -2.2),
            textcoords="offset fontsize",
            color=COL_DARK_RED,
            fontsize=8,
            fontweight="bold",
        )

    def _plot_hr_zones_mixin(
        self,
        axes: Axes,
        hr_stream: list,
        hr_min_ever: int = settings.HR_MIN,
        hr_max_ever: int = settings.HR_MAX_EVER_RUN,
    ):
        ## Data.
        # X data.
        res = np.histogram(
            hr_stream,
            bins=[
                min(hr_stream) if min(hr_stream) < hr_min_ever else hr_min_ever,
                round(hr_max_ever / 100 * 50),
                round(hr_max_ever / 100 * 60),
                round(hr_max_ever / 100 * 70),
                round(hr_max_ever / 100 * 80),
                round(hr_max_ever / 100 * 90),
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

        axes.set_xlim(left=0, right=1)
        axes.set_axis_off()


class BasePlotException(Exception):
    pass
