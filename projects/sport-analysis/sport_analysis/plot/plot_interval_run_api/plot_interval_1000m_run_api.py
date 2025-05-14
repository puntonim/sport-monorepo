from pathlib import Path

import click
import datetime_utils
from garmin_connect_client import ActivityTypedSplitsResponse

from ...base_cli_view import BaseClickCommand
from ...conf.settings_module import ROOT_DIR
from .base_plot_interval_run_api import BasePlotIntervalRunApi


@click.command(
    cls=BaseClickCommand,
    name="plot-interval-1000m-run",
    help='Plot an interval 1000m run; eg: analysis plot-interval-1000m-run 19042748874 --vs-n 3 --text "4x1000m" --title "4x1000m a Verdellino" --figure-size 5.0 8.2 -d ~/workspace/sport-monorepo/projects/sport-analysis/output-images/',
)
@click.argument("garmin-activity-id", nargs=1, type=int)
@click.option(
    "--vs-n",
    "n_previous_activities_to_compare",
    type=int,
    default=10,
    help="Number of previous activities to compare to the given activity; they are searched automatically",
)
@click.option(
    "--text",
    "text_to_search_for_previous_activities",
    type=str,
    help="Text used in the search for previous activities to compare; it's an exact match on activities' titles.",
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
def plot_interval_1000m_run_api_cli_view(
    garmin_activity_id: int,
    n_previous_activities_to_compare: int = 10,
    text_to_search_for_previous_activities: str | None = None,
    title: str | None = None,
    figure_size: tuple[float, float] | None = None,
    dir_or_file_path: Path = ROOT_DIR / "output-images",
) -> None:
    """
    Plot the given Garmin activity id as a 1000m interval run.
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

    plot_int_1000m = PlotInterval1000mRunApi(
        garmin_activity_id,
        n_previous_activities_to_compare=n_previous_activities_to_compare,
        text_to_search_for_previous_activities=text_to_search_for_previous_activities,
        title=title,
        figure_size=figure_size,
    )
    return plot_int_1000m.plot(save_to_png_file_path=save_to_png_file_path)


class PlotInterval1000mRunApi(BasePlotIntervalRunApi):
    """
    Plot charts to support the analysis of a 4x1000m run activity performance,
     optionally compared with previous activities.
    """

    # Mind that it's an exact match on activities' titles.
    DEFAULT_TEXT_TO_SEARCH_FOR_PREVIOUS_ACTIVITIES = "4x1000m"

    def _get_splits_for_activity_typed_splits_response(
        self, response: ActivityTypedSplitsResponse
    ):
        splits = list()
        for split in response.get_interval_active_splits():
            if abs(split["distance"] - 1000) < 10:
                splits.append(split)
        if not len(splits) == 4:
            raise BasePlotInterval1000mRunApiException(
                f"Expected 4 splits, found {len(splits)}"
            )

        return splits

    def _fmt_time(self, seconds: float):
        return datetime_utils.seconds_to_hh_mm_ss(round(seconds))[3:]


class BasePlotInterval1000mRunApiException(Exception):
    pass
