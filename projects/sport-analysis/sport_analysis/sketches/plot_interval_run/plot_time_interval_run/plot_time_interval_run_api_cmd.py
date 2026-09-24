from dataclasses import dataclass
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
from garmin_connect_client import ActivityDetailsResponse, ActivitySummaryResponse
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


@dataclass
class CollectedData:
    summary_resp: ActivitySummaryResponse = None
    details_resp: ActivityDetailsResponse = None


class PlotTimeIntervalRunApiCmd(
    base_api.MixinGarminRequestsApi, base_plot.MixinBarHPlot
):
    """
    Plots to support the analysis of a time interval run activity performance.
    """

    def __init__(
        self,
        # id (int) of Garmin activity to analyze or ("LATEST", 0) or ("LATEST", -3).
        garmin_activity_id: int | tuple[str, int],
        # intervals_plan=intervals_plan, # TODO
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

        # TODO I should add the arg `trim_by_elapsed_time=(0, 32*60)` that allows me to
        #  trim the activity by time. Now it's temporarily hardcoded.
        ix_start = 0
        ix_end = 0
        for i, elapsed_time in enumerate(xdata_elapsed_time):
            if elapsed_time >= 32 * 60:
                ix_end = i
                break
        xdata_elapsed_time = xdata_elapsed_time[ix_start : ix_end + 1]
        _speed_stream = _speed_stream[ix_start : ix_end + 1]
        assert len(xdata_elapsed_time) == len(_speed_stream)

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
            ydata_hr = ydata_hr[ix_start : ix_end + 1]

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

            # Write text annotation for PACE and HR with the matching colors..
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

        # Draw intervals as gray background areas.
        for i in range(0, 32, 2):
            a.axvspan(
                i * 60,
                (i * 60) + 60,
                color="grey",
                alpha=0.2,
            )

    def _plot_pace_bars(self):
        # TODO rivedi tutti i commenti in questo metodo, xche li ho scopiazzati.

        elapsed_time_stream = self._s[0].details_resp.get_elapsed_time_stream()
        distance_stream = self._s[0].details_resp.get_distance_stream()

        ## Campute the intervas data: pace and HR.
        # TODO raise exception
        assert len(elapsed_time_stream) == len(distance_stream)

        # TODO these 2 should be instance vars and be filled here and in _plot_hr_bars()
        #  and the used in _print_intervals
        fast_intervals = dict(
            paces=[],
        )
        slow_intervals = dict(
            paces=[],
            pace_deltas=[],
        )

        ix_start = ix_end = 0
        interval_count = 1
        for ix, elapsed_time in enumerate(elapsed_time_stream):
            if elapsed_time >= (60 * interval_count):
                ix_start = ix_end
                ix_end = ix

                interval_time = (
                    elapsed_time_stream[ix_end] - elapsed_time_stream[ix_start]
                )
                interval_distance = distance_stream[ix_end] - distance_stream[ix_start]
                pace_mps = interval_distance / interval_time
                # pace_minpkm = speed_utils.minpkm_base10_to_base60(
                #     speed_utils.mps_to_minpkm_base10(pace_mps)
                # )

                # Check if it was a fast or slow interval.
                if interval_count % 2 == 1:
                    # print(f"{interval_count} % 2 == 0")
                    fast_intervals["paces"].append(pace_mps)
                else:
                    # print(f"{interval_count} % 2 != 0")
                    slow_intervals["paces"].append(pace_mps)

                # print(f"Interval: {interval_count}")
                # print(f"Duration: {interval_time}")
                # print(f"Distance: {round(interval_distance)}")
                # print(f"Pace: {pace_minpkm}/km")

                # print("\n\n")
                interval_count += 1

            if interval_count >= 33:
                break

        ## Plot.
        a: Axes = self._axes_mosaic["pace-bars"]

        ydata_range = np.arange(len(fast_intervals["paces"]) + 1)

        # Plot main activity's times.
        bar = a.barh(
            self._ydata_for_barh_mixin(ydata_range, 0, 3),
            fast_intervals["paces"] + [fmean(fast_intervals["paces"])],
            self._bar_height_for_barh_mixin(0, 3),
            # label=self._make_legend_label(0),
            color=[base_plot.COL_PLUM for _ in range(len(ydata_range) - 1)]
            + [base_plot.COL_DARK_GRAY],
            alpha=1.0,
        )
        # Add the main activity's time values at the right of each bar.
        a.bar_label(bar, fmt=self._fmt_pace, padding=2, path_effects=self.PATH_EFFECTS)

        bar = a.barh(
            self._ydata_for_barh_mixin(ydata_range, 1, 3),
            slow_intervals["paces"] + [fmean(slow_intervals["paces"])],
            self._bar_height_for_barh_mixin(1, 3),
            # color="gray",
            color=[base_plot.COL_PLUM for _ in range(len(ydata_range) - 1)]
            + [base_plot.COL_DARK_GRAY],
            alpha=0.6,
        )
        a.bar_label(
            bar,
            fmt=self._fmt_pace,
            padding=2,
            fontsize=8,
            color="gray",
            alpha=0.7,
            path_effects=self.PATH_EFFECTS,
        )

        for i in range(len(fast_intervals["paces"])):
            fast_pace_mps = fast_intervals["paces"][i]
            slow_pace_mps = slow_intervals["paces"][i]
            delta_sec = (
                speed_utils.mps_to_minpkm_base10(slow_pace_mps)
                - speed_utils.mps_to_minpkm_base10(fast_pace_mps)
            ) * 60
            slow_intervals["pace_deltas"].append(delta_sec)
        atwiny_pace_delta: Axes = a.twiny()
        bar = atwiny_pace_delta.barh(
            self._ydata_for_barh_mixin(ydata_range, 2, 3),
            slow_intervals["pace_deltas"] + [fmean(slow_intervals["pace_deltas"])],
            self._bar_height_for_barh_mixin(2, 3),
            color=[base_plot.COL_PLUM for _ in range(len(ydata_range) - 1)]
            + [base_plot.COL_DARK_GRAY],
            alpha=0.3,
        )
        atwiny_pace_delta.bar_label(
            bar,
            fmt=self._fmt_delta_pace,
            padding=2,
            fontsize=8,
            color="gray",
            alpha=0.7,
            path_effects=self.PATH_EFFECTS,
        )

        max_pace = max(fast_intervals["paces"])

        ## Format.
        # Invert the y-axis so the 1st attempt is on top.
        a.invert_yaxis()
        a.set_xlabel("Pace [min/km], log scale", fontsize=9)
        # Set the x-axis label to the top.
        a.xaxis.set_label_position("top")
        # Use log scale to amplify the small differences.
        # Using a diff base for the log does NOT change the chart.
        a.set_xscale("log")  # Add a base with arg: `base=2`.
        atwiny_pace_delta.set_xscale("log")
        atwiny_pace_delta.set_axis_off()
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
            # labelleft=False,
        )

        # Prepare the y tick labels as: "1st", "2nd", ... "avg".
        y_ticks_labels = [number_utils.ordinal(_) for _ in range(1, len(ydata_range))]
        y_ticks_labels += ["avg"]
        a.set_yticks(ydata_range, labels=y_ticks_labels)

    def _plot_hr_bars(self):
        # TODO rivedi tutti i commenti in questo metodo, xche li ho scopiazzati.

        elapsed_time_stream = self._s[0].details_resp.get_elapsed_time_stream()
        hr_stream = self._s[0].details_resp.get_heartrate_stream(
            do_remove_none_values=False
        )

        ## Campute the intervas data: pace and HR.
        # TODO raise exception
        assert len(elapsed_time_stream) == len(hr_stream)

        fast_intervals = dict(
            hrs_avg=[],
            hrs_max=[],
        )
        slow_intervals = dict(
            hrs_avg=[],
            hrs_min=[],
            hr_deltas=[],
        )

        ix_start = ix_end = 0
        interval_count = 1
        for ix, elapsed_time in enumerate(elapsed_time_stream):
            if elapsed_time >= (60 * interval_count):
                ix_start = ix_end
                ix_end = ix

                hr_avg = fmean(hr_stream[ix_start : ix_end + 1])

                # Check if it was a fast or slow interval.
                if interval_count % 2 == 1:  # Fast interval.
                    hr_max = max(hr_stream[ix_start : ix_end + 1])
                    fast_intervals["hrs_avg"].append(hr_avg)
                    fast_intervals["hrs_max"].append(hr_max)
                else:  # Slow interval.
                    hr_min = min(hr_stream[ix_start : ix_end + 1])
                    slow_intervals["hrs_avg"].append(hr_avg)
                    slow_intervals["hrs_min"].append(hr_min)

                interval_count += 1

            if interval_count >= 33:
                break

        ## Plot.
        a: Axes = self._axes_mosaic["hr-bars"]

        ydata_range = np.arange(len(fast_intervals["hrs_avg"]) + 1)

        bar = a.barh(
            self._ydata_for_barh_mixin(ydata_range, 0, 3),
            fast_intervals["hrs_max"] + [fmean(fast_intervals["hrs_max"])],
            self._bar_height_for_barh_mixin(0, 3),
            color=[base_plot.COL_DARK_RED for _ in range(len(ydata_range) - 1)]
            + [base_plot.COL_DARK_GRAY],
            alpha=0.6,
        )
        # Add main activity's maxes HR values at the right of each bar.
        a.bar_label(bar, fmt="{0:.0f}", padding=2, path_effects=self.PATH_EFFECTS)

        bar = a.barh(
            self._ydata_for_barh_mixin(ydata_range, 0, 3),
            fast_intervals["hrs_avg"] + [fmean(fast_intervals["hrs_avg"])],
            self._bar_height_for_barh_mixin(0, 3),
            # label=self._make_legend_label(0),
            color=[base_plot.COL_DARK_RED for _ in range(len(ydata_range) - 1)]
            + [base_plot.COL_DARK_GRAY],
            alpha=1.0,
        )
        # Add the main activity's time values at the right of each bar.
        a.bar_label(bar, fmt="{0:.0f}", padding=2, path_effects=self.PATH_EFFECTS)

        bar = a.barh(
            self._ydata_for_barh_mixin(ydata_range, 1, 3),
            slow_intervals["hrs_avg"] + [fmean(slow_intervals["hrs_avg"])],
            self._bar_height_for_barh_mixin(1, 3),
            color=[base_plot.COL_DARK_RED for _ in range(len(ydata_range) - 1)]
            + [base_plot.COL_DARK_GRAY],
            alpha=0.4,
        )
        a.bar_label(
            bar,
            fmt="{0:.0f}",
            padding=2,
            fontsize=8,
            color="gray",
            alpha=0.7,
            path_effects=self.PATH_EFFECTS,
        )
        bar = a.barh(
            self._ydata_for_barh_mixin(ydata_range, 1, 3),
            slow_intervals["hrs_min"] + [fmean(slow_intervals["hrs_min"])],
            self._bar_height_for_barh_mixin(1, 3),
            color=[base_plot.COL_DARK_RED for _ in range(len(ydata_range) - 1)]
            + [base_plot.COL_DARK_GRAY],
            alpha=0.7,
        )
        a.bar_label(
            bar,
            fmt="{0:.0f}",
            padding=2,
            fontsize=8,
            color="gray",
            alpha=0.7,
            path_effects=self.PATH_EFFECTS,
        )

        ###############
        for i in range(len(fast_intervals["hrs_max"])):
            fast_pace_hrs_max = fast_intervals["hrs_max"][i]
            slow_pace_hrs_min = slow_intervals["hrs_min"][i]
            delta = fast_pace_hrs_max - slow_pace_hrs_min
            slow_intervals["hr_deltas"].append(delta)
        atwiny_hr_delta: Axes = a.twiny()
        bar = atwiny_hr_delta.barh(
            self._ydata_for_barh_mixin(ydata_range, 2, 3),
            slow_intervals["hr_deltas"] + [fmean(slow_intervals["hr_deltas"])],
            self._bar_height_for_barh_mixin(2, 3),
            color=[base_plot.COL_DARK_RED for _ in range(len(ydata_range) - 1)]
            + [base_plot.COL_DARK_GRAY],
            alpha=0.2,
        )
        atwiny_hr_delta.bar_label(
            bar,
            fmt=r"$\Delta$=" + "{0:.0f}",
            padding=2,
            fontsize=8,
            color="gray",
            alpha=0.7,
            path_effects=self.PATH_EFFECTS,
        )
        ##############
        max_hr = max(fast_intervals["hrs_max"])

        ## Format.
        # Invert the y-axis so the 1st attempt is on top.
        a.invert_yaxis()
        a.set_xlabel(
            "HR avg|max in fast intervals [bpm], log scale\nHR min|avg in slow intervals [bpm], log scale",
            fontsize=9,
        )
        # Set the x-axis label to the top.
        a.xaxis.set_label_position("top")
        # Use log scale to amplify the small differences.
        # Using a diff base for the log does NOT change the chart.
        a.set_xscale("log")  # Add a base with arg: `base=2`.
        atwiny_hr_delta.set_xscale("log")
        atwiny_hr_delta.set_axis_off()
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

        ## Collect MAIN activity's time splits and summary.
        self._s.append(
            CollectedData(
                summary_resp=self._api_get_activity_summary(self.garmin_activity_id),
                details_resp=self._api_get_activity_details(
                    self.garmin_activity_id,
                    max_metrics_data_count=100 * 1000,
                ),
            )
        )

        # Print dates to console.
        self.print_activity_date(self._s[0].summary_resp.summary["startTimeLocal"])

        # Figure.
        figure, self._axes_mosaic = self._make_subplot_mosaic()
        figure: Figure
        self._axes_mosaic: dict[str, Axes]

        # All plots.
        self._plot_pace()
        self._plot_pace_bars()
        self._plot_hr_bars()
        # self._print_intervals()  # TODO

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
        return 10, 10  # width, height.

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
                ["pace", "pace"],
                ["pace-bars", "hr-bars"],
            ],
            # fmt: on
            gridspec_kw=dict(
                # The relative sizes of the subplots.
                width_ratios=[1, 1],
                height_ratios=[0.3, 1],
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
