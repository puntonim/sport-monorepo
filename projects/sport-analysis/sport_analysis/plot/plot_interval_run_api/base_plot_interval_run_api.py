from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

import log_utils as logger
import matplotlib.pyplot as plt
import number_utils
import numpy as np
import speed_utils
from garmin_connect_client import ActivitySummaryResponse, ActivityTypedSplitsResponse
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from .. import base_api, base_plot

COL_DARK_RED = "#9A2D2D"
COL_DARK_GRAY = "#3B3B3B"


@dataclass
class CollectedData:
    summary_resp: ActivitySummaryResponse = None
    type_splits_resp: ActivityTypedSplitsResponse = None


# TODO
#  - Consider removing the cadence graph and instead write, in the legend, the cadence
#     avg and max for each activity (like we do for marathons). But mind that the
#     avg and max values should be computed on INTERVAL_ACTIVE splits by reading the
#     averageRunCadence and maxRunCadence, exactly like we do now in the
#     cadence graph for the avg columns.
#    Or we can only have the avg columns for cadence (again, computed on INTERVAL_ACTIVE
#     splits by reading the averageRunCadence and maxRunCadence, exactly like we do now
#     in the cadence graph for the avg columns) in a small chart.


class BasePlotIntervalRunApi(
    ABC, base_api.MixinGarminRequestsApi, base_plot.MixinBarHPlot
):
    """
    Plot charts to support the analysis of an interval run activity performance,
     optionally compared with previous activities.
    """

    # IMP: TO BE DEFINED IN sub-classes. Mind that it's an exact match on activities'
    #  titles.
    DEFAULT_TEXT_TO_SEARCH_FOR_PREVIOUS_ACTIVITIES: str | None = None

    def __init__(
        self,
        garmin_activity_id: int,
        n_previous_activities_to_compare: int = 10,
        text_to_search_for_previous_activities: str | None = None,
        title: str | None = None,
        figure_size: tuple[float, float] | None = None,
        garmin_connect_token_manager: (
            FileGarminConnectTokenManager | FakeTestGarminConnectTokenManager | None
        ) = None,
    ):
        """
        Args:
            garmin_activity_id: id of Garmin activity to analyze.
            n_previous_activities_to_compare: number of previous activities to compare
             to the given activity. They are searched automatically.
            text_to_search_for_previous_activities: text used in the search for
             previous activities to compare. It's an exact match on activities' titles.
            title: figure title.
            figure_size: customize the figure size, eg. (3.0, 5.5).
            garmin_connect_token_manager: use FakeTestGarminConnectTokenManager when
             replaying VCR episodes.
        """
        super().__init__(garmin_connect_token_manager)

        self.n_previous_activities_to_compare = n_previous_activities_to_compare
        self.text_to_search_for_previous_activities = (
            text_to_search_for_previous_activities
            or self.DEFAULT_TEXT_TO_SEARCH_FOR_PREVIOUS_ACTIVITIES
        )
        self.garmin_activity_id = garmin_activity_id
        self.title = title
        self.figure_size = figure_size

        # The store used for Garmin Connect API responses collected for all activities.
        self._s: list[CollectedData] = []

        # Matplotlib axes mosaic. This figure is made of 3 charts in 2 rows and 1 col.
        #  These _axes_mosaic represent these 2 rows and 1 col.
        #  Each item in the _axes_mosaic dict is an Axes instance: the x-axis and y-axis
        #  of an actual chart.
        self._axes_mosaic: dict[str, Axes]

        # Start date of the main activity.
        self._start_date_str: str | None = None

        # In a horizontal bars plot there are bar GROUPS, where one group matches
        #  one y data.
        # For example if we want to display the avg height for 2 groups (males and
        #  females) then we would have 2 groups (males and females).
        # Each bar groups has 1 or more BARS.
        # The first bar (index 0) is always the MAIN BAR.
        # All the other bars (index 1+) are the SECONDARY BARS.
        # Secondary bars have the same height, the main bar has 2x height of sec bars.
        self._n_bars_per_group: int | None = None

    @abstractmethod
    def _get_splits_for_activity_typed_splits_response(
        self, response: ActivityTypedSplitsResponse
    ):
        """
        To be reimplemented in sub-classe.
        Extract the splits in the response with:
         for split in response.get_interval_active_splits()
        and make sure they are what you want, fi. their distance is 300m.
        """
        pass

    def _plot_time(self):
        a: Axes = self._axes_mosaic["time"]

        ## MAIN activity.
        # X and y data.
        splits = self._get_splits_for_activity_typed_splits_response(
            self._s[0].type_splits_resp
        )
        xdata_times = [_["elapsedDuration"] for _ in splits]
        xdata_times.append(mean(xdata_times))  # Add avg time.
        ydata_range = np.arange(len(xdata_times))

        # Keep track of the max time, so we can use it later on to set the lim for
        #  x-axis. This is just for a visual optimization: add some empty space to
        #  make room for the bars labels.
        max_time = max(xdata_times)

        # Prepare the y tick labels as: "1st", "2nd", ... "avg".
        y_ticks_labels = [number_utils.ordinal(_) for _ in range(1, len(ydata_range))]
        y_ticks_labels += ["avg"]
        a.set_yticks(ydata_range, labels=y_ticks_labels)

        # Plot main activity's times.
        bar = a.barh(
            self._ydata_for_barh(ydata_range, 0, self._n_bars_per_group),
            xdata_times,
            self._bar_height_for_barh(0, self._n_bars_per_group),
            label=self._make_legend_label(0),
            color=["red" for _ in range(len(ydata_range) - 1)] + [COL_DARK_GRAY],
            alpha=0.6,
        )
        # Add the main activity's time values at the right of each bar.
        a.bar_label(bar, fmt=self._fmt_time, padding=2)

        ## SECONDARY activities.
        for i in range(1, len(self._s)):
            # X data.
            splits = self._get_splits_for_activity_typed_splits_response(
                self._s[i].type_splits_resp
            )
            xdata_times = [_["elapsedDuration"] for _ in splits]
            xdata_times.append(mean(xdata_times))  # Add avg time.

            # Update the max time.
            max_time = max(xdata_times) if max(xdata_times) > max_time else max_time

            # Plot secondary activities' times.
            bar = a.barh(
                self._ydata_for_barh(ydata_range, i, self._n_bars_per_group),
                xdata_times,
                self._bar_height_for_barh(i, self._n_bars_per_group),
                label=self._make_legend_label(i),
                color="gray",
                alpha=0.4,
            )
            # Add the secondary activities' times values at the right of each bar.
            a.bar_label(
                bar, fmt=self._fmt_time, padding=2, fontsize=8, color="gray", alpha=0.7
            )

        ## Format.
        # Invert the y-axis so the 1st attempt is on top.
        a.invert_yaxis()
        # Axes labels.
        a.set_xlabel("log(time) [s]")
        # Set the x-axis label to the top.
        a.xaxis.set_label_position("top")
        # Use log scale to amplify the small differences.
        # Using a diff base for the log does NOT change the chart.
        a.set_xscale("log")  # Add a base with arg: `base=2`.
        # Set the start and end scale for the x-axis, adding 2% width to make
        #  space for the bar labels.
        a.set_xlim((0, max_time * 1.03))
        # Set the start and end scale for the y-axis, so the 2 plots are aligned.
        a.set_ylim((len(ydata_range) - 0.4, -0.6))
        # Remove ticks.
        a.tick_params(
            axis="both",  # Changes apply to both axes.
            which="both",  # Both major and minor ticks are affected.
            bottom=False,  # Ticks along the bottom edge are off.
            # top=False,
            left=False,  # Ticks along the left edge are off.
            # right=False,
            labelbottom=False,  # Ticks labels along the bottom are off.
            # labelleft=False,
        )

    def _plot_pace(self):
        a: Axes = self._axes_mosaic["pace"]

        ## MAIN activity.
        # X and y data.
        splits = self._get_splits_for_activity_typed_splits_response(
            self._s[0].type_splits_resp
        )
        xdata_pace_avgs: list[float] = [_["averageMovingSpeed"] for _ in splits]
        xdata_pace_avgs.append(mean(xdata_pace_avgs))  # Add avg of all avgs pace.
        xdata_pace_maxs: list[float] = [_["maxSpeed"] for _ in splits]
        xdata_pace_maxs.append(mean(xdata_pace_maxs))  # Add avg of all maxes pace.
        ydata_range = np.arange(len(xdata_pace_avgs))

        # Keep track of the max pace, so we can use it later on to set the lim for
        #  x-axis. This is just for a visual optimization: add some empty space to
        #  make room for the bars labels.
        max_pace = max(xdata_pace_maxs)

        # Plot main activity's maxes pace.
        bar = a.barh(
            self._ydata_for_barh(ydata_range, 0, self._n_bars_per_group),
            xdata_pace_maxs,
            self._bar_height_for_barh(0, self._n_bars_per_group),
            color=["red" for _ in range(len(ydata_range) - 1)] + ["dimgray"],
            # color="tab:blue",
            alpha=0.6,
        )
        # Add main activity's maxes pace values at the right of each bar.
        a.bar_label(bar, fmt=self._fmt_pace, padding=2)

        # Plot main activity's avgs pace, on top of the maxes.
        bar = a.barh(
            self._ydata_for_barh(ydata_range, 0, self._n_bars_per_group),
            xdata_pace_avgs,
            self._bar_height_for_barh(0, self._n_bars_per_group),
            # color="#084266",
            color=[COL_DARK_RED for _ in range(len(ydata_range) - 1)] + [COL_DARK_GRAY],
            alpha=0.8,
        )
        # Add main activity's avgs pace values at the right of each bar.
        a.bar_label(bar, fmt=self._fmt_pace, padding=2)

        ## SECONDARY activities.
        for i in range(1, len(self._s)):
            splits = self._get_splits_for_activity_typed_splits_response(
                self._s[i].type_splits_resp
            )

            # X and y data.
            xdata_pace_avgs: list[float] = [_["averageMovingSpeed"] for _ in splits]
            xdata_pace_avgs.append(mean(xdata_pace_avgs))  # Add avg of all avgs pace.
            xdata_pace_maxs: list[int] = [_["maxSpeed"] for _ in splits]
            xdata_pace_maxs.append(mean(xdata_pace_maxs))  # Add avg of all maxes pace.

            # Update max_pace.
            max_pace = (
                max(xdata_pace_maxs) if max(xdata_pace_maxs) > max_pace else max_pace
            )

            # Plot secondary activities' maxes pace.
            bar = a.barh(
                self._ydata_for_barh(ydata_range, i, self._n_bars_per_group),
                xdata_pace_maxs,
                self._bar_height_for_barh(i, self._n_bars_per_group),
                color="gray",
                alpha=0.4,
            )
            # Add secondary activities' maxes pace values at the right of each bar.
            a.bar_label(
                bar, fmt=self._fmt_pace, padding=2, fontsize=8, color="gray", alpha=0.7
            )
            # Plot secondary activities' avgs paces, on top of the maxes.
            bar = a.barh(
                self._ydata_for_barh(ydata_range, i, self._n_bars_per_group),
                xdata_pace_avgs,
                self._bar_height_for_barh(i, self._n_bars_per_group),
                color="gray",
                alpha=0.4,
            )
            # Add secondary activities' avg paces values at the right of each bar.
            a.bar_label(
                bar, fmt=self._fmt_pace, padding=2, fontsize=8, color="black", alpha=0.7
            )

        ## Format.
        # Invert the y-axis so the 1st attempt is on top.
        a.invert_yaxis()
        a.set_xlabel("log(pace avg|max) [min/km]")
        # Set the x-axis label to the top.
        a.xaxis.set_label_position("top")
        # Use log scale to amplify the small differences.
        # Using a diff base for the log does NOT change the chart.
        a.set_xscale("log")  # Add a base with arg: `base=2`.
        # Set the start and end scale for the x-axis, adding 2% width to make
        #  space for the bar labels.
        a.set_xlim((0, max_pace * 1.03))
        # Set the start and end scale for the y-axis, so the 2 plots are aligned.
        a.set_ylim((len(ydata_range) - 0.4, -0.6))
        # Remove ticks.
        a.tick_params(
            axis="both",  # Changes apply to both axes.
            which="both",  # Both major and minor ticks are affected.
            bottom=False,  # Ticks along the bottom edge are off.
            # top=False,
            left=False,  # Ticks along the left edge are off.
            # right=False,
            labelbottom=False,  # Ticks labels along the bottom are off.
            labelleft=False,
        )

    def _plot_cadence(self):
        a: Axes = self._axes_mosaic["cadence"]

        ## MAIN activity.
        # X and y data.
        splits = self._get_splits_for_activity_typed_splits_response(
            self._s[0].type_splits_resp
        )
        xdata_cadence_avgs: list[float] = [_["averageRunCadence"] for _ in splits]
        # Add avg of all avgs cadence.
        xdata_cadence_avgs.append(mean(xdata_cadence_avgs))
        xdata_cadence_maxs: list[float] = [_["maxRunCadence"] for _ in splits]
        # Add avg of all maxes cadence.
        xdata_cadence_maxs.append(mean(xdata_cadence_maxs))
        ydata_range = np.arange(len(xdata_cadence_avgs))

        # Keep track of the max cadence, so we can use it later on to set the lim for
        #  x-axis. This is just for a visual optimization: add some empty space to
        #  make room for the bars labels.
        max_cadence = max(xdata_cadence_maxs)

        # Plot main activity's maxes cadence.
        bar = a.barh(
            self._ydata_for_barh(ydata_range, 0, self._n_bars_per_group),
            xdata_cadence_maxs,
            self._bar_height_for_barh(0, self._n_bars_per_group),
            color=["red" for _ in range(len(ydata_range) - 1)] + ["dimgray"],
            # color="tab:blue",
            alpha=0.6,
        )
        # Add main activity's maxes cadence values at the right of each bar.
        a.bar_label(bar, fmt="{0:.0f}", padding=2)

        # Plot main activity's avgs cadence, on top of the maxes.
        bar = a.barh(
            self._ydata_for_barh(ydata_range, 0, self._n_bars_per_group),
            xdata_cadence_avgs,
            self._bar_height_for_barh(0, self._n_bars_per_group),
            # color="#084266",
            color=[COL_DARK_RED for _ in range(len(ydata_range) - 1)] + [COL_DARK_GRAY],
            alpha=0.8,
        )
        # Add main activity's avgs cadence values at the right of each bar.
        a.bar_label(bar, fmt="{0:.0f}", padding=2)

        ## SECONDARY activities.
        for i in range(1, len(self._s)):
            splits = self._get_splits_for_activity_typed_splits_response(
                self._s[i].type_splits_resp
            )

            # X and y data.
            xdata_cadence_avgs: list[float] = [_["averageRunCadence"] for _ in splits]
            # Add avg of all avgs cadence.
            xdata_cadence_avgs.append(mean(xdata_cadence_avgs))
            xdata_cadence_maxs: list[int] = [_["maxRunCadence"] for _ in splits]
            # Add avg of all maxes cadence.
            xdata_cadence_maxs.append(mean(xdata_cadence_maxs))

            # Update max_cadence.
            max_cadence = (
                max(xdata_cadence_maxs)
                if max(xdata_cadence_maxs) > max_cadence
                else max_cadence
            )

            # Plot secondary activities' maxes cadence.
            bar = a.barh(
                self._ydata_for_barh(ydata_range, i, self._n_bars_per_group),
                xdata_cadence_maxs,
                self._bar_height_for_barh(i, self._n_bars_per_group),
                color="gray",
                alpha=0.4,
            )
            # Add secondary activities' maxes cadence values at the right of each bar.
            a.bar_label(
                bar, fmt="{0:.0f}", padding=2, fontsize=8, color="gray", alpha=0.7
            )
            # Plot secondary activities' avgs cadence, on top of the maxes.
            bar = a.barh(
                self._ydata_for_barh(ydata_range, i, self._n_bars_per_group),
                xdata_cadence_avgs,
                self._bar_height_for_barh(i, self._n_bars_per_group),
                color="gray",
                alpha=0.4,
            )
            # Add secondary activities' avgs cadence values at the right of each bar.
            a.bar_label(
                bar, fmt="{0:.0f}", padding=2, fontsize=8, color="black", alpha=0.7
            )

        ## Format.
        # Invert the y-axis so the 1st attempt is on top.
        a.invert_yaxis()
        a.set_xlabel("log(cadence avg|max) [spm]")
        # Set the x-axis label to the top.
        a.xaxis.set_label_position("top")
        # Use log scale to amplify the small differences.
        # Using a diff base for the log does NOT change the chart.
        a.set_xscale("log")  # Add a base with arg: `base=2`.
        # Set the start and end scale for the x-axis, adding 2% width to make
        #  space for the bar labels.
        a.set_xlim((0, max_cadence * 1.03))
        # Set the start and end scale for the y-axis, so the 2 plots are aligned.
        a.set_ylim((len(ydata_range) - 0.4, -0.6))
        # Remove ticks.
        a.tick_params(
            axis="both",  # Changes apply to both axes.
            which="both",  # Both major and minor ticks are affected.
            bottom=False,  # Ticks along the bottom edge are off.
            # top=False,
            left=False,  # Ticks along the left edge are off.
            # right=False,
            labelbottom=False,  # Ticks labels along the bottom are off.
            labelleft=False,
        )

    def _plot_hr(self):
        a: Axes = self._axes_mosaic["hr"]

        ## MAIN activity.
        # X and y data.
        splits = self._get_splits_for_activity_typed_splits_response(
            self._s[0].type_splits_resp
        )
        xdata_hr_avgs: list[float] = [_["averageHR"] for _ in splits]
        xdata_hr_avgs.append(mean(xdata_hr_avgs))  # Add avg of all HR avgs.
        xdata_hr_maxs: list[int] = [_["maxHR"] for _ in splits]
        xdata_hr_maxs.append(mean(xdata_hr_maxs))  # Add avg of all HR maxes.
        ydata_range = np.arange(len(xdata_hr_avgs))

        # Keep track of the max hr, so we can use it later on to set the lim for
        #  x-axis. This is just for a visual optimization: add some empty space to
        #  make room for the bars labels.
        max_hr = max(xdata_hr_maxs)

        # Plot main activity's maxes HR.
        bar = a.barh(
            self._ydata_for_barh(ydata_range, 0, self._n_bars_per_group),
            xdata_hr_maxs,
            self._bar_height_for_barh(0, self._n_bars_per_group),
            color=["red" for _ in range(len(ydata_range) - 1)] + ["dimgray"],
            # color="tab:blue",
            alpha=0.6,
        )
        # Add main activity's maxes HR values at the right of each bar.
        a.bar_label(bar, fmt="{0:.0f}", padding=2)

        # Plot main activity's avgs HR, on top of the maxes.
        bar = a.barh(
            self._ydata_for_barh(ydata_range, 0, self._n_bars_per_group),
            xdata_hr_avgs,
            self._bar_height_for_barh(0, self._n_bars_per_group),
            # color="#084266",
            color=[COL_DARK_RED for _ in range(len(ydata_range) - 1)] + [COL_DARK_GRAY],
            alpha=0.8,
        )
        # Add main activity's avgs HR values at the right of each bar.
        a.bar_label(bar, fmt="{0:.0f}", padding=2)

        ## SECONDARY activities.
        for i in range(1, len(self._s)):
            # If the activity does not have a heart rate monitor, then I skip it.
            #  I chose this because data without HRM are unreliable and lower,
            #  so the effect on the chart is to visually reduce the differences.
            if not self._s[i].summary_resp.has_heart_rate_monitor():
                continue

            splits = self._get_splits_for_activity_typed_splits_response(
                self._s[i].type_splits_resp
            )

            # X and y data.
            xdata_hr_avgs: list[float] = [_["averageHR"] for _ in splits]
            xdata_hr_avgs.append(mean(xdata_hr_avgs))  # Add avg of all avgs HR.
            xdata_hr_maxs: list[int] = [_["maxHR"] for _ in splits]
            xdata_hr_maxs.append(mean(xdata_hr_maxs))  # Add avg of all maxes HR.

            # Update max_hr.
            max_hr = max(xdata_hr_maxs) if max(xdata_hr_maxs) > max_hr else max_hr

            # Plot secondary activities' maxes HR.
            bar = a.barh(
                self._ydata_for_barh(ydata_range, i, self._n_bars_per_group),
                xdata_hr_maxs,
                self._bar_height_for_barh(i, self._n_bars_per_group),
                color="gray",
                alpha=0.4,
            )
            # Add secondary activities' maxes HR values at the right of each bar.
            a.bar_label(
                bar, fmt="{0:.0f}", padding=2, fontsize=8, color="gray", alpha=0.7
            )
            # Plot secondary activities' avgs HR, on top of the maxes.
            bar = a.barh(
                self._ydata_for_barh(ydata_range, i, self._n_bars_per_group),
                xdata_hr_avgs,
                self._bar_height_for_barh(i, self._n_bars_per_group),
                color="gray",
                alpha=0.4,
            )
            # Add secondary activities' avgs HR values at the right of each bar.
            a.bar_label(
                bar, fmt="{0:.0f}", padding=2, fontsize=8, color="black", alpha=0.7
            )

        ## Format.
        # Invert the y-axis so the 1st attempt is on top.
        a.invert_yaxis()
        a.set_xlabel("log(HR avg|max) [bpm]")
        # Set the x-axis label to the top.
        a.xaxis.set_label_position("top")
        # Use log scale to amplify the small differences.
        # Using a diff base for the log does NOT change the chart.
        a.set_xscale("log")  # Add a base with arg: `base=2`.
        # Set the start and end scale for the x-axis, adding 2% width to make
        #  space for the bar labels.
        a.set_xlim((0, max_hr * 1.03))
        # Set the start and end scale for the y-axis, so the 2 plots are aligned.
        a.set_ylim((len(ydata_range) - 0.4, -0.6))
        # Remove ticks.
        a.tick_params(
            axis="both",  # Changes apply to both axes.
            which="both",  # Both major and minor ticks are affected.
            bottom=False,  # Ticks along the bottom edge are off.
            # top=False,
            left=False,  # Ticks along the left edge are off.
            # right=False,
            labelbottom=False,  # Ticks labels along the bottom are off.
            labelleft=False,
        )

    def plot(self, save_to_png_file_path: Path | None = None):
        ## Collect MAIN activity's time splits and summary.
        self._s.append(
            CollectedData(
                summary_resp=self._api_get_activity_summary(self.garmin_activity_id),
                type_splits_resp=self._api_get_activity_typed_splits(
                    self.garmin_activity_id
                ),
            )
        )
        self._start_date_str = self._s[0].summary_resp.summary["startTimeLocal"][:10]

        if self.n_previous_activities_to_compare > 0:
            for activity_id in self._api_search_activities(
                filter_exclude=[self.garmin_activity_id],
                text=self.text_to_search_for_previous_activities,
                activity_type="running",
                day_end=self._start_date_str,
                # Add 1 because the results include the main activity,
                #  and another 1 to account for the activity that was interrupted for a
                #  false Incident Detection and ended up as 2 activities (as better
                #  explained in MixinGarminRequestsApi._api_get_activity_splits()).
                n_results=self.n_previous_activities_to_compare + 2,
            ):
                ## Collect all SECONDARY activities time splits and summeries.
                try:
                    splits_resp = self._api_get_activity_typed_splits(activity_id)
                except base_api.InterruptedActivity:
                    # An activity that was interrupted for a false Incident Detection
                    #  and ended up as 2 activities (as better explained in
                    #  MixinGarminRequestsApi._api_get_activity_splits()).
                    #  Nothing to do as the other activity uses a fixture to join all
                    #  the splits.
                    splits_resp = None
                try:
                    summary_resp = self._api_get_activity_summary(activity_id)
                except base_api.InterruptedActivity:
                    # An activity that was interrupted for a false Incident Detection
                    #  and ended up as 2 activities (as better explained in
                    #  MixinGarminRequestsApi._api_get_activity_splits()).
                    #  Nothing to do as the other activity uses a fixture to join all
                    #  the splits.
                    summary_resp = None
                self._s.append(
                    CollectedData(
                        summary_resp=summary_resp, type_splits_resp=splits_resp
                    )
                )

        # Figure.
        self._n_bars_per_group = len(self._s)
        figure, self._axes_mosaic = self._make_subplot_mosaic()
        figure: Figure
        self._axes_mosaic: dict[str, Axes]

        # All plots.
        self._plot_time()
        self._plot_pace()
        self._plot_cadence()
        self._plot_hr()

        title = (
            self.title
            if self.title is not None
            else self._s[0].summary_resp.data["activityName"]
        )
        figure.suptitle(title)

        # Docs on legend location:
        #  https://matplotlib.org/stable/users/explain/axes/legend_guide.html
        figure.legend(loc="outside lower left", ncol=1, frameon=False, fontsize=9)

        # Fix overlapping bar labels.
        self._fix_overlapping_bar_labels(
            [
                self._axes_mosaic["hr"],
                self._axes_mosaic["pace"],
                self._axes_mosaic["cadence"],
            ]
        )

        if save_to_png_file_path:
            logger.info(f"Created image: {save_to_png_file_path}")
            plt.savefig(save_to_png_file_path)
        else:
            plt.show()

    def _make_figure_size(self) -> tuple[float, float]:
        if self.figure_size is not None:
            return self.figure_size

        width = 5.0
        if self._n_bars_per_group == 2:
            height = 7
        elif self._n_bars_per_group == 3:
            height = 8
        else:
            height = max(5.0, self._n_bars_per_group * 2.2)
        return width, height

    def _make_subplot_mosaic(self) -> tuple[Figure, dict[str, Axes]]:
        # Docs for subplot_mosaic():
        #  https://matplotlib.org/stable/users/explain/axes/arranging_axes.html#variable-widths-or-heights-in-a-grid
        #  https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplot_mosaic.html#matplotlib.pyplot.subplot_mosaic
        return plt.subplot_mosaic(
            # fmt: off
    [
                # 2 rows, 2 col.
                ["time", "hr"],
                ["pace", "cadence"],
            ],
            # fmt: on
            gridspec_kw=dict(
                # The relative sizes of the subplots.
                width_ratios=[1, 1],
                height_ratios=[1, 1],
            ),
            figsize=self._make_figure_size(),
            layout="constrained",
        )

    def _make_legend_label(self, activity_index: int) -> str:
        """
        Make the text used in the legend label for a plot.
        """
        summary = self._s[activity_index].summary_resp

        # Start date.
        legend_label = summary.summary["startTimeLocal"][:10]
        # HRM.
        if not summary.has_heart_rate_monitor():
            legend_label += " no HRM"

        return legend_label

    def _fmt_pace(self, pace_mps: float):
        x = speed_utils.mps_to_minpkm_base10(pace_mps)
        return speed_utils.minpkm_base10_to_base60(x)

    def _fmt_time(self, seconds: float):
        return f"{seconds:.2f}"


class BasePlotIntervalRunException(Exception):
    pass
