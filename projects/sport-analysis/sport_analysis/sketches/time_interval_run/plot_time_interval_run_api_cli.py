"""
During a run class (garmin id 24387737173) I run 16 intervals: 1 min fast and 1 min slow.
The first  interval (starting at 0 seconds) was a fast one.
The last interval was a slow one.

Note: this script uses VCR.py to record HTTP interactions. Just because I wanted to
 test how to use VCR.py in a live code.

Usage:
    $ poetry run python -m sport_analysis.sketches.time_interval_run.plot_time_interval_run_api_cli 24387737173
    To record new VCR.py episodes:
    $ IS_VCR_EPISODE_OR_ERROR=n poetry run python -m sport_analysis.sketches.time_interval_run.plot_time_interval_run_api_cli 24387737173
"""

from contextlib import suppress
from pathlib import Path

import click
import questionary

from ...base_cli_view import (
    ACTIVITY_ID_TYPE,
    QUESTIONARY_STYLE,
    BaseClickCommand,
    ConsoleAdapter,
)
from ...conf.settings_module import ROOT_DIR
from ...plot import base_plot
from ...utils import questionary_parsers
from .intervals_plan import IntervalsPlan, IntervalsPlanParamType
from .plot_time_interval_run_api_cmd import PlotTimeIntervalRunApiCmd

console = ConsoleAdapter()

