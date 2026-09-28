from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from statistics import fmean
from typing import Sequence

import datetime_utils
import matplotlib as mpl
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import number_utils
import numpy as np
import pandas as pd
import speed_utils
import text_utils
from garmin_connect_client import (
    ActivityDetailsResponse,
    ActivitySummaryResponse,
    ActivityTypedSplitsResponse,
)
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from sport_analysis.base_cli_view import ConsoleAdapter
from sport_analysis.conf import settings
from sport_analysis.plot import base_api, base_plot
from sport_analysis.plot.base_plot import (
    _get_bpm_range_for_hr_zone,
    _make_subtitle,
    _make_title,
)

console = ConsoleAdapter()


# Example of dict in `typed_splits_extracted`, it's the 5th split of 8 in garmin-id 24473738940):
# split = {
#     "startTimeLocal": "2026-09-23T20:26:43.0",
#     "startTimeGMT": "2026-09-23T18:26:43.0", <<<<<<<<<<<<<<<<<<<<<<<<<<<
#     "startLatitude": 45.71300701238215,
#     "startLongitude": 9.715366819873452,
#     "distance": 1000.0, <<<<<<<<<<<<<<<<<<<<<<<<<<<
#     "duration": 236.317,
#     "movingDuration": 233.0,
#     "elapsedDuration": 236.317, <<<<<<<<<<<<<<<<<<<<<<<<<<<
#     "elevationGain": 0.0,
#     "elevationLoss": 0.0,
#     "averageSpeed": 4.23199987411499, <<<<<<<<<<<<<<<<<<<<<<<<<<<
#     "averageMovingSpeed": 4.291845493562231,
#     "maxSpeed": 4.692999839782715,
#     "calories": 65.0,
#     "bmrCalories": 6.0,
#     "averageHR": 136.0, <<<<<<<<<<<<<<<<<<<<<<<<<<<
#     "maxHR": 157.0, <<<<<<<<<<<<<<<<<<<<<<<<<<<
#     "averageRunCadence": 177.6875,
#     "maxRunCadence": 188.0,
#     "averagePower": 500.0,
#     "maxPower": 571.0,
#     "normalizedPower": 493.0,
#     "groundContactTime": 218.1999969482422,
#     "strideLength": 143.39000244140627,
#     "verticalOscillation": 9.34000015258789,
#     "verticalRatio": 6.510000228881836,
#     "totalExerciseReps": 0,
#     "endLatitude": 45.71223638020456,
#     "endLongitude": 9.71445151604712,
#     "avgVerticalSpeed": 0.0,
#     "avgElapsedDurationVerticalSpeed": 0.0,
#     "type": "INTERVAL_ACTIVE",
#     "messageIndex": 31,
#     "lapIndexes": [11],
#     "endTimeGMT": "2026-09-23T18:30:39.0", <<<<<<<<<<<<<<<<<<<<<<<<<<<
#     "startElevation": 279.0,
#     "avgStepLength": 1.4339000244140627,
# }
#
# Example of `typed_splits_stream_indexes` (the matching stream start and end indexes
#  for each typed split in the activity) for garmin-id 24473738940:
# [(0, 231), (385, 612), (806, 1029), (1202, 1432), (1636, 1865), (2064, 2300), (2519, 2740), (2962, 3177)]
@dataclass
class CollectedData:
    summary_resp: ActivitySummaryResponse = None
    details_resp: ActivityDetailsResponse = None
    typed_splits_resp: ActivityTypedSplitsResponse = None
    typed_splits_extracted: list[dict] = field(default_factory=list)  # See docs above.
    # See docs above.
    typed_splits_stream_indexes: list[tuple[int, int]] = field(default_factory=list)


