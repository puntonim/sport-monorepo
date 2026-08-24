from dataclasses import dataclass
from pathlib import Path

import click
import datetime_utils
import matplotlib.pyplot as plt
from garmin_connect_client import ActivityDetailsResponse, ActivitySummaryResponse
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ...base_cli_view import ACTIVITY_ID_TYPE, BaseClickCommand
from ...conf import settings
from ...conf.settings_module import ROOT_DIR
from .. import base_api, base_plot
from ..base_plot import PERCENTILE_TO_DRAW_ENUM


@click.command(
    cls=BaseClickCommand,
    name="plot-simple-ride",
    help="""
    Plot a simple bike ride.
    
    \b
    Examples
    $ san plot-simple-ride 19795436851 --title "Verdellino - Adda 20km" --figure-size 5.0 6.5 -d ~/workspace/sport-monorepo/projects/sport-analysis/output-images/
    """,
)
@click.argument(
    # id (int) of Garmin activity to analyze or "LATEST" or "LATEST-3".
    "garmin-activity-id",
    nargs=1,
    type=ACTIVITY_ID_TYPE,
    # help="Garmin activity id or LATEST or LATEST-3",
)
@click.option(
    "--percentile-to-draw",
    type=click.Choice(tuple(x for x in PERCENTILE_TO_DRAW_ENUM), case_sensitive=False),
    help="Optional percentile to draw in histogram; P80 is great for a 80/20 ride, P98 for a slow ride; eg. P80 | P98",
)
@click.option("--title", type=str)
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
def plot_simple_ride_api_cli_view(
    # id (int) of Garmin activity to analyze or ("LATEST", 0) or ("LATEST", -3).
    garmin_activity_id: int | tuple[str, int],
    percentile_to_draw: PERCENTILE_TO_DRAW_ENUM | None = None,
    title: str | None = None,
    figure_size: tuple[float, float] | None = None,
    dir_or_file_path: Path = ROOT_DIR / "output-images",
) -> None:
    """
    Plot the HR histogram alone for the given Garmin activity id as a bike ride.
    """
    if dir_or_file_path.suffix:  # It's a file.
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

    plot_ride = PlotSimpleRideApi(
        garmin_activity_id,
        percentile_to_draw=percentile_to_draw,
        title=title,
        figure_size=figure_size,
    )
    return plot_ride.plot(save_to_png_file_path=save_to_png_file_path)


@dataclass
class CollectedData:
    summary_resp: ActivitySummaryResponse = None
    details_resp: ActivityDetailsResponse = None


class PlotSimpleRideApi(base_api.MixinGarminRequestsApi, base_plot.MixinHrPlot):
    def __init__(
        self,
        # id (int) of Garmin activity to analyze or ("LATEST", 0) or ("LATEST", -3).
        garmin_activity_id: int | tuple[str, int],
        percentile_to_draw: PERCENTILE_TO_DRAW_ENUM | str | None = None,
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
            percentile_to_draw: either P80 or P98 to draw as vertical line on the
             histogram. Note that both percentiles are always written as text under the
             histogram.
            title: plot title.
            figure_size: customize the figure size, eg. (3.0, 5.5).
            garmin_connect_token_manager: use FakeTestGarminConnectTokenManager when
             replaying VCR episodes.
        """
        super().__init__(garmin_connect_token_manager)

        self.garmin_activity_id = garmin_activity_id
        self.percentile_to_draw = percentile_to_draw
        self.title = title
        self.figure_size = figure_size

        # It's the store for responses collected for all activities.
        self._s: list[CollectedData] = []

        # Matplotlib axes mosaic. This figure is made of 3 charts in 2 rows and 1 col.
        #  These _axes_mosaic represent these 2 rows and 1 col.
        #  Each item in the _axes_mosaic dict is an Axes instance: the x-axis and y-axis
        #  of an actual chart.
        self._axes_mosaic: dict[str, Axes]

    def _plot_hr_histogram(self):
        hr_stream = self._s[0].details_resp.get_heartrate_stream(
            do_remove_none_values=False
        )
        self._plot_hr_histogram_mixin(
            self._axes_mosaic["hr-hist"],
            hr_stream,
            hr_max_ever=settings.HR_MAX_EVER_RIDE,
            percentile_to_draw=self.percentile_to_draw,
        )

    def _plot_hr_zones(self):
        hr_stream = self._s[0].details_resp.get_heartrate_stream(
            do_remove_none_values=False
        )
        self._plot_hr_zones_mixin(
            self._axes_mosaic["hr-zones"],
            hr_stream,
            settings.HR_MIN,
            settings.HR_MAX_EVER_RIDE,
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
        height = max(len(self._s), 3.5) * 1.1
        return 5, height

    def _make_subplot_mosaic(self) -> tuple[Figure, dict[str, Axes]]:
        # Docs for subplot_mosaic():
        #  https://matplotlib.org/stable/users/explain/axes/arranging_axes.html#variable-widths-or-heights-in-a-grid
        #  https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplot_mosaic.html#matplotlib.pyplot.subplot_mosaic
        return plt.subplot_mosaic(
            # fmt: off
            [
                # 1 rows, 1 col.
                ["hr-hist", ],
                ["hr-zones", ]
            ],
            # fmt: on
            gridspec_kw=dict(
                # The relative sizes of the subplots.
                width_ratios=[1],
                height_ratios=[5, 1],
            ),
            figsize=self._make_figure_size(),
            layout="constrained",
        )
