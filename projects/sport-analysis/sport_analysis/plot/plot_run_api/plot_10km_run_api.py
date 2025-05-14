from pathlib import Path

import click
import datetime_utils

from ...base_cli_view import BaseClickCommand
from ...conf.settings_module import ROOT_DIR
from .base_plot_run_api import BasePlotRunApi


@click.command(
    cls=BaseClickCommand,
    name="plot-10km-run",
    help='Plot a 10km run; eg: analysis plot-10km-run 19005790234 -vs 19074660632 -vs 18797516250 --title "Fosso BG" --figure-size 5.0 6.5 --pace-plot-set-y-axis-bottom-to-slowest-pace-perc 3.5 -d ~/workspace/sport-monorepo/projects/sport-analysis/output-images/',
)
@click.argument("garmin-activity-id", nargs=1, type=int)
@click.option(
    "--activity-id-to-compare",
    "-vs",
    "activity_ids_to_compare",
    type=int,
    multiple=True,
    help="Garmin activity id to compare; it can be used multiple times",
)
@click.option("--title", type=str)
@click.option(
    "--figure-size",
    nargs=2,
    type=click.Tuple([float, float]),
    help="eg. 5.0 7.0; a tuple of floats",
)
@click.option(
    "--pace-plot-set-y-axis-bottom-to-slowest-pace-perc",
    type=float,
    help="eg. 0.45; in the MA(pace) chart, cutting out of the visible part of the chart"
    " the slowest 0.45% pace datapoints; this is done because it is better visually:"
    " the chart is less compressed vertically",
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
def plot_10km_run_api_cli_view(
    garmin_activity_id: int,
    activity_ids_to_compare: list[int] | None = None,
    title: str | None = None,
    figure_size: tuple[float, float] | None = None,
    pace_plot_set_y_axis_bottom_to_slowest_pace_perc: float | None = None,
    dir_or_file_path: Path = ROOT_DIR / "output-images",
) -> None:
    """
    Plot the given Garmin activity id as a 10km run.
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

    plot_10k = Plot10KmRunApi(
        garmin_activity_id,
        activity_ids_to_compare=[x for x in activity_ids_to_compare],  # Tuple to list.
        title=title,
        figure_size=figure_size,
        pace_plot_set_y_axis_bottom_to_slowest_pace_perc=pace_plot_set_y_axis_bottom_to_slowest_pace_perc,
    )
    return plot_10k.plot(save_to_png_file_path=save_to_png_file_path)


class Plot10KmRunApi(BasePlotRunApi):
    DEFAULT_ACTIVITY_IDS_TO_COMPARE = [
        19005790234,  # Fosso BG 1 Cologno on 02/05/2025.
        19074660632,  # Fosso BG 2 Camisano on 09/05/2025.
    ]