class PlotDistIntervalRunApiCmd(
    base_api.MixinGarminRequestsApi,
    base_plot.MixinBarHPlot,
    base_plot.MixinHrPlot,
):
    """
    Plots to support the analysis of a time interval run activity performance.
    """

    # TODO Copied from plot_interval_run_api_cmd.DISTANCE_ENUM.
    class INTERVAL_DISTANCE_ENUM(IntEnum):
        ONE_H = 100
        TWO_H = 200
        THREE_H = 300
        ONE_T = 1000

    # TODO Copied from plot_interval_run_api_cmd.DEFAULT_N_EXPECTED_INTERVALS.
    # List of all possible expected number of intervals: fi. for a 4x1000m it is [4],
    #  but if you want to include also a 5x1000m then it is [4, 5]. Use range() to
    #  include many values.
    DEFAULT_N_EXPECTED_INTERVALS: dict[INTERVAL_DISTANCE_ENUM, Sequence] = {
        100: range(3, 26),
        200: range(3, 26),
        300: range(3, 16),
        1000: range(3, 11),
    }

    def __init__(
        self,
        # id (int) of Garmin activity to analyze or ("LATEST", 0) or ("LATEST", -3).
        garmin_activity_id: int | tuple[str, int],
        # intervals_plan=intervals_plan, # TODO
        distance: INTERVAL_DISTANCE_ENUM | int,
        n_expected_intervals: Sequence[int] | None = None,
        pace_plot_clip_y_axis: tuple[float, float] | None = None,
        do_skip_hr_in_pace_plot: bool = False,
        title: str | None = None,
        figure_size: tuple[float, float] | None = None,
        garmin_connect_token_manager: (
            FileGarminConnectTokenManager | FakeTestGarminConnectTokenManager | None
        ) = None,
    ):
        """
        Args:
            garmin_activity_id: required, id (int) of Garmin activity to analyze or
             ("LATEST", 0) or ("LATEST", -3).
            intervals_plan: TODO
            pace_plot_clip_y_axis: eg. (1.2, 0.45) | (0, 0.5). In the
             pace plot, cutting out, of the visible part of the plot, the top % and
             bottom % of data (so the fastest and slowest datapoints). This is done
             because it is better visually: the plot is less compressed vertically.
            do_skip_hr_in_pace_plot: skip adding HR line in the pace plot.
            title: figure title.
            figure_size: customize the figure size, eg. (3.0, 5.5).
            garmin_connect_token_manager: use FakeTestGarminConnectTokenManager when
             replaying VCR episodes.
        """
        super().__init__(garmin_connect_token_manager)

        self.garmin_activity_id = garmin_activity_id
        self.distance = distance
        if distance not in self.INTERVAL_DISTANCE_ENUM:
            raise IntervalDistanceNotSupported(
                f"Interval distance not supported yet: {distance}"
            )
        self.n_expected_intervals = (
            n_expected_intervals or self.DEFAULT_N_EXPECTED_INTERVALS[distance]
        )
        self.pace_plot_clip_y_axis = pace_plot_clip_y_axis
        self.do_skip_hr_in_pace_plot = do_skip_hr_in_pace_plot
        self.title = title
        self.figure_size = figure_size

        # The store used for Garmin Connect API responses collected for all activities.
        self._s: list[CollectedData] = []

        # Matplotlib axes mosaic. This figure is made of 3 charts in 2 rows and 1 col.
        #  These _axes_mosaic represent these 2 rows and 1 col.
        #  Each item in the _axes_mosaic dict is an Axes instance: the x-axis and y-axis
        #  of an actual chart.
        self._axes_mosaic: dict[str, Axes]

    # TODO copied from PlotIntervalRunApiCmd._get_splits_for_activity_typed_splits_response
    def _get_splits_for_activity_typed_splits_response(
        self,
        response: ActivityTypedSplitsResponse,
        # Usually we want to check the n of extracted splits vs the expected one only
        #  for the given activity, not for the old activities to compare.
        do_raise_if_n_split_not_expected=True,
    ):
        # The max distance error allowed for a split is 1.5% of the given distance (min
        #   3 meters).
        # So a split is valid if the distance run in that split is <= 1.5% off the
        #  given distance.
        max_distance_error = max(3, round((self.distance / 100) * 1.5))
        splits = list()
        for split in response.get_interval_active_splits():
            if abs(split["distance"] - self.distance) <= max_distance_error:
                splits.append(split)
        if do_raise_if_n_split_not_expected and (
            len(splits) not in self.n_expected_intervals
        ):
            raise NumberOfExpectedIntervalsError(
                f"Found {len(splits)} splits of {self.distance}m, expected {' or '.join(str(x) for x in self.n_expected_intervals)}"
            )

        return splits

    def _plot_pace(self):
        # TODO this code is copied from plot-simple-run, so it would be nice to join
        #  the 2 method. The main diff are:
        #  - this plot is over time and not distance
        #  - there are less features (like the xtick labels are simpler here)
        #  - it supports trimming by elapsed time
        #  - it highlights the intervals by colouring the bg to gray
        #  Maybe I could create a mixin method that performs the common things
        #   and then do the specific things in each actual method

        a: Axes = self._axes_mosaic["pace"]

        ## MAIN activity.
        # X and y data.
        # xdata_distance = self._s[0].details_resp.get_distance_stream()
        xdata_elapsed_time = self._s[0].details_resp.get_elapsed_time_stream()
        # Y data should be the PACE in m/s.
        _speed_stream = self._s[0].details_resp.get_speed_stream(
            do_remove_none_values=False
        )
        ydata_pace_mps_df = pd.DataFrame(_speed_stream, columns=["pace"])
        del _speed_stream

        # Compute the y-axis bottom.
        # Setting the bottom of y-axis to the best pace of the lowest 0.5% pace
        #  datapoint. In simpler words: cutting out of the visible part of the chart
        #  the slowest 0.5% pace datapoints. This is done because it is better
        #  visually: the chart is less compressed vertically.
        _y_axis_top = None
        _y_axis_bottom = None
        if self.pace_plot_clip_y_axis:
            _y_axis_top = (
                ydata_pace_mps_df["pace"]
                # Get the 0.5% largest datapoints, so the slowest paces.
                .nlargest(
                    round(
                        ydata_pace_mps_df["pace"].size
                        / 100
                        * self.pace_plot_clip_y_axis[0]
                    )
                    or 1
                )
                # And get the last one, so the slowest of the fastest 0.5% paces.
                .iloc[-1]
            )
            _y_axis_bottom = (
                ydata_pace_mps_df["pace"]
                # Get the 0.5% largest datapoints, so the slowest paces.
                .nsmallest(
                    round(
                        ydata_pace_mps_df["pace"].size
                        / 100
                        * self.pace_plot_clip_y_axis[1]
                    )
                    or 1
                )
                # And get the last one, so the fastest of the slowest 0.5% paces.
                .iloc[-1]
            )

        # Plot PACE.
        a.plot(
            xdata_elapsed_time,
            ydata_pace_mps_df,
            # label=self._make_legend_label(0),
            # color="red",
            color=base_plot.COL_PLUM,
            alpha=0.8,
            linewidth=3.0,
        )
        # Plot HR.
        if not self.do_skip_hr_in_pace_plot:
            # Get HR.
            ydata_hr = self._s[0].details_resp.get_heartrate_stream(
                do_remove_none_values=False
            )

            # Plot HR on twin x axis.
            # Create new Axes that share the x-axis.
            atwinx_hr: Axes = a.twinx()
            atwinx_hr.plot(
                xdata_elapsed_time,
                ydata_hr,
                color="red",
                alpha=0.2,
            )

        ## Format.
        # Axes labels.
        a.set_ylabel("Pace [min/km]", fontsize=9)
        a.set_xlabel("Elapsed time", fontsize=9)  # labelpad=13.0)

        # axes.xaxis.set_label_position("top")
        # Convert the y-axis ticks to pace in min/km (so from base10 to base60).
        a.yaxis.set_major_formatter(
            mpl.ticker.FuncFormatter(
                lambda x, pos: speed_utils.minpkm_base10_to_base60(
                    speed_utils.mps_to_minpkm_base10(x)
                )
            )
        )
        a.yaxis.grid(color="gray", alpha=0.2, linestyle="--")

        # Ticks for the x axis: time.
        a.xaxis.set_major_formatter(
            mpl.ticker.FuncFormatter(
                lambda x, pos: datetime_utils.seconds_to_hh_mm_ss(x)
            )
        )

        # x axis limits.
        a.set_xlim(left=0, right=xdata_elapsed_time[-1])

        # y axis limit: set the bottom of y-axis to the best pace of the lowest
        #  0.5% pace found.
        if self.pace_plot_clip_y_axis and self.pace_plot_clip_y_axis[0]:
            a.set_ylim(top=_y_axis_top)
        if self.pace_plot_clip_y_axis and self.pace_plot_clip_y_axis[1]:
            a.set_ylim(bottom=_y_axis_bottom)

        # Z0, Z1, Z2, etc on the y axis right.
        if not self.do_skip_hr_in_pace_plot:
            # Get the HR zones bpm ranges.
            hr_min = min(tuple(x for x in ydata_hr if x is not None))
            hr_max_ever = settings.HR_MAX_EVER_RUN
            z0_x0, z0_x1 = _get_bpm_range_for_hr_zone(0, hr_min, hr_max_ever)
            z1_x0, z1_x1 = _get_bpm_range_for_hr_zone(1, hr_min, hr_max_ever)
            z2_x0, z2_x1 = _get_bpm_range_for_hr_zone(2, hr_min, hr_max_ever)
            z3_x0, z3_x1 = _get_bpm_range_for_hr_zone(3, hr_min, hr_max_ever)
            z4_x0, z4_x1 = _get_bpm_range_for_hr_zone(4, hr_min, hr_max_ever)
            z5_x0, z5_x1 = _get_bpm_range_for_hr_zone(5, hr_min, hr_max_ever)

            # Set tick on the y right axis with HR.
            # Hack: first just set it to anything, so it gets the min value, which is
            #  not simply min(ydata_hr) because this is a twin axis and the min can be
            #  min(ydata_pace_df["MA(pace)"]) which, also, is in a diff unit.
            # You see what I mean if you `san plot-simple-run g-18948270166`.
            atwinx_hr.set_yticks([120])  # Hack, see ^.
            distance_ticks_m = (z0_x1, z1_x1, z2_x1, z3_x1, z4_x1, z5_x1)
            atwinx_hr.set_yticks(distance_ticks_m)
            atwinx_hr.set_ylabel("HR [bpm]", fontsize=9)

            # Draw the labels Z0, Z1, Z2, ...
            for i, x in enumerate(
                (
                    (z0_x0, z0_x1),
                    (z1_x0, z1_x1),
                    (z2_x0, z2_x1),
                    (z3_x0, z3_x1),
                    (z4_x0, z4_x1),
                    (z5_x0, z5_x1),
                )
            ):
                x0, x1 = x
                # Draw "Z0" only if there's enough room.
                if x1 - atwinx_hr.get_ylim()[0] > 9:
                    atwinx_hr.annotate(
                        f"Z{i}",
                        (atwinx_hr.get_xlim()[1], (x0 + x1) / 2),
                        xytext=(2.0, -0.6),
                        textcoords="offset fontsize",
                        color="red",
                        alpha=0.3,
                        fontsize=8,
                        fontweight="bold",
                        horizontalalignment="center",
                    )

            # Write text annotation for PACE and HR with the matching colors.
            a.annotate(
                "PACE",
                (a.get_xlim()[0], a.get_ylim()[1]),
                xytext=(0.3, -1.2),
                textcoords="offset fontsize",
                color=base_plot.COL_PLUM,
                alpha=0.6,
                fontsize=8,
                fontweight="bold",
                path_effects=self.PATH_EFFECTS,
            )
            a.annotate(
                "HR",
                (a.get_xlim()[0], a.get_ylim()[1]),
                xytext=(3.7, -1.2),
                textcoords="offset fontsize",
                color="red",
                alpha=0.3,
                fontsize=8,
                fontweight="bold",
                path_effects=self.PATH_EFFECTS,
            )

        # Draw fast intervals as gray background areas.
        for start_ix, end_ix in self._s[0].typed_splits_stream_indexes:
            a.axvspan(
                xdata_elapsed_time[start_ix],
                xdata_elapsed_time[end_ix],
                color="grey",
                alpha=0.2,
            )

    def _plot_time_bars(self):
        # TODO rivedi tutti i commenti in questo metodo, xche li ho scopiazzati.

        a: Axes = self._axes_mosaic["time-bars"]

        ## FAST intervals.
        # Note: it's an interval, so there is no pause nor still time, and so
        #  elapsed time is the best choice (better than moving time).
        xdata_times_fast = [
            _["elapsedDuration"] for _ in self._s[0].typed_splits_extracted
        ]
        ydata_range = np.arange(len(xdata_times_fast) + 1)
        ydata_range_fast_for_barh_mixin = self._ydata_for_barh_mixin(ydata_range, 0, 2)
        bar = a.barh(
            ydata_range_fast_for_barh_mixin,
            xdata_times_fast + [fmean(xdata_times_fast)],
            self._bar_height_for_barh_mixin(0, 2),
            # label=self._make_legend_label(0),
            color=[base_plot.COL_PLUM for _ in range(len(ydata_range) - 1)]
            + [base_plot.COL_DARK_GRAY],
            alpha=0.9,
        )
        # Add the main activity's time values at the right of each bar.
        a.bar_label(bar, fmt=self._fmt_time, padding=2, path_effects=self.PATH_EFFECTS)

        ## SLOW intervals.
        xdata_times_slow = []
        for i in range(len(self._s[0].typed_splits_extracted) - 1):
            split0 = self._s[0].typed_splits_extracted[i]
            split1 = self._s[0].typed_splits_extracted[i + 1]
            start_dt = datetime_utils.parse_datetime_arg(
                split0["endTimeGMT"], is_naive_allowed=True
            ).replace(tzinfo=timezone.utc)
            end_dt = datetime_utils.parse_datetime_arg(
                split1["startTimeGMT"], is_naive_allowed=True
            ).replace(tzinfo=timezone.utc)

            duration = (end_dt - start_dt).total_seconds()
            xdata_times_slow.append(duration)
        # Finally, append the last slow, which is 0 because it's usually a long cool down.
        xdata_times_slow.append(0)
        # Create new axes that shares the y-axis.
        atwiny_slow: Axes = a.twiny()
        ydata_range_slow_for_barh_mixin = self._ydata_for_barh_mixin(ydata_range, 1, 2)
        bar = atwiny_slow.barh(
            ydata_range_slow_for_barh_mixin,
            xdata_times_slow + [fmean(xdata_times_slow)],
            self._bar_height_for_barh_mixin(1, 2),
            # label=self._make_legend_label(0),
            color=[base_plot.COL_PLUM for _ in range(len(ydata_range) - 1)]
            + [base_plot.COL_DARK_GRAY],
            alpha=0.4,
        )
        # Add the main activity's time values at the right of each bar.
        atwiny_slow.bar_label(
            bar,
            fmt=self._fmt_time,
            padding=2,
            fontsize=8,
            color="gray",
            alpha=0.7,
            path_effects=self.PATH_EFFECTS,
        )

        ## Format.
        # Invert the y-axis so the 1st attempt is on top.
        a.invert_yaxis()
        # Axes labels.
        a.set_xlabel("Time [s]", fontsize=9)
        # Set the x-axis label to the top.
        a.xaxis.set_label_position("top")
        # Use log scale to amplify the small differences.
        # Using a diff base for the log does NOT change the chart.
        a.set_xscale("log")  # Add a base with arg: `base=2`.
        atwiny_slow.set_xscale("log")
        atwiny_slow.set_axis_off()
        # Set the start and end scale for the x-axis, adding 2% width to make
        #  space for the bar labels.
        max_time = max(xdata_times_fast)
        a.set_xlim((0, max_time * 1.007))
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
        # Hide all spines except the left one.
        a.spines[["right", "top", "bottom"]].set_visible(False)

        # Set the y tick labels as: "1000m|REST", "2nd", "3rd", ... "avg".
        y_ticks_labels = [number_utils.ordinal(_) for _ in range(1, len(ydata_range))]
        y_ticks_labels[0] = ""
        y_ticks_labels += ["avg"]
        a.set_yticks(ydata_range, labels=y_ticks_labels)
        a.annotate(
            f"{self.distance}m",
            (a.get_xlim()[0], ydata_range_fast_for_barh_mixin[0]),
            xytext=(-0.3, -0.4),
            textcoords="offset fontsize",
            color=base_plot.COL_PLUM,
            alpha=0.9,
            fontsize=8,
            fontweight="bold",
            # style="italic",
            horizontalalignment="right",
            path_effects=self.PATH_EFFECTS,
        )
        a.annotate(
            "REST",
            (a.get_xlim()[0], ydata_range_slow_for_barh_mixin[0]),
            xytext=(-0.3, -0.4),
            textcoords="offset fontsize",
            color=base_plot.COL_PLUM,
            alpha=0.4,
            fontsize=8,
            fontweight="bold",
            # style="italic",
            horizontalalignment="right",
            path_effects=self.PATH_EFFECTS,
        )

    def _plot_hr_bars(self):
        a: Axes = self._axes_mosaic["hr-bars"]

        ## FAST intervals.
        xdata_hr_avgs: list[float] = [
            _["averageHR"] for _ in self._s[0].typed_splits_extracted
        ]
        xdata_hr_avgs.append(fmean(xdata_hr_avgs))
        xdata_hr_maxs: list[int] = [
            _["maxHR"] for _ in self._s[0].typed_splits_extracted
        ]
        xdata_hr_maxs.append(fmean(xdata_hr_maxs))
        ydata_range = np.arange(len(xdata_hr_avgs))

        # Plot bar from avg HR to max HR.
        HR_AVG_GAP = 0.4
        bar = a.barh(
            y=self._ydata_for_barh_mixin(ydata_range, 0, 2),
            width=np.asarray(xdata_hr_maxs) - np.asarray(xdata_hr_avgs),
            height=self._bar_height_for_barh_mixin(0, 2),
            left=np.asarray(xdata_hr_avgs) + (HR_AVG_GAP / 2),
            color=[base_plot.COL_DARK_RED for _ in range(len(ydata_range) - 1)]
            + [base_plot.COL_DARK_GRAY],
            alpha=1,
        )
        a.bar_label(
            bar,
            labels=[round(x) for x in xdata_hr_maxs],
            padding=2,
            path_effects=self.PATH_EFFECTS,
        )
        # Plot bar from min HR to avg HR.
        xdata_hr_mins = []
        hr_stream = self._s[0].details_resp.get_heartrate_stream(
            do_remove_none_values=False
        )
        # The min HRs are not within the split data, so I have to extract them from
        #  the HR stream.
        for stream_indexes in self._s[0].typed_splits_stream_indexes:
            split_hr_stream = hr_stream[stream_indexes[0] : stream_indexes[1] + 1]
            xdata_hr_mins.append(min(split_hr_stream))
        xdata_hr_mins.append(fmean(xdata_hr_mins))
        ydata_range_fast_for_barh_mixin = self._ydata_for_barh_mixin(ydata_range, 0, 2)
        bar = a.barh(
            y=ydata_range_fast_for_barh_mixin,
            width=np.asarray(xdata_hr_avgs)
            - np.asarray(xdata_hr_mins)
            - (HR_AVG_GAP / 2),
            height=self._bar_height_for_barh_mixin(0, 2),
            left=xdata_hr_mins,
            color=[base_plot.COL_DARK_RED for _ in range(len(ydata_range) - 1)]
            + [base_plot.COL_DARK_GRAY],
            alpha=1,
        )
        a.bar_label(
            bar,
            labels=[round(x) for x in xdata_hr_avgs],
            padding=-7,
            path_effects=self.PATH_EFFECTS,
        )
        # Add the min HR bar labels.
        for i in range(len(ydata_range_fast_for_barh_mixin)):
            a.annotate(
                round(xdata_hr_mins[i]),
                (xdata_hr_mins[i], ydata_range_fast_for_barh_mixin[i]),
                xytext=(-0.3, -0.3),
                textcoords="offset fontsize",
                # color=base_plot.COL_PLUM,
                # alpha=0.9,
                # fontsize=8,
                # fontweight="bold",
                # style="italic",
                horizontalalignment="right",
                path_effects=self.PATH_EFFECTS,
            )

        ## HR MAX DROP.
        slow_int_hr_mins = []
        for i in range(len(self._s[0].typed_splits_stream_indexes) - 1):
            start_ix = self._s[0].typed_splits_stream_indexes[i][1]
            end_ix = self._s[0].typed_splits_stream_indexes[i + 1][0]
            slow_hr_stream = hr_stream[start_ix : end_ix + 1]
            slow_int_hr_mins.append(min(slow_hr_stream))
        _avg = fmean(slow_int_hr_mins)
        slow_int_hr_mins.append(0)
        slow_int_hr_mins.append(round(_avg))
        assert len(slow_int_hr_mins) == len(xdata_hr_maxs)  # TODO raise custom exc.
        hr_drops = []
        for i in range(len(slow_int_hr_mins)):
            if slow_int_hr_mins[i] == 0:
                hr_drops.append(0)
            else:
                hr_drops.append(round(xdata_hr_maxs[i] - slow_int_hr_mins[i]))
        atwiny_hr_drop: Axes = a.twiny()
        ydata_range_drop_for_barh_mixin = self._ydata_for_barh_mixin(ydata_range, 1, 2)
        bar = atwiny_hr_drop.barh(
            y=ydata_range_drop_for_barh_mixin,
            width=hr_drops,
            height=self._bar_height_for_barh_mixin(1, 2),
            # left=xdata_hr_mins,
            color=[base_plot.COL_DARK_RED for _ in range(len(ydata_range) - 1)]
            + [base_plot.COL_DARK_GRAY],
            alpha=0.4,
        )
        atwiny_hr_drop.bar_label(
            bar,
            padding=2,
            fontsize=8,
            color="gray",
            alpha=0.7,
            path_effects=self.PATH_EFFECTS,
        )

        ## Format.
        # Invert the y-axis so the 1st attempt is on top.
        a.invert_yaxis()
        a.set_xlabel("HR min|avg|max, drop [bpm]", fontsize=9, labelpad=10)
        # Set the x-axis label to the top.
        a.xaxis.set_label_position("top")
        # Use log scale to amplify the small differences.
        # Using a diff base for the log does NOT change the chart.
        # Note: do not use log scale in this case as it flattens the max HR.
        # a.set_xscale("log")  # Add a base with arg: `base=2`.
        atwiny_hr_drop.set_xscale("log")
        atwiny_hr_drop.set_axis_off()
        # Set the start and end scale for the x-axis, adding 2% width to make
        #  space for the bar labels.
        max_hr = max(xdata_hr_maxs)
        min_hr = min(xdata_hr_mins)
        a.set_xlim((min_hr * 0.92, max_hr * 1.03))
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
        # Hide all spines except the left one.
        a.spines[["right", "top", "bottom"]].set_visible(False)

        # Set only the first y tick labels as: "FAST|drop".
        a.annotate(
            f"{self.distance}m",
            (a.get_xlim()[0], ydata_range_fast_for_barh_mixin[0]),
            xytext=(-0.3, -0.4),
            textcoords="offset fontsize",
            color=base_plot.COL_DARK_RED,
            alpha=0.9,
            fontsize=8,
            fontweight="bold",
            # style="italic",
            horizontalalignment="right",
            path_effects=self.PATH_EFFECTS,
        )
        a.annotate(
            "drop",
            (a.get_xlim()[0], ydata_range_drop_for_barh_mixin[0]),
            xytext=(-0.3, -0.4),
            textcoords="offset fontsize",
            color=base_plot.COL_DARK_RED,
            alpha=0.4,
            fontsize=8,
            fontweight="bold",
            # style="italic",
            horizontalalignment="right",
            path_effects=self.PATH_EFFECTS,
        )

        # Add note about definition of HR drop.
        a.annotate(
            r"drop := max(HR) fast int. - min(HR) rest int.",
            ((a.get_xlim()[1] + a.get_xlim()[0]) / 2, a.get_ylim()[1]),
            xytext=(0, 0),
            textcoords="offset fontsize",
            # color=base_plot.COL_DARK_RED,
            # alpha=0.4,
            fontsize=8,
            # fontweight="bold",
            style="italic",
            horizontalalignment="center",
            # path_effects=self.PATH_EFFECTS,
        )

    def _plot_hr_zones(self):
        hr_stream = self._s[0].details_resp.get_heartrate_stream(
            # None values cause exceptions in self._plot_hr_zones_mixin().
            do_remove_none_values=False
        )
        xdata_hr = []
        for split_indexes in self._s[0].typed_splits_stream_indexes:
            xdata_hr.extend(hr_stream[split_indexes[0] : split_indexes[1] + 1])

        self._plot_hr_zones_mixin(
            self._axes_mosaic["hr-zones"],
            xdata_hr,
            settings.HR_MIN,
            settings.HR_MAX_EVER_RUN,
            text_prefix="Time in zones, fast intervals only\n",
            text_position="TOP_CENTER",
        )

    def plot(self, save_to_png_file_path: Path | str | None = None):
        ## Find the actual Garmin activity, if the garmin id arg was LATEST or LATEST-3.
        original_garmin_activity_id_arg = self.garmin_activity_id
        if (
            # original_garmin_activity_id_arg is a tuple like ("LATEST", 0) or ("LATEST", -3).
            isinstance(original_garmin_activity_id_arg, tuple)
            and original_garmin_activity_id_arg[0] == "LATEST"
        ):
            # Get N-most recent running activity from Garmin API.
            self.garmin_activity_id = self._api_search_activities(
                activity_type="running",
                n_results=abs(original_garmin_activity_id_arg[1]) + 1,
            )[-1]
        self.print_activity_urls(
            original_activity_id_arg=original_garmin_activity_id_arg,
            garmin_activity_id=self.garmin_activity_id,
            activity_txt_to_print="run",
        )

        ## Collect activity's typed splits and summary.
        self._s.append(
            CollectedData(
                summary_resp=self._api_get_activity_summary(self.garmin_activity_id),
                details_resp=self._api_get_activity_details(
                    self.garmin_activity_id,
                    max_metrics_data_count=100 * 1000,
                ),
                typed_splits_resp=self._api_get_activity_typed_splits(
                    self.garmin_activity_id
                ),
            )
        )

        # Print dates to console.
        self.print_activity_date(self._s[0].summary_resp.summary["startTimeLocal"])

        ## Extract all typed splits.
        typed_splits = self._get_splits_for_activity_typed_splits_response(
            self._s[0].typed_splits_resp,
            # Usually we want to check the n of extracted splits vs the expected
            #  one only for the given activity, not for the old activity to compare.
            do_raise_if_n_split_not_expected=True,
        )
        self._s[0].typed_splits_extracted = typed_splits

        # Find the matching stream start and end indexes for each typed split.
        for split in self._s[0].typed_splits_extracted:

            start_ix, end_ix = (
                find_matching_stream_start_and_end_indexes_for_typed_split(
                    split, self._s[0].details_resp
                )
            )
            self._s[0].typed_splits_stream_indexes.append((start_ix, end_ix))

        # Figure.
        figure, self._axes_mosaic = self._make_subplot_mosaic()
        figure: Figure
        self._axes_mosaic: dict[str, Axes]

        # All plots.
        self._plot_pace()
        self._plot_time_bars()
        self._plot_hr_bars()
        self._plot_hr_zones()
        # self._print_intervals()  # TODO mi serve davvero?? Non penso

        # Title and subtitle.
        title = _make_title(
            activity_original_title=self._s[0].summary_resp.data["activityName"],
            custom_title=self.title,
        )
        figure.suptitle(title + "\n  ", fontweight="bold")
        subtitle = _make_subtitle(
            activity_original_start_time_local=self._s[0].summary_resp.summary[
                "startTimeLocal"
            ],
            activity_original_moving_duration=self._s[0].summary_resp.summary[
                "movingDuration"
            ],
            activity_original_elapsed_duration=self._s[0].summary_resp.summary[
                "elapsedDuration"
            ],
            activity_original_distance=self._s[0].summary_resp.summary["distance"],
        )
        figure.text(
            figure.get_figwidth() / 2,  # Inches.
            figure.get_figheight() - 0.35,  # Inches.
            subtitle,
            fontsize=9,
            horizontalalignment="center",
            transform=figure.dpi_scale_trans,  # Use inches as figure size.
        )

        # Finally save.
        if save_to_png_file_path:
            self.print_created_image_path(save_to_png_file_path)
            plt.savefig(save_to_png_file_path)
        else:
            plt.show()

    def _make_figure_size(self) -> tuple[float, float]:
        # height = max(len(self._s), 3.5) * 2.1
        return 8, 7  # width, height.

    def _make_subplot_mosaic(self) -> tuple[Figure, dict[str, Axes]]:
        figsize = self.figure_size or self._make_figure_size()
        console.print(
            f":triangular_ruler: Figure size: {', '.join([str(round(x, 2)) for x in figsize])}"
        )

        # Docs for subplot_mosaic():
        #  https://matplotlib.org/stable/users/explain/axes/arranging_axes.html#variable-widths-or-heights-in-a-grid
        #  https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplot_mosaic.html#matplotlib.pyplot.subplot_mosaic
        return plt.subplot_mosaic(
            # fmt: off
    [
                # 1 rows, 1 col.
                ["pace",      "pace"],
                ["time-bars", "hr-bars"],
                ["hr-zones",  "hr-zones"]
            ],
            # fmt: on
            gridspec_kw=dict(
                # The relative sizes of the subplots.
                width_ratios=[1, 1],
                height_ratios=[0.3, 1, 0.1],
            ),
            figsize=figsize,
            layout="constrained",
        )

    def _fmt_pace(self, pace_mps: float):
        if pace_mps == 0:
            return 0
        x = speed_utils.mps_to_minpkm_base10(pace_mps)
        return speed_utils.minpkm_base10_to_base60(x)

    def _fmt_delta_pace(self, seconds: float):
        mm_ss = datetime_utils.seconds_to_hh_mm_ss(
            round(seconds), do_hide_hours_and_mins_if_zero=True
        )
        math_txt = rf"$\Delta$={mm_ss}"
        return math_txt

    def _fmt_time(self, seconds: float):
        if seconds > 60:
            return datetime_utils.seconds_to_hh_mm_ss(round(seconds))[3:]
        return f"{seconds:.2f}"


