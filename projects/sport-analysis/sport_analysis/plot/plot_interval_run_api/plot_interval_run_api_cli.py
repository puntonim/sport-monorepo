from pathlib import Path

import click
import datetime_utils

from ...base_cli_view import BaseClickCommand
from ...conf.settings_module import ROOT_DIR
from .plot_interval_run_api_cmd import DistanceEnum, PlotIntervalRunApiCmd

# Hack-ish default values.
__DEFAULT_INPUT_TXT_SEARCH_PREV_ACTIVITY = (
    "blank for smart search like: 1x200m ... 10x200m"
)
__DEFAULT_INPUT_TITLE = "blank to use Garmin title"


@click.command(
    cls=BaseClickCommand,
    name="plot-interval-run",
    help="""Plot an interval run.
     
     \b
     Examples
     This will ask for inputs:
        $ san plot-interval-run 18923007987
     This will not ask for inputs:
        $ san plot-interval-run 20579416584 --distance 200 --vs-n 3 --text DEFAULT --n-expected-intervals 10 --title DEFAULT --dir DEFAULT
     This uses all possible args:
        $ san plot-interval-run 18923007987 --distance 200 --vs-n 3 --text "10x200m" --n-expected-intervals 6 --title "10x200m a Verdellino" --figure-size 5.0 8.2 --dir ~/workspace/sport-monorepo/projects/sport-analysis/output-images/
     """,
)
@click.argument("garmin-activity-id", nargs=1, type=int, required=True)
@click.option(
    "--distance",
    "-dist",
    "distance",
    type=click.Choice((x.value for x in DistanceEnum), case_sensitive=False),
    prompt="Distance in meters?",
    help="Distance: 200, 300 or 1000",
    required=True,
)
@click.option(
    "--vs-n",
    "n_previous_activities_to_compare",
    type=int,
    prompt="Num of previous activities to compare?",
    default=10,
    help="Number of previous activities to compare to the given activity; they are searched automatically",
    required=True,
)
@click.option(
    "--text",
    "text_to_search_for_previous_activities",
    type=str,
    prompt="Text used in the search for prev activities to compare?",
    default=__DEFAULT_INPUT_TXT_SEARCH_PREV_ACTIVITY,
    help="Text used in the search for previous activities to compare; it's an exact match on activities' titles; use DEFAULT for a smart serach like: 1x200m ... 10x200m",
    required=True,
)
@click.option(
    "--n-expected-intervals",
    "-n-int",
    "n_expected_intervals",
    type=int,
    prompt="Num of expected intervals in the run?",
    default=10,
    help="Number of expected intervals in the given activity; mind that some intervals in the given activity might have been skipped by accident (and thus they are shorted than 200m and automatically discarded).",
    required=True,
)
@click.option(
    "--title",
    "title",
    type=str,
    prompt="Title?",
    default=__DEFAULT_INPUT_TITLE,
    help="Chart title; use DEFAULT to use Garmin activity's title",
    required=True,
)
# It's too difficult to ask for a prompt for this Tuple value.
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
        exists=False,
        file_okay=True,
        dir_okay=True,
        readable=True,
        writable=True,
        resolve_path=True,
        path_type=Path,
    ),
    prompt="Dir or file path?",
    default=ROOT_DIR / "output-images",
    help=f"Either dir or file path where to store the .png plot; use DEFAULT for {(ROOT_DIR / 'output-images').resolve()} ",
    required=True,
)
def plot_interval_run_api_cli_view(
    garmin_activity_id: int,
    distance: DistanceEnum,
    n_previous_activities_to_compare: int = 10,
    text_to_search_for_previous_activities: str | None = None,
    n_expected_intervals: int = 10,
    title: str | None = None,
    figure_size: tuple[float, float] | None = None,
    dir_or_file_path: Path = ROOT_DIR / "output-images",
) -> None:
    """
    Plot the given Garmin activity id as an interval run.
    """
    # Set the hack-ish defaults to None.
    if text_to_search_for_previous_activities in (
        __DEFAULT_INPUT_TXT_SEARCH_PREV_ACTIVITY,
        "DEFAULT",
    ):
        text_to_search_for_previous_activities = None
    if title in (__DEFAULT_INPUT_TITLE, "DEFAULT"):
        title = None

    # Parse dir_or_file_path.
    if dir_or_file_path.resolve() == Path("DEFAULT").resolve():
        dir_or_file_path = ROOT_DIR / "output-images"
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

    plot_interval = PlotIntervalRunApiCmd(
        garmin_activity_id,
        distance=distance,
        n_previous_activities_to_compare=n_previous_activities_to_compare,
        text_to_search_for_previous_activities=text_to_search_for_previous_activities,
        n_expected_intervals=[n_expected_intervals],
        title=title,
        figure_size=figure_size,
    )
    return plot_interval.plot(save_to_png_file_path=save_to_png_file_path)
