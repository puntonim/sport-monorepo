from pathlib import Path

import click
import datetime_utils

from ...base_cli_view import ACTIVITY_ID_TYPE, BaseClickCommand
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
     This command asks for inputs:
       $ san plot-interval-run 18923007987
     This command does NOT ask for inputs:
       $ san plot-interval-run 20579416584 --distance 200 --vs-n 3 --text DEFAULT --n-expected-intervals 10 --title DEFAULT --dir DEFAULT
     All possible args:
       $ san plot-interval-run 18923007987 --distance 200 --vs-n 3 --text "10x200m" --n-expected-intervals 6 --title "10x200m a Verdellino" --figure-size 5.0 8.2 --dir ~/workspace/sport-monorepo/projects/sport-analysis/output-images/
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
    "--distance",
    "-dist",
    "distance",
    type=click.Choice((x.value for x in DistanceEnum), case_sensitive=False),
    prompt="Distance in meters?",
    help="Distance: 100, 200, 300 or 1000",
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
    "--activity-id-to-compare",
    "-vs",
    # Note: "ids" is plural as this option can be repeated multiple times.
    "activity_ids_to_compare",
    type=int,
    multiple=True,
    help="Garmin activity id to compare; it can be used multiple times",
)
@click.option(
    "--vs-n",
    "n_prev_activities_to_auto_compare",
    type=int,
    prompt="Num of previous activities to AUTO compare?",
    default=0,
    help="Number of previous activities to AUTO compare to the given activity; they are searched automatically",
    required=True,
)
@click.option(
    "--text",
    "txt_to_search_for_prev_activities_to_auto_compare",
    type=str,
    prompt="Text used in the search for prev activities to AUTO compare?",
    default=__DEFAULT_INPUT_TXT_SEARCH_PREV_ACTIVITY,
    help="Text used in the search for previous activities to AUTO compare; it's an exact match on activities' titles; use DEFAULT for a smart serach like: 1x200m ... 10x200m",
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
    # id (int) of Garmin activity to analyze or ("LATEST", 0) or ("LATEST", -3).
    garmin_activity_id: int | tuple[str, int],
    distance: DistanceEnum,
    activity_ids_to_compare: tuple[int] | None = None,
    n_expected_intervals: int = 10,
    n_prev_activities_to_auto_compare: int = 10,
    txt_to_search_for_prev_activities_to_auto_compare: str | None = None,
    title: str | None = None,
    figure_size: tuple[float, float] | None = None,
    dir_or_file_path: Path = ROOT_DIR / "output-images",
) -> None:
    """
    Plot the given Garmin activity id as an interval run.
    """
    # Parse activity_ids_to_compare, n_prev_activities_to_auto_compare,
    #  txt_to_search_for_prev_activities_to_auto_compare.
    if activity_ids_to_compare and n_prev_activities_to_auto_compare > 0:
        raise click.BadParameter(
            "--activity-id-to-compare (-vs) and --vs-n args cannot be used together"
        )

    # Set the hack-ish defaults to None.
    if txt_to_search_for_prev_activities_to_auto_compare in (
        __DEFAULT_INPUT_TXT_SEARCH_PREV_ACTIVITY,
        "DEFAULT",
    ):
        txt_to_search_for_prev_activities_to_auto_compare = None
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
        n_expected_intervals=[n_expected_intervals],
        activity_ids_to_compare=[x for x in activity_ids_to_compare],  # Tuple to list.
        n_prev_activities_to_auto_compare=n_prev_activities_to_auto_compare,
        txt_to_search_for_prev_activities_to_auto_compare=txt_to_search_for_prev_activities_to_auto_compare,
        title=title,
        figure_size=figure_size,
    )
    return plot_interval.plot(save_to_png_file_path=save_to_png_file_path)
