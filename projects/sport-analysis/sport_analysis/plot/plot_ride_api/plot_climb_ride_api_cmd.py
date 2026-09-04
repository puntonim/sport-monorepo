from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import datetime_utils
import matplotlib as mpl
import matplotlib.pyplot as plt
from garmin_connect_client import ActivityDetailsResponse, ActivitySummaryResponse
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from strava_client import SegmentEffortNotFound, StravaClient, StreamsResponse
from strava_client.strava_token_managers import (
    AwsParameterStoreStravaTokenManager,
    FakeTestStravaTokenManager,
    FileStravaTokenManager,
)

from ...base_cli_view import ConsoleAdapter
from ...conf import settings
from ...get.get_activity_urls.get_activity_urls_api_cmd import (
    search_strava_activity_matching_garmin_activity,
)
from .. import base_api, base_plot
from ..base_plot import PERCENTILE_TO_DRAW_ENUM, _make_subtitle, _make_title

console = ConsoleAdapter()


@dataclass
class CollectedData:
    summary_resp: ActivitySummaryResponse = None
    details_resp: ActivityDetailsResponse = None


class PlotClimbRideApiCmd(base_api.MixinGarminRequestsApi, base_plot.MixinHrPlot):
    def __init__(
        self,
        # id (int) of Garmin activity to analyze or ("LATEST", 0) or ("LATEST", -3).
        garmin_activity_id: int | tuple[str, int],
        percentile_to_draw: PERCENTILE_TO_DRAW_ENUM | str | None = None,
        # List of HR zones that are "disabled" by hatching (drawing 45deg grey lines).
        hr_zones_to_hatch: Sequence[str] | None = None,
        segment_start_meters: int | None = None,
        segment_end_meters: int | None = None,
        segment_title: str | None = None,
        segment_strava_name: str | None = None,
        title: str | None = None,
        figure_size: tuple[float, float] | None = None,
        garmin_connect_token_manager: (
            FileGarminConnectTokenManager | FakeTestGarminConnectTokenManager | None
        ) = None,
        strava_token_manager: (
            AwsParameterStoreStravaTokenManager
            | FileStravaTokenManager
            | FakeTestStravaTokenManager
            | None
        ) = None,
    ):
        """
        Args:
            garmin_activity_id: id (int) of Garmin activity to analyze or ("LATEST", 0)
             or ("LATEST", -3).
            percentile_to_draw: either P80 or P98 to draw as vertical line on the
             histogram. Note that both percentiles are always written as text under the
             histogram.
            hr_zones_to_hatch: list of HR zones that are "disabled" by hatching
             (drawing 45deg grey lines). Eg. ["Z3", "Z4", "Z5"].
            segment_start_meters: the start of the desired segment, in meters.
            segment_end_meters: the end of the desired segment, in meters.
            segment_title: title used for the segment chart.
            segment_strava_name: name of the Strava segment. It cannot be used
             together with segment_start|end_meters.
            title: plot title.
            figure_size: customize the figure size, eg. (3.0, 5.5).
            garmin_connect_token_manager: use FakeTestGarminConnectTokenManager when
             replaying VCR episodes.
            strava_token_manager: use FakeTestStravaTokenManager when
             replaying VCR episodes.
        """
        super().__init__(garmin_connect_token_manager)

        self.garmin_connect_token_manager = garmin_connect_token_manager
        self.strava_token_manager = strava_token_manager
        self.garmin_activity_id = garmin_activity_id
        self.percentile_to_draw = percentile_to_draw
        self.title = title
        self.segment_start_meters = segment_start_meters
        self.segment_end_meters = segment_end_meters
        self.segment_title = segment_title
        self.segment_strava_name = segment_strava_name
        self.figure_size = figure_size

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

    def _plot_hr_and_elevation(self):
        a0: Axes = self._axes_mosaic["hr"]

        ## Collect data.
        # X data.
        xdata_time = self._s[0].details_resp.get_elapsed_time_stream()

        # Y data.
        ydata_hr = self._s[0].details_resp.get_heartrate_stream(
            do_remove_none_values=False
        )
        ydata_elevation = self._s[0].details_resp.get_altitude_stream()

        ## Plot data.
        # Plot HR.
        a0.plot(
            xdata_time,
            ydata_hr,
            # label="HR",
            color="red",
            alpha=0.6,
            linewidth=1.5,
        )
        a0.set_ylabel("Heart rate [bpm]")

        # Plot Elevation.
        # Create a new axes that shares the x-axis.
        a1 = a0.twinx()
        a1.plot(
            xdata_time,
            ydata_elevation,
            color="gray",
            alpha=0.2,
            linewidth=0,
            linestyle="-",
            # marker=".",
            # label="Elevation",
        )
        a1.fill_between(
            x=xdata_time,
            y1=ydata_elevation,
            color="gray",
            alpha=0.1,
        )
        a1.set_ylabel("Elevation [m]")

        ## Format axes.
        # Ticks and labels.
        a0.xaxis.set_major_formatter(
            mpl.ticker.FuncFormatter(
                # Set ticks label as hh:mm.
                lambda x, pos: datetime_utils.seconds_to_hh_mm(
                    x, do_hide_hours_and_mins_if_zero=True
                )
            )
        )

        ## Format.
        # Axes labels.
        a0.set_xlabel("Time [hh:mm]")

    def _plot_hr_histogram(self):
        hr_stream = self._s[0].details_resp.get_heartrate_stream(
            do_remove_none_values=True,
            segment_start_meters=self.segment_start_meters,
            segment_end_meters=self.segment_end_meters,
        )
        time_stream = self._s[0].details_resp.get_elapsed_time_stream(
            segment_start_meters=self.segment_start_meters,
            segment_end_meters=self.segment_end_meters,
        )
        elevation_stream = self._s[0].details_resp.get_altitude_stream(
            segment_start_meters=self.segment_start_meters,
            segment_end_meters=self.segment_end_meters,
        )

        segment_title = None
        distance = self._s[0].summary_resp.data["summaryDTO"]["distance"]
        if self.segment_title:
            segment_title = f"Segment {self.segment_title} ({round(self.segment_start_meters/1000, 1) if self.segment_start_meters else '0'}-{round(self.segment_end_meters/1000, 1) if self.segment_end_meters else round(distance/1000, 1)} km)"
        elif self.segment_strava_name:
            segment_title = self.segment_strava_name
        elif self.segment_start_meters or self.segment_end_meters:
            segment_title = f"Segment {round(self.segment_start_meters/1000, 1) if self.segment_start_meters else '0'}-{round(self.segment_end_meters/1000, 1) if self.segment_end_meters else round(distance/1000, 1)} km"
        self._plot_hr_histogram_mixin(
            self._axes_mosaic["hr-hist"],
            hr_stream,
            hr_max_ever=settings.HR_MAX_EVER_RIDE,
            elevation_stream=elevation_stream,
            time_stream=time_stream,
            segment_title=segment_title,
            percentile_to_draw=self.percentile_to_draw,
            hr_zones_to_hatch=self.hr_zones_to_hatch,
        )

    def _plot_hr_zones(self):
        hr_stream = self._s[0].details_resp.get_heartrate_stream(
            do_remove_none_values=True,
            segment_start_meters=self.segment_start_meters,
            segment_end_meters=self.segment_end_meters,
        )
        self._plot_hr_zones_mixin(
            self._axes_mosaic["hr-zones"],
            hr_stream,
            settings.HR_MIN,
            settings.HR_MAX_EVER_RIDE,
        )

    def _get_strava_segment_info(self):
        strava_token_manager = (
            self.strava_token_manager
            or AwsParameterStoreStravaTokenManager(
                settings.TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
                settings.CLIENT_ID_PARAMETER_STORE_KEY_PATH,
                settings.CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            )
        )
        strava = StravaClient(strava_token_manager.get_access_token())

        matching_activities = search_strava_activity_matching_garmin_activity(
            self.garmin_activity_id,
            strava_token_manager=self.strava_token_manager,
            garmin_connect_token_manager=self.garmin_connect_token_manager,
        )
        strava_activity_id = matching_activities.strava_activity_dict["id"]
        strava_details = strava.get_activity_details(strava_activity_id)
        stream_types = ["time", "distance"]
        strava_streams: StreamsResponse = strava.get_streams(
            strava_activity_id, stream_types=stream_types
        )

        # Ensure that the Garmin and Strava matching activities have the same dataset
        #  size.
        garmin_dataset_size = self._s[0].details_resp.original_dataset_size
        strava_dataset_size = strava_streams.get_original_dataset_size()
        if garmin_dataset_size != strava_dataset_size:
            raise DatasetSizeError(
                "The matching Strava activity has a dataset with different size than"
                " the Garmin activity (and I am searching for the Strava segment effort"
                f" with the name provided): {strava_dataset_size} in Strava vs"
                f" {garmin_dataset_size} in Garmin"
            )

        # Get the segment effort in Strava.
        try:
            segment_efforts = strava_details.get_segment_efforts(
                [self.segment_strava_name]
            )
        except SegmentEffortNotFound as exc:
            raise StravaSegmentEffortNotFound(self.segment_strava_name) from exc

        if len(segment_efforts) != 1:
            raise MultipleStravaSegmentEfforts(
                f"Expected 1 Strava segment effort, but found: {len(segment_efforts)}"
            )

        segment_start_index = segment_efforts[0]["start_index"]
        segment_end_index = segment_efforts[0]["end_index"]
        segment_start_distance = strava_streams.get_distance_stream()[
            segment_start_index
        ]
        segment_end_distance = strava_streams.get_distance_stream()[segment_end_index]
        self.segment_start_meters = segment_start_distance
        self.segment_end_meters = segment_end_distance
        console.print(
            f"Segment: {self.segment_start_meters}m-{self.segment_end_meters}m "
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
                activity_type="cycling",
                n_results=abs(original_garmin_activity_id_arg[1]) + 1,
            )[-1]
        self.print_activity_urls(
            original_activity_id_arg=original_garmin_activity_id_arg,
            garmin_activity_id=self.garmin_activity_id,
            activity_txt_to_print="ride",
        )

        ## Collect summary and details.
        self._s.append(
            CollectedData(
                summary_resp=self._api_get_activity_summary(self.garmin_activity_id),
                details_resp=self._api_get_activity_details(
                    self.garmin_activity_id,
                    max_metrics_data_count=100 * 1000,
                ),
            )
        )

        self.print_activity_date(self._s[0].summary_resp.summary["startTimeLocal"])

        # Figure.
        figure, self._axes_mosaic = self._make_subplot_mosaic()
        figure: Figure
        self._axes_mosaic: dict[str, Axes]

        # All plots.
        if self.segment_strava_name:
            self._get_strava_segment_info()
        self._plot_hr_and_elevation()
        self._plot_hr_histogram()
        self._plot_hr_zones()

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
        figure.legend(
            loc="outside lower left",
            ncol=1,
            frameon=False,
            fontsize=9,
            labelspacing=0.8,
        )

        if save_to_png_file_path:
            self.print_created_image_path(save_to_png_file_path)
            plt.savefig(save_to_png_file_path)
        else:
            plt.show()

    def _make_figure_size(self) -> tuple[float, float]:
        height = max(len(self._s), 3.5) * 2
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
                ["hr", ],
                ["hr-hist", ],
                ["hr-zones", ]
            ],
            # fmt: on
            gridspec_kw=dict(
                # The relative sizes of the subplots.
                width_ratios=[1],
                height_ratios=[1.5, 1, 1 / 5],
            ),
            figsize=figsize,
            layout="constrained",
        )


class BasePlotClimbRideApiCmdException(Exception): ...


class StravaSegmentEffortNotFound(BasePlotClimbRideApiCmdException):
    def __init__(self, strava_segment_name: str):
        self.strava_segment_name = strava_segment_name


class DatasetSizeError(BasePlotClimbRideApiCmdException): ...


class MultipleStravaSegmentEfforts(BasePlotClimbRideApiCmdException): ...
