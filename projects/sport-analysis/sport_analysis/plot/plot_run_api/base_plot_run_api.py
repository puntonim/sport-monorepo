from abc import ABC
from dataclasses import dataclass
from pathlib import Path

import datetime_utils
import log_utils as logger
import matplotlib as mpl
import matplotlib.pyplot as plt
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

from .. import base_api

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


@dataclass
class CollectedData:
    summary_resp: ActivitySummaryResponse = None
    details_resp: ActivityDetailsResponse = None


class BasePlotRunApi(ABC, base_api.MixinGarminRequestsApi):
    """
    Plot charts to support the analysis of a half-marathon run activity performance,
     optionally compared with previous activities.
    """

    # IMP: TO BE DEFINED IN sub-classes.
    DEFAULT_ACTIVITY_IDS_TO_COMPARE: list[int] | None = None

    def __init__(
        self,
        garmin_activity_id: int,
        activity_ids_to_compare: list[int] | None = None,
        title: str | None = None,
        figure_size: tuple[float, float] | None = None,
        pace_plot_set_y_axis_bottom_to_slowest_pace_perc: float | None = None,
        garmin_connect_token_manager: (
            FileGarminConnectTokenManager | FakeTestGarminConnectTokenManager | None
        ) = None,
    ):
        """
        Args:
            garmin_activity_id: id of Garmin activity to analyze.
            activity_ids_to_compare: list of previous activities to compare
             to the given activity. Default: a hardcoded list.
            title: plot title.
            pace_plot_set_y_axis_bottom_to_slowest_pace_perc: eg. 0.45. In the
             MA(pace) chart, cutting out of the visible part of the chart the slowest
             0.45% pace datapoints. This is done because it is better visually: the
             chart is less compressed vertically.
            figure_size: customize the figure size, eg. (3.0, 5.5).
            garmin_connect_token_manager: use FakeTestGarminConnectTokenManager when
             replaying VCR episodes.
        """
        super().__init__(garmin_connect_token_manager)

        self.garmin_activity_id = garmin_activity_id
        self.activity_ids_to_compare = activity_ids_to_compare
        if self.activity_ids_to_compare is None:
            self.activity_ids_to_compare = self.DEFAULT_ACTIVITY_IDS_TO_COMPARE or []
        self.title = title
        self.figure_size = figure_size
        self.pace_plot_set_y_axis_bottom_to_slowest_pace_perc = (
            pace_plot_set_y_axis_bottom_to_slowest_pace_perc
        )

        # It's the store for responses collected for all activities.
        self._s: list[CollectedData] = []

        # Matplotlib axes mosaic. This figure is made of 3 charts in 2 rows and 1 col.
        #  These _axes_mosaic represent these 2 rows and 1 col.
        #  Each item in the _axes_mosaic dict is an Axes instance: the x-axis and y-axis
        #  of an actual chart.
        self._axes_mosaic: dict[str, Axes]

    def _plot_pace(self):
        a: Axes = self._axes_mosaic["pace"]

        _y_axis_bottom = 0

        ## MAIN activity.
        # X and y data.
        xdata_distance = self._s[0].details_resp.get_distance_stream()
        # Y data should be the moving average of the pace, compute from the speed.
        _speed_stream = self._s[0].details_resp.get_speed_stream(
            do_remove_none_values=False
        )
        # Compute the moving average for the speed stream.
        # Set the window size to 120 datapoints, which is roughly 2 minutes,
        #  however we will compute the windows size in meters and seconds later on.
        _rolling_window_size = 60 * 2
        # Convert to DataFrame.
        ydata_pace_df = pd.DataFrame(_speed_stream, columns=["pace"])
        del _speed_stream
        # Convert from m/s to min/km.
        ydata_pace_df = speed_utils.mps_to_minpkm_base10(ydata_pace_df)
        ydata_pace_df["MA(pace)"] = (
            ydata_pace_df["pace"].rolling(_rolling_window_size, center=True).mean()
        )
        del ydata_pace_df["pace"]

        # We want to print some info about how large is the rolling window, so we
        #  compute the avg window size in meters and in seconds.
        rolling_window_avg_distance = (
            pd.DataFrame(xdata_distance)
            # Apply the same rolling window as MA(pace) to the distance stream.
            .rolling(window=_rolling_window_size, center=True)
            # And compute the diff in meters between the last and the first datapoint in the window.
            .apply(lambda x: x.iloc[-1] - x.iloc[0]).mean()[0]
        )
        elapsed_time_stream = self._s[0].details_resp.get_elapsed_time_stream()
        rolling_window_avg_time = (
            pd.DataFrame(elapsed_time_stream)
            # Apply the same rolling window as MA(pace) to the time stream.
            .rolling(window=_rolling_window_size, center=True)
            # And compute the diff in seconds between the last and the first datapoint in the window.
            .apply(lambda x: x.iloc[-1] - x.iloc[0]).mean()[0]
        )

        # Compute the y-axis bottom.
        # Setting the bottom of y-axis to the best pace of the lowest 0.5% pace
        #  datapoint. In simpler words: cutting out of the visible part of the chart
        #  the slowest 0.5% pace datapoints. This is done because it is better
        #  visually: the chart is less compressed vertically.
        if self.pace_plot_set_y_axis_bottom_to_slowest_pace_perc:
            _y_axis_bottom = (
                ydata_pace_df["MA(pace)"]
                # Get the 0.5% largest datapoints, so the slowest paces.
                .nlargest(
                    round(
                        ydata_pace_df["MA(pace)"].size
                        / 100
                        * self.pace_plot_set_y_axis_bottom_to_slowest_pace_perc
                    )
                )
                # And get the last one, so the fastest of the slowest 0.5% paces.
                .iloc[-1]
            )

        # Plot pace.
        a.plot(
            xdata_distance,
            ydata_pace_df["MA(pace)"],
            label=self._make_legend_label(0),
            color="red",
            alpha=0.6,
            linewidth=3.0,
        )

        ## SECONDARY activities.
        for i in range(1, len(self._s)):
            details = self._s[i].details_resp
            # summary = self._s[i].summary_resp

            # X and y data.
            xdata_distance = details.get_distance_stream()
            _speed_stream = details.get_speed_stream(do_remove_none_values=False)
            # Convert to DataFrame.
            ydata_pace_df = pd.DataFrame(_speed_stream, columns=["pace"])
            del _speed_stream
            # Convert from m/s to min/km.
            ydata_pace_df = speed_utils.mps_to_minpkm_base10(ydata_pace_df)
            ydata_pace_df["MA(pace)"] = (
                ydata_pace_df["pace"].rolling(_rolling_window_size, center=True).mean()
            )
            del ydata_pace_df["pace"]

            a.plot(
                xdata_distance,
                ydata_pace_df["MA(pace)"],
                label=self._make_legend_label(i),
                # color="gray",
                color=COLS_SECONDARY[i - 1][0],
                alpha=COLS_SECONDARY[i - 1][1],
            )

            # Update the y-axis bottom.
            # Setting the bottom of y-axis to the best pace of the lowest 0.5% pace
            #  datapoint. In simpler words: cutting out of the visible part of the chart
            #  the slowest 0.5% pace datapoints. This is done because it is better
            #  visually: the chart is less compressed vertically.
            if self.pace_plot_set_y_axis_bottom_to_slowest_pace_perc:
                _y_axis_bottom_tmp = (
                    ydata_pace_df["MA(pace)"]
                    # Get the 0.5% largest datapoints, so the slowest paces.
                    .nlargest(
                        round(
                            ydata_pace_df["MA(pace)"].size
                            / 100
                            * self.pace_plot_set_y_axis_bottom_to_slowest_pace_perc
                        )
                    )
                    # And get the last one, so the fastest of the slowest 0.5% paces.
                    .iloc[-1]
                )
                _y_axis_bottom = (
                    _y_axis_bottom_tmp
                    if _y_axis_bottom_tmp > _y_axis_bottom
                    else _y_axis_bottom
                )

        ## Format.
        # Axes labels.
        a.set_ylabel("MA(pace) [min/km]")
        a.set_xlabel("distance [km]")
        # axes.xaxis.set_label_position("top")
        # Invert the y-axis so the fastest pace is on top.
        a.invert_yaxis()
        # Convert the y-axis ticks to pace in min/km (so from base10 to base60).
        a.yaxis.set_major_formatter(
            mpl.ticker.FuncFormatter(
                lambda x, pos: speed_utils.minpkm_base10_to_base60(x)
            )
        )
        a.yaxis.grid(color="gray", alpha=0.2, linestyle="--")
        a.xaxis.set_major_formatter(
            mpl.ticker.FuncFormatter(lambda x, pos: round(x / 1000, 1))
        )

        # Setting the bottom of y-axis to the best pace of the lowest 0.5% pace found.
        if self.pace_plot_set_y_axis_bottom_to_slowest_pace_perc:
            a.set_ylim(bottom=_y_axis_bottom)

        # Draw pace avg horizontal line.
        # Compute pace avg.
        _speed_avg = self._s[0].summary_resp.summary["averageSpeed"]
        _pace_base10_avg = speed_utils.mps_to_minpkm_base10(_speed_avg)
        a.axhline(
            y=_pace_base10_avg,
            color=COL_DARK_RED,
            alpha=0.5,
            linestyle=":",
        )
        # Write text annotation for pace avg.
        a.annotate(
            f"avg {speed_utils.minpkm_base10_to_base60(_pace_base10_avg)}",
            (a.get_xlim()[0], _pace_base10_avg),
            xytext=(0.1, 0.2),
            textcoords="offset fontsize",
            color=COL_DARK_RED,
        )
        # Write text annotation for MA window size.
        a.annotate(
            f"MA window: ~{round(rolling_window_avg_time)}s, ~{round(rolling_window_avg_distance)}m",
            (a.get_xlim()[0], a.get_ylim()[0]),
            xytext=(0.1, 0.1),
            textcoords="offset fontsize",
            color=COL_DARK_RED,
            style="italic",
            fontsize=8,
        )

    def _plot_hr(self):
        a: Axes = self._axes_mosaic["hr"]

        ## MAIN activity.
        # X data.
        xdata_hr = self._s[0].details_resp.get_heartrate_stream(
            do_remove_none_values=False
        )
        # Note: I tested that the HR avg|min|max return here are very close to the ones
        #  computed directly from the HR stream.
        hr_avg = self._s[0].summary_resp.summary["averageHR"]
        hr_max = self._s[0].summary_resp.summary["maxHR"]

        # Plot HR.
        _n_bins = 10
        a.hist(
            xdata_hr,
            bins=_n_bins,
            weights=1 / len(xdata_hr) * np.ones(len(xdata_hr)),
            color="red",
            alpha=0.6,
        )

        ## Format axes based on the main activity only, so before plotting the
        #   secondary activities.
        # Ticks.
        a.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(xmax=1, decimals=0))
        a.yaxis.grid(color="gray", alpha=0.2, linestyle="--")
        a.xaxis.set_major_formatter(
            mpl.ticker.FuncFormatter(
                # Set label ticks as bpm and as % of HR max.
                lambda x, pos: f"{round(x)}\n{round(x*100/hr_max)}%"
            )
        )

        ## SECONDARY activities.
        for i in range(1, len(self._s)):
            details = self._s[i].details_resp
            summary = self._s[i].summary_resp

            # If the activity does not have a heart rate monitor, then I skip it.
            #  I chose this because data without HRM are unreliable and lower,
            #  so the effect on the chart is to visually reduce the differences.
            if not summary.has_heart_rate_monitor():
                continue

            # X data.
            xdata_hr = details.get_heartrate_stream(do_remove_none_values=False)
            # Plot HR.
            a.hist(
                xdata_hr,
                bins=_n_bins,
                weights=1 / len(xdata_hr) * np.ones(len(xdata_hr)),
                # color="gray",
                color=COLS_SECONDARY[i - 1][0],
                alpha=COLS_SECONDARY[i - 1][1],
            )

        ## Format.
        # Axes labels.
        a.set_xlabel("heart rate [bpm, % of max]")
        a.set_ylabel("frequency")

        # Draw HR avg vertical line.
        a.axvline(
            x=hr_avg,
            color=COL_DARK_RED,
            alpha=0.5,
            linestyle=":",
        )
        # Write text annotation for HR avg and max.
        a.annotate(
            f"avg\n{round(hr_avg)}\n{round(hr_avg*100/hr_max)}%",
            (hr_avg, a.get_ylim()[1]),
            xytext=(-2.2, -3.2),
            textcoords="offset fontsize",
            color=COL_DARK_RED,
        )
        a.annotate(
            f"max\n{round(hr_max)}",
            (hr_max, a.get_ylim()[1]),
            xytext=(-1.1, -2.2),
            textcoords="offset fontsize",
            color=COL_DARK_RED,
        )

    def plot(self, save_to_png_file_path: Path | None = None):
        ## Collect summary and details for MAIN and SECONDARY activities.
        for activity_id in [self.garmin_activity_id] + self.activity_ids_to_compare:
            self._s.append(
                CollectedData(
                    summary_resp=self._api_get_activity_summary(activity_id),
                    details_resp=self._api_get_activity_details(
                        activity_id,
                        max_metrics_data_count=100 * 1000,
                    ),
                )
            )

        # Figure.
        figure, self._axes_mosaic = self._make_subplot_mosaic()
        figure: Figure
        self._axes_mosaic: dict[str, Axes]

        # All plots.
        self._plot_pace()
        self._plot_hr()

        title = (
            self.title
            if self.title is not None
            else self._s[0].summary_resp.data["activityName"]
        )
        figure.suptitle(title)  # color=COL_DARK_RED

        # Docs on legend location:
        #  https://matplotlib.org/stable/users/explain/axes/legend_guide.html
        figure.legend(
            loc="outside lower left",
            ncol=1,
            frameon=False,
            fontsize=9,
            labelspacing=0.8,
        )
        # Customize legend to make it more visible: less alpha and larger line widths.
        for i in range(1, len(self._s)):
            figure.legends[0].legend_handles[i].set_alpha(0.8)
            figure.legends[0].legend_handles[i].set_linewidth(3.0)

        if save_to_png_file_path:
            logger.info(f"Created image: {save_to_png_file_path}")
            plt.savefig(save_to_png_file_path)
        else:
            plt.show()

    def _make_figure_size(self) -> tuple[float, float]:
        height = max(len(self._s), 3.5) * 2
        return 5, height

    def _make_subplot_mosaic(self) -> tuple[Figure, dict[str, Axes]]:
        # Docs for subplot_mosaic():
        #  https://matplotlib.org/stable/users/explain/axes/arranging_axes.html#variable-widths-or-heights-in-a-grid
        #  https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplot_mosaic.html#matplotlib.pyplot.subplot_mosaic
        return plt.subplot_mosaic(
            # fmt: off
    [
                # 2 rows, 1 col.
                ["pace", ],
                ["hr", ],
            ],
            # fmt: on
            gridspec_kw=dict(
                # The relative sizes of the subplots.
                width_ratios=[1],
                height_ratios=[1.5, 1],
            ),
            figsize=self._make_figure_size(),
            layout="constrained",
        )

    def _make_legend_label(self, activity_index: int) -> str:
        """
        Make the text used in the legend label for a plot.
        """
        ACTIVITY_NAME_MAX_LENGTH = 50
        summary = self._s[activity_index].summary_resp

        # Start date.
        legend_label = summary.summary["startTimeLocal"][:10]
        # Name.
        legend_label += " " + text_utils.truncate_text(
            summary.data["activityName"], ACTIVITY_NAME_MAX_LENGTH
        )
        # Pace, cadence, duration, distance.
        _speed_avg = summary.summary["averageSpeed"]
        pace_base10_avg = speed_utils.mps_to_minpkm_base10(_speed_avg)
        cadence = summary.summary["averageRunCadence"]
        duration = summary.summary["duration"]
        distance = summary.summary["distance"]
        legend_label += f"\n{speed_utils.minpkm_base10_to_base60(pace_base10_avg)}/km"
        legend_label += f" {round(cadence)}spm"
        legend_label += f" for {round(distance/1000, 2)}km"
        legend_label += f" in {datetime_utils.seconds_to_hh_mm_ss(round(duration))}"
        # HRM.
        if not summary.has_heart_rate_monitor():
            legend_label += " without HRM"
        else:
            hr_avg = summary.summary["averageHR"]
            hr_max = summary.summary["maxHR"]
            legend_label += f" at {round(hr_avg)}-{round(hr_max)}bpm"
        return legend_label


class BasePlotRunApiException(Exception):
    pass
