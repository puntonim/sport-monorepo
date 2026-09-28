"""
During a run class (garmin id 24473738940) I run 8x1000m intervals and I managed to set
 the Garmin watch to track the 8 intervals on button press and for 1000m, 8 times, with
 rest until button press.
The first interval (starting at 0 seconds) was a fast one.
The last interval was indeed a rest with a few lasp of slow run.

Note: this script uses VCR.py to record HTTP interactions. Just because I wanted to
 test how to use VCR.py in a live code.

Usage:
    $ poetry run python -m sport_analysis.sketches.plot_interval_run.plot_dist_interval_run.plot_dist_interval_run_api_cli 24473738940
    To record new VCR.py episodes:
    $ IS_VCR_EPISODE_OR_ERROR=n poetry run python -m sport_analysis.sketches.plot_interval_run.plot_dist_interval_run.plot_dist_interval_run_api_cli 24473738940
"""

from contextlib import suppress
from pathlib import Path

import click
import questionary
import vcr as vcr_module
from vcr.errors import CannotOverwriteExistingCassetteException

from sport_analysis.base_cli_view import (
    ACTIVITY_ID_TYPE,
    QUESTIONARY_STYLE,
    BaseClickCommand,
    ConsoleAdapter,
)
from sport_analysis.conf.settings_module import ROOT_DIR
from sport_analysis.plot import base_plot
from sport_analysis.utils import questionary_parsers
from tests import conftest

from .plot_dist_interval_run_api_cmd import PlotDistIntervalRunApiCmd

console = ConsoleAdapter()


# TODO remove VCR when this becomes an actual CLI.
def configure_vcr():
    return vcr_module.VCR(**conftest.vcr_config_dict())


# TODO fix help string.
@click.command(
    cls=BaseClickCommand,
    name="plot-time-interval-run",
    help="""Plot a time interval run.""",
)
@click.argument(
    # REQUIRED arg (via cli arg or questionary).
    # id (int) of Garmin activity to analyze or "LATEST" or "LATEST-3".
    "garmin-activity-id",
    nargs=1,
    type=ACTIVITY_ID_TYPE,
    # help="Garmin activity id or LATEST or LATEST-3",
    # Required False because the user might use questionary prompt.
    required=False,  # `click.argument` is required by default (unlike `click.option`).
)
def plot_interval_run_api_cli_view(
    # id (int) of Garmin activity to analyze or ("LATEST", 0) or ("LATEST", -3).
    garmin_activity_id: int | tuple[str, int] | None = None,
) -> None:
    """
    Plot the given Garmin activity id as an interval run.
    """
    save_to_png_file_path = base_plot.make_png_file_path(ROOT_DIR / "output-images")

    p = PlotDistIntervalRunApiCmd(
        garmin_activity_id,
        distance=1000,
        n_expected_intervals=[8],
        # intervals_plan=intervals_plan, # TODO
        # pace_plot_clip_y_axis=pace_plot_clip_y_axis,
        # do_skip_hr_in_pace_plot=do_skip_hr_in_pace_plot,
        title="8x1000m",
        # figure_size=figure_size,
    )

    # TODO remove VCR when this becomes an actual CLI.
    # Configure VCR.py.
    vcr = configure_vcr()
    # Use VCR.py with the cassette named after this file and in this same dir.
    cassette_path = (
        Path(__file__).parent / "cassettes" / (Path(__file__).stem + ".yaml")
    )
    console.print(f"[italic dim]Using VCR.py cassette: {cassette_path}[/]")
    with vcr.use_cassette(cassette_path):
        try:
            return p.plot(save_to_png_file_path=save_to_png_file_path)
        # Enrich VCR.py's `CannotOverwriteExistingCassetteException` original exception
        #  with some useful info.
        except Exception as exc:
            if isinstance(exc, CannotOverwriteExistingCassetteException) or isinstance(
                getattr(exc, "kwargs", dict()).get("error"),
                CannotOverwriteExistingCassetteException,
            ):
                args = list(exc.args)
                args[0] += "\nUse IS_VCR_EPISODE_OR_ERROR=no to record a new episode."
                exc.args = tuple(args)
            raise


if __name__ == "__main__":
    print("START")
    plot_interval_run_api_cli_view()
    print("END")
