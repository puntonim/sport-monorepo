from dataclasses import dataclass
from pathlib import Path

import click
import datetime_utils
import log_utils as logger
import matplotlib as mpl
import matplotlib.pyplot as plt
from garmin_connect_client import ActivityDetailsResponse, ActivitySummaryResponse
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ...base_cli_view import BaseClickCommand
from ...conf import settings
from ...conf.settings_module import ROOT_DIR
from .. import base_api, base_plot


@click.command(
    cls=BaseClickCommand,
    name="plot-climb-ride",
    help='Plot a climb ride; eg: san plot-climb-ride 19792668968 --title "Re Stelvio Mapei" --segment-start-meters 0 --segment-end-meters 21110 --segment-title "Climb segment only" --figure-size 5.0 6.5 -d ~/workspace/sport-monorepo/projects/sport-analysis/output-images/',
)
@click.argument("garmin-activity-id", nargs=1, type=int)
@click.option("--title", type=str)
@click.option("--segment-start-meters", type=int)
@click.option("--segment-end-meters", type=int)
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
    garmin_activity_id: int,
    title: str | None = None,
    segment_start_meters: int | None = None,
    segment_end_meters: int | None = None,
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

    plot_ride = PlotClimbRideApi(
        garmin_activity_id,
        title=title,
        segment_start_meters=segment_start_meters,
        segment_end_meters=segment_end_meters,
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
        garmin_activity_id: int,
        title: str | None = None,
        segment_start_meters: int | None = None,
        segment_end_meters: int | None = None,
        segment_title: str = "Segment only",
        figure_size: tuple[float, float] | None = None,
        garmin_connect_token_manager: (
            FileGarminConnectTokenManager | FakeTestGarminConnectTokenManager | None
        ) = None,
    ):
        """
        Args:
            garmin_activity_id: id of Garmin activity to analyze.
            title: plot title.
            segment_title: title used for the segment chart,
            figure_size: customize the figure size, eg. (3.0, 5.5).
            garmin_connect_token_manager: use FakeTestGarminConnectTokenManager when
             replaying VCR episodes.
        """
        super().__init__(garmin_connect_token_manager)

        self.garmin_activity_id = garmin_activity_id
        self.title = title
        self.segment_start_meters = segment_start_meters
        self.segment_end_meters = segment_end_meters
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
        segment_title = f"{self.segment_title}\n{round(self.segment_start_meters/1000, 2) if self.segment_start_meters else ''}-{round(self.segment_end_meters/1000, 2) if self.segment_end_meters else ''} km"
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

    def plot(self, save_to_png_file_path: Path | None = None):
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

        # Figure.
        figure, self._axes_mosaic = self._make_subplot_mosaic()
        figure: Figure
        self._axes_mosaic: dict[str, Axes]

        # All plots.
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