INTERVALS_PLAN_PARAM_TYPE = IntervalsPlanParamType()


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
# TODO
# @click.option(
#     # REQUIRED arg (via cli arg or questionary).
#     "--plan",
#     "intervals_plan",
#     type=INTERVALS_PLAN_PARAM_TYPE,
#     help=f"Required interval plan; eg. --plan 16x 60s@fast 60s@slow",
#     # required=True,  # `click.option` is NOT required by default (unlike `click.argument`).
# )
@click.option(
    # OPTIONAL arg.
    "--pace-plot-clip-y-axis",
    "pace_plot_clip_y_axis",
    nargs=2,
    type=click.Tuple([float, float]),
    help="Optionally cutting out, of the visible part of the pace plot,"
    " the top % and bottom % of data (so the fastest and slowest datapoints);"
    " the plot becomes less compressed vertically; order: top, bottom; eg. --pace-plot-clip-y-axis 1.3 0.45 | --pace-plot-clip-y-axis 0 0.45",
)
@click.option(
    # OPTIONAL arg.
    "--without-hr-in-pace-plot",
    "do_skip_hr_in_pace_plot",
    is_flag=True,
    default=False,
    help="Optionally skip adding HR line in the pace plot; auto skipped when --activity-id-to-compare is given",
)
@click.option(
    # OPTIONAL arg.
    "--title",
    type=str,
    help="Optional title; eg. --title '5x1000m'",
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
        exists=False,
        file_okay=True,
        dir_okay=True,
        readable=True,
        writable=True,
        resolve_path=True,
        path_type=Path,
    ),
    help="Optional DIR or FILE PATH; eg. -d output-images | -d /tmp/my-dir | -d /tmp/foo.png",
)
@click.option(
    # OPTIONAL arg.
    "--no-questions",
    "-no-?",  # Note: use -no-\? in the shell.
    "-no?",  # Note: use -no\? in the shell.
    "-no-q",
    "-noq",
    "do_skip_any_questions",
    is_flag=True,
    default=False,
    help="Do not ask any questions to provide args via user input",
)
@click.option(
    # OPTIONAL arg.
    "--debug-args",
    "do_debug_args",
    is_flag=True,
    default=False,
    help="Print debug info about the provided args",
)
def plot_interval_run_api_cli_view(
    # id (int) of Garmin activity to analyze or ("LATEST", 0) or ("LATEST", -3).
    garmin_activity_id: int | tuple[str, int] | None = None,
    # intervals_plan: IntervalsPlan | None = None, # TODO
    pace_plot_clip_y_axis: tuple[float, float] | None = None,
    do_skip_hr_in_pace_plot: bool = False,
    title: str | None = None,
    figure_size: tuple[float, float] | None = None,
    dir_or_file_path: Path | None = None,
    do_skip_any_questions: bool = False,
    do_debug_args: bool = False,
) -> None:
    """
    Plot the given Garmin activity id as an interval run.
    """

    # Parse dir_or_file_path.
    save_to_png_file_path: Path | None = None
    if dir_or_file_path is not None:
        try:
            save_to_png_file_path = base_plot.make_png_file_path(dir_or_file_path)
        except base_plot.DirOrFilePathError as exc:
            raise click.BadParameter(str(exc)) from exc

    ## Prompt for all args that were not provided in the CLI.
    # Required arg: garmin_activity_id.
    is_input_valid = True if garmin_activity_id else False
    if not is_input_valid and do_skip_any_questions:
        raise click.BadParameter("activity id required with --no-questions")
    while not is_input_valid:
        text = "*Required* Garmin ACTIVITY ID (eg. 24018992823 | LATEST-3)\n"
        instruction = ">"
        x = (
            # unsafe_ask() so it can be stopped with ctrl-c.
            # Cannot use `validate=<questionary.Validator subclass>` because that is for
            #  the live validation, it's run on every keystroke and returns None.
            questionary.text(
                text, instruction=instruction, style=QUESTIONARY_STYLE
            ).unsafe_ask()
            or None
        )
        if x is None:  # Required.
            console.print_error("Required!")
            continue
        with suppress(questionary_parsers.ParserValidationError):
            garmin_activity_id = questionary_parsers.parse_garmin_activity_id_input(
                x, format_like="24018992823 | LATEST-3"
            )
            is_input_valid = True

    # Optional arg: intervals_plan.  # TODO

    # Optional arg: pace_plot_clip_y_axis.
    is_input_valid = True if pace_plot_clip_y_axis is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional PACE PLOT CLIP Y AXIS (eg. 1.3 0.45 | 0 0.45)\n"
        instruction = (
            "Cut out, of the visible part of the pace plot, the top % and bottom %"
            " of data (so the fastest and slowest datapoints) so the plot becomes"
            " less compressed vertically\nOrder: top, bottom\n  >"
        )
        x = (
            # unsafe_ask() so it can be stopped with ctrl-c.
            # Cannot use `validate=<questionary.Validator subclass>` because that is for
            #  the live validation, it's run on every keystroke and returns None.
            questionary.text(
                text, instruction=instruction, style=QUESTIONARY_STYLE
            ).unsafe_ask()
            or None
        )
        with suppress(questionary_parsers.ParserValidationError):
            if x is not None:
                pace_plot_clip_y_axis = questionary_parsers.parse_multiple_floats_input(
                    x, length=2, format_like="0.3 1.35"
                )
            is_input_valid = True

    # Optional arg: do_skip_hr_in_pace_plot.
    if not do_skip_hr_in_pace_plot and not do_skip_any_questions:
        text = "Optional NO HR IN PACE PLOT\n"
        instruction = " Skip adding HR line in the pace plot\n  > (y/N*) "
        do_skip_hr_in_pace_plot = questionary.confirm(
            text, default=False, instruction=instruction, style=QUESTIONARY_STYLE
        ).unsafe_ask()

    # Optional arg: title.
    if title is None and not do_skip_any_questions:
        text = "Optional TITLE (eg. 80/20 run)\n"
        instruction = ">"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        title = (
            questionary.text(
                text, instruction=instruction, style=QUESTIONARY_STYLE
            ).unsafe_ask()
            or None
        )

    # Optional arg: figure_size.
    is_input_valid = True if figure_size is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional FIGURE SIZE (eg. 5.0 7.0)\n"
        instruction = ">"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = (
            questionary.text(
                text, instruction=instruction, style=QUESTIONARY_STYLE
            ).unsafe_ask()
            or None
        )
        with suppress(questionary_parsers.ParserValidationError):
            if x is not None:
                figure_size = questionary_parsers.parse_multiple_floats_input(
                    x, length=2, format_like="5.0 7.0"
                )
            is_input_valid = True

    # Optional arg: dir_or_file_path.
    is_input_valid = True if save_to_png_file_path is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional DIR or FILE PATH (eg. output-images | /tmp/my-dir | /tmp/foo.png)\n"
        instruction = ">"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = (
            questionary.text(
                text,
                instruction=instruction,
                default=str((ROOT_DIR / "output-images").relative_to(ROOT_DIR)),
                style=QUESTIONARY_STYLE,
            ).unsafe_ask()
            or None
        )
        with suppress(questionary_parsers.ParserValidationError):
            if x is not None:
                save_to_png_file_path = (
                    questionary_parsers.parse_dir_or_file_path_input(
                        x, format_like="output-images | /tmp/my-dir | /tmp/foo.png"
                    )
                )
            is_input_valid = True
    if save_to_png_file_path is None:
        save_to_png_file_path = base_plot.make_png_file_path(ROOT_DIR / "output-images")

    # Print how to re-run this command.
    if not do_skip_any_questions:
        activity_id_str = garmin_activity_id
        if isinstance(garmin_activity_id, tuple):
            activity_id_str = garmin_activity_id[0]
            if garmin_activity_id[1] != 0:
                activity_id_str += str(garmin_activity_id[1])
        cli_msg = f"$ san plot-time-interval-run {activity_id_str}"
        # TODO
        #  cli_msg += ... intervals_plan
        if pace_plot_clip_y_axis is not None:
            cli_msg += f" --pace-plot-clip-y-axis {' '.join(str(x) for x in pace_plot_clip_y_axis)}"
        if do_skip_hr_in_pace_plot:
            cli_msg += f" --no-hr-in-pace-plot"
        if title:
            cli_msg += f" --title '{title}'"
        if figure_size:
            cli_msg += f" --figure-size {' '.join(str(x) for x in figure_size)}"
        if save_to_png_file_path:
            cli_msg += f" --dir '{save_to_png_file_path}'"
        cli_msg += " --no-questions"
        console.print(f"\nYou can re-run this same command with:\n{cli_msg}\n")

    # If do_debug_args then print all the provided args.
    if do_debug_args:
        for arg in (
            "garmin_activity_id",
            # "intervals_plan", # TODO
            "pace_plot_clip_y_axis",
            "do_skip_hr_in_pace_plot",
            "title",
            "figure_size",
            "do_skip_any_questions",
            "do_debug_args",
        ):
            console.print(f"{arg}: {locals()[arg]} | {type(locals()[arg])}")
        console.print(
            f"dir_or_file_path: {save_to_png_file_path} | {type(save_to_png_file_path)}"
        )

    p = PlotTimeIntervalRunApiCmd(
        garmin_activity_id,
        # intervals_plan=intervals_plan, # TODO
        pace_plot_clip_y_axis=pace_plot_clip_y_axis,
        do_skip_hr_in_pace_plot=do_skip_hr_in_pace_plot,
        title=title,
        figure_size=figure_size,
    )
    return p.plot(save_to_png_file_path=save_to_png_file_path)


if __name__ == "__main__":
    print("START")
    plot_interval_run_api_cli_view()
    print("END")
