from math import floor

import numpy as np
from matplotlib.axes import Axes


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

    def _ydata_for_barh(
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

    def _bar_height_for_barh(self, cur_bar_index: int, n_bars_per_group: int) -> float:
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

    def _fix_overlapping_bar_labels(self, axes: list[Axes]):
        """
        Fix overlapping bar labels. Bar labels are printed to the right of each bar,
         for instance for the HR avg and max, pace avg and max. In some cases, the
         avg and max values are close and the bar labels overlaps. This method
         is meant to fix this issue.

        Screenshot: fix-overlapping-bar-labels.png

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


class BasePlotException(Exception):
    pass
