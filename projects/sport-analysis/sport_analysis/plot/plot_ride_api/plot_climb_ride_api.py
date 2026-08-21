from dataclasses import dataclass
from pathlib import Path

import click
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
from strava_client import StravaClient, StreamsResponse
from strava_client.strava_token_managers import (
    AwsParameterStoreStravaTokenManager,
    FakeTestStravaTokenManager,
    FileStravaTokenManager,
)

from ...base_cli_view import ACTIVITY_ID_TYPE, BaseClickCommand
from ...conf import settings
from ...conf.settings_module import ROOT_DIR
from ...search.search_matching_activity_api import (
    search_strava_activity_matching_garmin_activity_api,
)
from .. import base_api, base_plot


@click.command(
    cls=BaseClickCommand,
    name="plot-climb-ride",
    help="""
    Plot a climb ride.
    
    \b
    Examples
    $ san plot-climb-ride 19792668968 --title "Re Stelvio Mapei" --segment-start-meters 0 --segment-end-meters 21110 --segment-title "Climb segment only" --figure-size 5.0 6.5 -d ~/workspace/sport-monorepo/projects/sport-analysis/output-images/
    """,
)
@click.argument(
    # id (int) of Garmin activity to analyze or "LATEST" or "LATEST-3".
    "garmin-activity-id",
    nargs=1,
    type=ACTIVITY_ID_TYPE,
    # help="Garmin activity id or LATEST or LATEST-3",
)
@click.option("--title", type=str)
@click.option(
    "--segment-start-meters",
    type=int,
    help="The start of the desired segment, in meters",
)
@click.option(
    "--segment-end-meters", type=int, help="The end of the desired segment, in meters"
)
@click.option(
    "--segment-strava-name",
    type=str,
    help="Name of the Strava segment - it cannot be used together with segment_start|end_meters",
)
@click.option("--segment-title", default="Segment only", type=str)
@click.option(
    "--figure-size",
    nargs=2,
    type=click.Tuple([float, float]),
    help="eg. 5.0 7.0; a tuple of floats",
)
@click.option(
    "--dir",
    "-d",
    "dir_or_file_path",
    type=click.Path(
        # exists=True,
        file_okay=True,
        dir_okay=True,
        readable=True,
        writable=True,
        resolve_path=True,
        path_type=Path,
    ),
    default=ROOT_DIR / "output-images",
    help="Either dir or file path where to store the .png plot",
)
def plot_climb_ride_api_cli_view(
    # id (int) of Garmin activity to analyze or ("LATEST", 0) or ("LATEST", -3).
    garmin_activity_id: int | tuple[str, int],
    title: str | None = None,
    segment_start_meters: int | None = None,
    segment_end_meters: int | None = None,
    segment_strava_name: str | None = None,
    segment_title: str = "Segment only",
    figure_size: tuple[float, float] | None = None,
    dir_or_file_path: Path = ROOT_DIR / "output-images",
) -> None:
    """
    Plot the HR histogram for the given Garmin activity id as a bike ride.
    """
    if dir_or_file_path.suffix:
        if dir_or_file_path.suffix == ".png":  # It's a .png file.
            if dir_or_file_path.exists():
                raise click.BadParameter("The given .png file already exists")
        else:
            raise click.BadParameter("Not a .png file path")
        save_to_png_file_path: Path = dir_or_file_path
    else:  # It's a dir.
        if not dir_or_file_path.exists():
            raise click.BadParameter("The given dir does not exists")
        ts = datetime_utils.now().isoformat()  # Eg. "2025-05-13T21:01:33.752427+02:00".
        save_to_png_file_path: Path = dir_or_file_path / f"{ts}.png"

    # Check that
    #   segment_start|end_meters and segment_strava_name
    #  are NOT given together.
    if segment_strava_name and (segment_start_meters or segment_end_meters):
        raise click.BadParameter(
            "Either segment-strava-name or (segment-start-meters and segment-end-meters)"
        )

    plot_ride = PlotClimbRideApi(
        garmin_activity_id,
        title=title,
        segment_start_meters=segment_start_meters,
        segment_end_meters=segment_end_meters,
        segment_strava_name=segment_strava_name,
        segment_title=segment_title,
        figure_size=figure_size,
    )
    return plot_ride.plot(save_to_png_file_path=save_to_png_file_path)


@dataclass
class CollectedData:
    summary_resp: ActivitySummaryResponse = None
    details_resp: ActivityDetailsResponse = None


class PlotClimbRideApi(base_api.MixinGarminRequestsApi, base_plot.MixinHrPlot):
    def __init__(
        self,
        # id (int) of Garmin activity to analyze or ("LATEST", 0) or ("LATEST", -3).
        garmin_activity_id: int | tuple[str, int],
        title: str | None = None,
        segment_start_meters: int | None = None,
        segment_end_meters: int | None = None,
        segment_strava_name: str | None = None,
        segment_title: str = "Segment only",
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
            title: plot title.
            segment_start_meters: the start of the desired segment, in meters.
            segment_end_meters: the end of the desired segment, in meters.
            segment_strava_name: name of the Strava segment. It cannot be used
             together with segment_start|end_meters.
            segment_title: title used for the segment chart,
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
        self.title = title
        self.segment_start_meters = segment_start_meters
        self.segment_end_meters = segment_end_meters
        self.segment_strava_name = segment_strava_name
        self.segment_title = segment_title
        self.figure_size = figure_size

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
            do_remove_none_values=False,
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
        segment_title = f"{self.segment_title}\n{round(self.segment_start_meters/1000, 2) if self.segment_start_meters else '0'}-{round(self.segment_end_meters/1000, 2) if self.segment_end_meters else ''} km"
        self._plot_hr_histogram_mixin(
            self._axes_mosaic["hr-hist"],
            hr_stream,
            hr_max_ever=settings.HR_MAX_EVER_RIDE,
            elevation_stream=elevation_stream,
            time_stream=time_stream,
            segment_title=segment_title,
        )

    def _plot_hr_zones(self):
        hr_stream = self._s[0].details_resp.get_heartrate_stream(
            do_remove_none_values=False,
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

        strava_summary = search_strava_activity_matching_garmin_activity_api(
            self.garmin_activity_id,
            strava_token_manager=self.strava_token_manager,
            garmin_connect_token_manager=self.garmin_connect_token_manager,
        )
        strava_activity_id = strava_summary["id"]
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
            # TODO better exc
            raise Exception(
                "The matching Strava activity has a dataset with different size (and I am searching for the Strava segment name provided)"
            )

        # Get the segment effort in Strava.
        # TODO cambia codice di strava client per prendere un segment effort by name only
        segment_efforts = strava_details.get_segment_efforts(
            [(14418673, "Selvino Fontanella")]
        )
        # TODO replace assertion with exception
        assert len(segment_efforts) == 1
        segment_start_index = segment_efforts[0]["start_index"]
        segment_end_index = segment_efforts[0]["end_index"]
        print(f"Strava segment indices: {segment_start_index}-{segment_end_index}")
        segment_start_distance = strava_streams.get_distance_stream()[
            segment_start_index
        ]
        segment_end_distance = strava_streams.get_distance_stream()[segment_end_index]
        print(
            f"Strava segment distances: {segment_start_distance}-{segment_end_distance}"
        )
        self.segment_start_meters = segment_start_distance
        self.segment_end_meters = segment_end_distance

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

        title = (
            self.title
            if self.title is not None
            else self._s[0].summary_resp.data["activityName"]
        )
        figure.suptitle(title)

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
            figsize=self._make_figure_size(),
            layout="constrained",
        )
