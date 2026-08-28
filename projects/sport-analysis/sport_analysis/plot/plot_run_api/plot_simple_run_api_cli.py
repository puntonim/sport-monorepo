from pathlib import Path

import click
import datetime_utils

from ...base_cli_view import ACTIVITY_ID_TYPE, BaseClickCommand
from ...conf.settings_module import ROOT_DIR
from ..base_plot import PERCENTILE_TO_DRAW_ENUM
from .plot_simple_run_api_cmd import PlotSimpleRunApiCmd


@click.command(
    cls=BaseClickCommand,
    name="plot-simple-run",
    help="""
    Plot a simple run. It can be a 10km, 21km, 8km or any distance run.
    
    \b
    Examples
    $ san plot-simple 19005790234 -vs 19074660632 -vs 18797516250 --title "Fosso BG" --figure-size 5.0 6.5 --pace-plot-set-y-axis-bottom-to-slowest-pace-perc 3.5 -d ~/workspace/sport-monorepo/projects/sport-analysis/output-images/
    $ san plot-simple LATEST
    $ san plot-simple LATEST-3
    """,
)
@click.argument(
    # REQUIRED arg (via cli arg or questionary).
    # id (int) of Garmin activity to analyze or "LATEST" or "LATEST-3".
    "garmin-activity-id",
    nargs=1,
    type=ACTIVITY_ID_TYPE,
    # help="Garmin activity id or LATEST or LATEST-3",
    # required=False,  # `click.argument` is required by default (unlike `click.option`).
)
@click.option(
    # OPTIONAL arg.
    "--activity-id-to-compare",
    "-vs",
    # Note: "prev_runs_activity_ids_*" is plural as this option can be repeated multiple times.
    "prev_runs_activity_ids_to_compare",
    type=int,
    multiple=True,
    help="Optional Garmin activity id of a run to compare; it can be used multiple times; eg. -vs 24135607183 -vs 24110014772 -vs 24048184816",
)
@click.option(
    # OPTIONAL arg.
    "--hr-zone-to-hatch",
    "-hatch",
    # Note: "hr_zones_*" is plural as this option can be repeated multiple times.
    "hr_zones_to_hatch",
    type=click.Choice(("Z0", "Z1", "Z2", "Z3", "Z4", "Z5"), case_sensitive=False),
    multiple=True,
    help='Optional HR zone to "disable" by hatching (45deg grey lines); it can be used multiple times; eg. -hatch Z3 -hatch Z4 -hatch Z5',
)
@click.option(
    "--percentile-to-draw",
    type=click.Choice(tuple(x for x in PERCENTILE_TO_DRAW_ENUM), case_sensitive=False),
    help="Optional percentile to draw in histogram; P80 is great for a 80/20 run, P98 for a slow run; eg. --percentile-to-draw P80 | --percentile-to-draw P98",
)
@click.option(
    # OPTIONAL arg.
    "--pace-plot-set-y-axis-bottom-to-slowest-pace-perc",
    type=float,
    help="Optionally cutting out, of the visible part of the MA(pace) chart,"
    " the slowest given % (eg. 0.45%) pace datapoints;"
    " the chart becomes less compressed vertically; eg. --pace-plot-set-y-axis-bottom-to-slowest-pace-perc 0.45",
)
@click.option(
    # OPTIONAL arg.
    "--title",
    type=str,
    help="Optional title; eg. --title '80/20 run'",
)
@click.option(
    # OPTIONAL arg.
    "--figure-size",
    nargs=2,
    type=click.Tuple([float, float]),
    help="Optional figure size; eg. --figure-size 5.0 7.0",
)
@click.option(
    # OPTIONAL arg.
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
    help="Optional DIR or FILE PATH; eg. -d output-images | -d /tmp/my-dir | -d /tmp/foo.png",
)
def plot_simple_run_api_cli_view(
    # id (int) of Garmin activity to analyze or ("LATEST", 0) or ("LATEST", -3).
    garmin_activity_id: int | tuple[str, int],
    prev_runs_activity_ids_to_compare: tuple[int] | None = None,
    # List of HR zones that are "disabled" by hatching (drawing 45deg grey lines).
    hr_zones_to_hatch: tuple[str] | None = None,
    percentile_to_draw: PERCENTILE_TO_DRAW_ENUM | None = None,
    pace_plot_set_y_axis_bottom_to_slowest_pace_perc: float | None = None,
    title: str | None = None,
    figure_size: tuple[float] | None = None,
    dir_or_file_path: Path = ROOT_DIR / "output-images",
) -> None:
    """
    Plot the given Garmin activity id as a simple run.
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

    p = PlotSimpleRunApiCmd(
        garmin_activity_id,
        prev_runs_activity_ids_to_compare=prev_runs_activity_ids_to_compare or None,
        hr_zones_to_hatch=hr_zones_to_hatch or None,
        percentile_to_draw=percentile_to_draw,
        pace_plot_set_y_axis_bottom_to_slowest_pace_perc=pace_plot_set_y_axis_bottom_to_slowest_pace_perc,
        title=title,
        figure_size=figure_size or None,
    )
    return p.plot(save_to_png_file_path=save_to_png_file_path)