# TODO move this to Garmin Connect lib.
def find_matching_stream_start_and_end_indexes_for_typed_split(
    split: dict, details_resp: ActivityDetailsResponse
) -> tuple[int, int]:
    """
    Given a typed split (extracted from ActivityTypedSplitsResponse.splits or
     ActivityTypedSplitsResponse.get_interval_active_splits()), it gets the matching
     start and end indexes to be used in the streams returned by ActivityDetailsResponse.

    Use case: suppose I want to compute the HR avg or the pace in the slow intervals
     between two fast intervals that were tracked as typed split (because I pressed
     the lap button). Then I have to extract the start and end indexes of those typed
     split, then analyze the ActivityDetailsResponse.get_heartrate_stream() but slicing
     from the end indx of the first fast interval and the start index of the second fast
     interval.

    Args:
        split: the dict returned by ActivityTypedSplitsResponse.splits or
         ActivityTypedSplitsResponse.get_interval_active_splits()
        details_resp: the ActivityDetailsResponse for the same activity that the split
         belongs to.

    Returns: a tuple with the start and end indexes.
    """
    # Find the start and end timestamps of split.
    start_dt = datetime_utils.parse_datetime_arg(
        split["startTimeGMT"], is_naive_allowed=True
    ).replace(tzinfo=timezone.utc)
    start_ts = datetime_utils.utc_date_to_timestamp(start_dt)
    end_dt = datetime_utils.parse_datetime_arg(
        split["endTimeGMT"], is_naive_allowed=True
    ).replace(tzinfo=timezone.utc)
    end_ts = datetime_utils.utc_date_to_timestamp(end_dt)

    # Find what indexes, in the ts_stream, match the start and end timestamp.
    start_ix = end_ix = None
    for i, ts in enumerate(details_resp.get_ts_stream()):
        if start_ix is None and ts >= start_ts * 1000:
            start_ix = i
        if end_ix is None and ts >= end_ts * 1000:
            end_ix = i
            break

    return start_ix, end_ix


class BasePlotDistIntervalRunApiCmdException(Exception): ...


class NumberOfExpectedIntervalsError(BasePlotDistIntervalRunApiCmdException): ...


class IntervalDistanceNotSupported(BasePlotDistIntervalRunApiCmdException): ...
