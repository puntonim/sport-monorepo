from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import datetime_utils
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import speed_utils
import text_utils
from garmin_connect_client import (
    ActivityDetailsResponse,
    ActivitySplitsResponse,
    ActivitySummaryResponse,
)
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.legend_handler import HandlerTuple
from rich import box
from rich.table import Table

from ...base_cli_view import ConsoleAdapter
from ...conf import settings
from .. import base_api, base_plot
from ..base_plot import PERCENTILE_TO_DRAW_ENUM, _make_subtitle, _make_title

console = ConsoleAdapter()


@dataclass
class CollectedData:
    summary_resp: ActivitySummaryResponse = None
    details_resp: ActivityDetailsResponse = None
    splits_resp: ActivitySplitsResponse | None = None


class PlotSimpleRunApiCmd(base_api.MixinGarminRequestsApi, base_plot.MixinHrPlot):
    """
    Plot charts to support the analysis of a half-marathon run activity performance,
     optionally compared with previous runs.
    """

    def __init__(
        self,
        # id (int) of Garmin activity to analyze or ("LATEST", 0) or ("LATEST", -3).
        garmin_activity_id: int | tuple[str, int],
        prev_runs_activity_ids_to_compare: Sequence[int] | None = None,
        percentile_to_draw: PERCENTILE_TO_DRAW_ENUM | str | None = None,
        # List of HR zones that are "disabled" by hatching (drawing 45deg grey lines).
        hr_zones_to_hatch: Sequence[str] | None = None,
        pace_plot_set_y_axis_bottom_to_slowest_pace_perc: float | None = None,
        title: str | None = None,
        figure_size: tuple[float, float] | None = None,
        garmin_connect_token_manager: (
            FileGarminConnectTokenManager | FakeTestGarminConnectTokenManager | None
        ) = None,
    ):
        """
        Args:
            garmin_activity_id: id (int) of Garmin activity to analyze or ("LATEST", 0)
             or ("LATEST", -3).
            prev_runs_activity_ids_to_compare: list of previous activities (runs) to
             compare to the given activity.
            percentile_to_draw: either P80 or P98 to draw as vertical line on the
             histogram. Note that both percentiles are always written as text under the
             histogram.
            hr_zones_to_hatch: list of HR zones that are "disabled" by hatching
             (drawing 45deg grey lines). Eg. ["Z3", "Z4", "Z5"].
            pace_plot_set_y_axis_bottom_to_slowest_pace_perc: eg. 0.45. In the
             MA(pace) chart, cutting out of the visible part of the chart the slowest
             0.45% pace datapoints. This is done because it is better visually: the
             chart is less compressed vertically.
            title: plot title.
            figure_size: customize the figure size, eg. (3.0, 5.5).
            garmin_connect_token_manager: use FakeTestGarminConnectTokenManager when
             replaying VCR episodes.
        """
        super().__init__(garmin_connect_token_manager)

        self.garmin_activity_id = garmin_activity_id
        self.prev_runs_activity_ids_to_compare = (
            prev_runs_activity_ids_to_compare or tuple()
        )
        self.title = title
        self.figure_size = figure_size or tuple()
        self.pace_plot_set_y_axis_bottom_to_slowest_pace_perc = (
            pace_plot_set_y_axis_bottom_to_slowest_pace_perc
        )

        ## Validate some args: hr_zones_to_hatch, percentile_to_draw.
        self.hr_zones_to_hatch = hr_zones_to_hatch or tuple()
        if self.hr_zones_to_hatch:
            for zone in hr_zones_to_hatch:
                if zone.upper() not in ("Z0", "Z1", "Z2", "Z3", "Z4", "Z5"):
                    raise ValueError(
                        f"hr_zones_to_hatch invalid: {zone}\nValid values: Z0 | Z1 | Z2 | Z3 | Z4 | Z5"
                    )
            self.hr_zones_to_hatch = tuple(x.upper() for x in hr_zones_to_hatch)
        self.percentile_to_draw = percentile_to_draw
        if (
            percentile_to_draw
            and percentile_to_draw.upper() not in PERCENTILE_TO_DRAW_ENUM
        ):
            raise ValueError(
                f"percentile_to_draw arg invalid: {percentile_to_draw}\nValid values: {' | '.join(PERCENTILE_TO_DRAW_ENUM)}"
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
            # color="red",
            color=base_plot.COL_PLUM,
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
                color=base_plot.COLS_SECONDARY[i - 1][0],
                alpha=base_plot.COLS_SECONDARY[i - 1][1],
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
        a.set_ylabel("Pace [min/km]")
        a.set_xlabel("Distance [km]")
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
            color=base_plot.COL_PLUM,
            alpha=0.5,
            linestyle=":",
        )
        # Write text annotation for pace avg.
        a.annotate(
            f"avg {speed_utils.minpkm_base10_to_base60(_pace_base10_avg)}",
            (a.get_xlim()[0], _pace_base10_avg),
            xytext=(0.1, 0.2),
            textcoords="offset fontsize",
            color=base_plot.COL_PLUM,
            fontsize=8,
            fontweight="bold",
        )
        # Write text annotation for MA window size.
        a.annotate(
            f"MA(pace) window: ~{round(rolling_window_avg_time)}s, ~{round(rolling_window_avg_distance)}m",
            (a.get_xlim()[0], a.get_ylim()[0]),
            xytext=(0.1, 0.1),
            textcoords="offset fontsize",
            # color=base_plot.COL_DARK_RED,
            style="italic",
            fontsize=8,
        )

    def _plot_hr_zones(self):
        hr_stream = self._s[0].details_resp.get_heartrate_stream(
            # None values cause exceptions in self._plot_hr_zones_mixin().
            do_remove_none_values=True
        )
        self._plot_hr_zones_mixin(
            self._axes_mosaic["hr-zones"],
            hr_stream,
            settings.HR_MIN,
            settings.HR_MAX_EVER_RUN,
        )

    def _plot_hr_histogram(self):
        main_hr_stream = self._s[0].details_resp.get_heartrate_stream(
            # None values cause exceptions in self._plot_hr_histogram_mixin().
            do_remove_none_values=True
        )
        secondary_hr_streams = []
        for i in range(1, len(self._s)):
            details = self._s[i].details_resp
            summary = self._s[i].summary_resp
            # If the activity does not have a heart rate monitor, then I skip it.
            #  I chose this because data without HRM are unreliable and lower,
            #  so the effect on the chart is to visually reduce the differences.
            if not summary.has_heart_rate_monitor():
                continue
            secondary_hr_streams.append(
                details.get_heartrate_stream(do_remove_none_values=False)
            )

        self._plot_hr_histogram_mixin(
            self._axes_mosaic["hr-hist"],
            main_hr_stream,
            secondary_hr_streams=secondary_hr_streams,
            hr_max_ever=settings.HR_MAX_EVER_RUN,
            hr_zones_to_hatch=self.hr_zones_to_hatch,
            percentile_to_draw=self.percentile_to_draw,
        )

    def _print_splits(self):
        # Prepare the Splits table to be printed to the console.
        table = Table(
            title=":knife: Splits",  # Print all emoji with: `python -m rich.emoji`.
            title_style="bold black on yellow",
            row_styles=["dim", ""],
            box=box.SIMPLE,
        )
        table.add_column("km", justify="right", no_wrap=True)
        table.add_column("cum\nkm", justify="right", no_wrap=True)
        table.add_column("pace", justify="right", style="yellow", no_wrap=True)
        table.add_column("cum\npace", justify="right", style="yellow", no_wrap=True)
        table.add_column("cum\ntime", justify="right", no_wrap=True)
        table.add_column("elev", justify="right", no_wrap=True)
        table.add_column("avg\nHR", justify="right", no_wrap=True)
        table.add_column("max\nHR", justify="right", no_wrap=True)

        distance_cum = 0
        duration_cum = 0
        for split in self._s[0].splits_resp.splits:
            distance = split["distance"]
            distance_cum += distance
            distance_str = str(round(distance / 1000, 1))
            distance_cum_str = str(round(distance_cum / 1000, 1))

            duration = split["duration"]
            duration_cum += duration
            duration_cum_str = datetime_utils.seconds_to_hh_mm_ss(
                round(duration_cum), do_hide_hours_and_mins_if_zero=True
            )
            pace_cum_str = datetime_utils.seconds_to_hh_mm_ss(
                round(duration_cum / distance_cum * 1000),
                do_hide_hours_and_mins_if_zero=True,
            )
            pace_str = speed_utils.minpkm_base10_to_base60(
                speed_utils.mps_to_minpkm_base10(split["averageSpeed"])
            )
            elevation_str = str(round(split["elevationGain"] - split["elevationLoss"]))
            # Add rows to the Splits table to be printed to the console.
            table.add_row(
                distance_str,
                distance_cum_str,
                pace_str,
                pace_cum_str,
                duration_cum_str,
                elevation_str,
                str(round(split["averageHR"])),
                str(round(split["maxHR"])),
            )
        console.print(table)

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

        ## Collect summary and details for MAIN and SECONDARY activities.
        for activity_id in [self.garmin_activity_id] + [
            *self.prev_runs_activity_ids_to_compare
        ]:
            self._s.append(
                CollectedData(
                    summary_resp=self._api_get_activity_summary(activity_id),
                    details_resp=self._api_get_activity_details(
                        activity_id,
                        max_metrics_data_count=100 * 1000,
                    ),
                    splits_resp=None,  # Filled only for the main activity.
                )
            )
        # Fill in the splits only for the main activity.
        self._s[0].splits_resp = self._api_get_activity_splits(self.garmin_activity_id)

        self.print_activity_date(self._s[0].summary_resp.summary["startTimeLocal"])

        # Figure.
        figure, self._axes_mosaic = self._make_subplot_mosaic()
        figure: Figure
        self._axes_mosaic: dict[str, Axes]

        # All plots.
        self._plot_pace()
        self._print_splits()
        self._plot_hr_zones()
        self._plot_hr_histogram()

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
            activity_original_duration=self._s[0].summary_resp.summary["duration"],
            activity_original_distance=self._s[0].summary_resp.summary["distance"],
        )
        figure.text(
            figure.get_figwidth() / 2,  # Inches.
            figure.get_figheight() - 0.35,  # Inches.
            subtitle,
            fontsize=10,
            horizontalalignment="center",
            transform=figure.dpi_scale_trans,  # Use inches as figure size.
        )

        # Docs on legend location:
        #  https://matplotlib.org/stable/users/explain/axes/legend_guide.html
        # Alt 1/2: this is how to show a legend with only the plumb color of the main
        #  plot line in the pace chart.
        # figure.legend(
        #     loc="outside lower left",
        #     ncol=1,
        #     frameon=False,
        #     fontsize=9,
        #     labelspacing=0.8,
        # )
        # Alt 2/2: this is how to show a legend with both colors (plumb and red) of the
        #  main plot line in the pace chart and in the HR histogram chart.
        pace_axes = self._axes_mosaic["pace"]
        hr_hist_axes = self._axes_mosaic["hr-hist"]
        figure.legend(
            handles=[(hr_hist_axes.lines[0], pace_axes.lines[0])]
            + pace_axes.lines[1:-1],
            handler_map={tuple: HandlerTuple(ndivide=None)},
            labels=[x.get_label() for x in pace_axes.lines[:-1]],
            loc="outside lower left",
            ncol=1,
            frameon=False,
            fontsize=9,
            labelspacing=0.8,
        )

        # Customize legend to make it more visible: less alpha and larger line widths.
        for i in range(0, len(self._s)):
            figure.legends[0].legend_handles[0].set_linestyle("solid")
            figure.legends[0].legend_handles[i].set_alpha(0.8)
            figure.legends[0].legend_handles[i].set_linewidth(3.0)

        if save_to_png_file_path:
            self.print_created_image_path(save_to_png_file_path)
            plt.savefig(save_to_png_file_path)
        else:
            plt.show()

    def _make_figure_size(self) -> tuple[float, float]:
        height = max(len(self._s), 3.5) * 2.1
        return 5, height

    def _make_subplot_mosaic(self) -> tuple[Figure, dict[str, Axes]]:
        figsize = self.figure_size or self._make_figure_size()
        console.print(f":triangular_ruler: Figure size: {figsize}")

        # Docs for subplot_mosaic():
        #  https://matplotlib.org/stable/users/explain/axes/arranging_axes.html#variable-widths-or-heights-in-a-grid
        #  https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplot_mosaic.html#matplotlib.pyplot.subplot_mosaic
        return plt.subplot_mosaic(
            # fmt: off
    [
                # 2 rows, 1 col.
                ["pace", ],
                ["hr-zones", ],
                ["hr-hist", ],
            ],
            # fmt: on
            gridspec_kw=dict(
                # The relative sizes of the subplots.
                width_ratios=[1],
                height_ratios=[1.5, 0.22, 1],
            ),
            figsize=figsize,
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
