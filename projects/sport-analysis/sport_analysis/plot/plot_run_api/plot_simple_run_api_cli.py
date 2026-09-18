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
from ...utils import questionary_parsers
from .. import base_plot
from .plot_simple_run_api_cmd import PlotSimpleRunApiCmd

console = ConsoleAdapter()


@click.command(
    cls=BaseClickCommand,
    name="plot-simple-run",
    help="""
    Plot a simple run. It can be a 10km, 21km, 8km or any distance run.
    
    \b
    EXAMPLES
    \b
    Required args: activity-id.
    So to suppress any interactive questions:
      $ san plot-simple-run LATEST --no-questions
    \b
    Most popular, no questions:
      $ san plot-simple-run LATEST --percentile-to-draw P80 -hatch Z3 --no-questions
      $ san plot-simple-run 23309590263 -vs 19074660632 -vs 23226614861
    To interactively provide input for all options:
      $ san plot-simple-run
    All possible args, no questions:
      $ san plot-simple-run 23309590263 -vs 19074660632 -vs 23226614861 -hatch Z0 -hatch Z1 --percentile-to-draw P98 --pace-plot-set-y-axis-bottom-to-slowest-pace-perc 3.5 --title 'Fosso BG' --figure-size 5.0 6.5 --dir '/tmp/output-images'
    """,
)
@click.argument(
    # REQUIRED arg (via cli arg or questionary).
    # id (int) of Garmin activity to analyze or "LATEST" or "LATEST-3".
    "garmin-activity-id",
    nargs=1,
    type=ACTIVITY_ID_TYPE,
    # help="Garmin activity id or LATEST or LATEST-3",
    required=False,  # `click.argument` is required by default (unlike `click.option`).
)
@click.option(
    # OPTIONAL arg.
    "--activity-id-to-compare",
    "-vs",
    # Note: "prev_runs_activity_ids_*" is plural as this option can be repeated multiple times.
    "prev_runs_activity_ids_to_compare",
    type=int,
    multiple=True,
    help="Optional Garmin activity id of a run to compare; it can be used multiple times; eg. -vs 23309590263 -vs 23226614861 -vs 23035885088 -vs 22893403669",
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
    # OPTIONAL arg.
    "--percentile-to-draw",
    type=click.Choice(
        [*base_plot.PERCENTILE_TO_DRAW_ENUM],
        case_sensitive=False,
    ),
    help="Optional percentile to draw in histogram; P80 is great for a 80/20 run, P98 for a slow run; eg. --percentile-to-draw P80 | --percentile-to-draw P98",
)
@click.option(
    # OPTIONAL arg.
    "--pace-plot-clip-y-axis",
    "pace_plot_clip_y_axis",
    nargs=2,
    type=click.Tuple([float, float]),
    help="Optionally cutting out, of the visible part of the pace plot,"
    " the top % and bottom % of data (so the fastest and slowest datapoints);"
    " the plot becomes less compressed vertically; eg. --pace-plot-clip-y-axis 1.3 0.45 | --pace-plot-clip-y-axis 0 0.45",
)
@click.option(
    # OPTIONAL arg.
    "--pace-plot-rolling-window-size",
    "pace_plot_rolling_window_size",
    type=int,
    help="Optional, to smooth out the peaks in the pace plot by customizing the size of"
    " the rolling window used in the moving average; if none it defaults to 15"
    " datapoints (about 15 secs); eg. --pace-plot-rolling-window-size 60",
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
    "--with-elev-in-pace-plot/--without-elev-in-pace-plot",
    "do_add_elev_to_pace_plot",
    is_flag=True,
    default=None,
    help="Optionally force the plotting of elevation in the pace plot; if not given, the elev is auto plotted when > 300m",
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
def plot_simple_run_api_cli_view(
    # id (int) of Garmin activity to analyze or ("LATEST", 0) or ("LATEST", -3).
    garmin_activity_id: int | tuple[str, int],
    prev_runs_activity_ids_to_compare: tuple[int] | None = None,
    # List of HR zones that are "disabled" by hatching (drawing 45deg grey lines).
    hr_zones_to_hatch: tuple[str] | None = None,
    percentile_to_draw: base_plot.PERCENTILE_TO_DRAW_ENUM | None = None,
    pace_plot_clip_y_axis: tuple[float, float] | None = None,
    pace_plot_rolling_window_size: int | None = None,
    do_skip_hr_in_pace_plot: bool = False,
    do_add_elev_to_pace_plot: bool | None = None,
    title: str | None = None,
    figure_size: tuple[float, float] | None = None,
    dir_or_file_path: Path | None = None,
    do_skip_any_questions: bool = False,
    do_debug_args: bool = False,
) -> None:
    """
    Plot the given Garmin activity id as a simple run.
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

    # Optional arg: prev_runs_activity_ids_to_compare.
    is_input_valid = True if prev_runs_activity_ids_to_compare else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional ACTIVITIES IDS TO COMPARE (eg. 23309590263 23226614861 23035885088)\n"
        instruction = "Current PRs 🏆:\n"
        instruction += "    22975082447 5km 19:11 (ESET Melegnano, 22/5/'26)\n"
        instruction += "    22257100921 10km 40:43 (DKRace Monza, 22/3/'26)\n"
        instruction += (
            "    22496738231 HM 1:29:37 (Mezza 2 Laghi Grav.Toce, 12/4/'26)\n  >"
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
                prev_runs_activity_ids_to_compare = (
                    questionary_parsers.parse_multiple_ints_input(
                        x, format_like="23309590263 23226614861 23035885088"
                    )
                )
            is_input_valid = True

    # Optional arg: do_skip_hr_in_pace_plot.
    if prev_runs_activity_ids_to_compare:
        do_skip_hr_in_pace_plot = True
    elif not do_skip_hr_in_pace_plot and not do_skip_any_questions:
        text = "Optional NO HR IN PACE PLOT\n"
        instruction = " Skip adding HR line in the pace plot\n"
        instruction += (
            "  Auto skipped when --activity-id-to-compare is given\n  > (y/N*) "
        )
        do_skip_hr_in_pace_plot = questionary.confirm(
            text, default=False, instruction=instruction, style=QUESTIONARY_STYLE
        ).unsafe_ask()

    # Optional arg: hr_zones_to_hatch.
    if not hr_zones_to_hatch and not do_skip_any_questions:
        text = "Optional HR ZONES TO HATCH\n"
        instruction = (
            ' HR zone to "disable" by hatching (45deg grey lines)\n'
            "  Use Z3 for a 80/20 run (when you want to avoid Z3)\n"
            "  Use Z4 and Z5 for a slow run"
        )
        zones = ("Z0", "Z1", "Z2", "Z3", "Z4", "Z5")
        hr_zones_to_hatch = (
            # unsafe_ask() so it can be stopped with ctrl-c.
            # Cannot use `validate=<questionary.Validator subclass>` because that is for
            #  the live validation, it's run on every keystroke and returns None.
            questionary.checkbox(
                text,
                instruction=instruction,
                choices=zones,
                style=QUESTIONARY_STYLE,
            ).unsafe_ask()
            or None
        )

    # Optional arg: percentile_to_draw.
    if not percentile_to_draw and not do_skip_any_questions:
        text = "Optional PERCENTILE TO DRAW\n"
        instruction = (
            " Use P80 for a 80/20 run\n"
            "  Use P98 for a run entirely slow or fast (like a race)"
        )
        percentile_to_draw = (
            # unsafe_ask() so it can be stopped with ctrl-c.
            # Cannot use `validate=<questionary.Validator subclass>` because that is for
            #  the live validation, it's run on every keystroke and returns None.
            questionary.select(
                text,
                instruction=instruction,
                choices=["*None", *base_plot.PERCENTILE_TO_DRAW_ENUM],
                style=QUESTIONARY_STYLE,
            ).unsafe_ask()
            or None
        )
        if percentile_to_draw == "*None":
            percentile_to_draw = None

    # Optional arg: pace_plot_clip_y_axis.
    is_input_valid = True if pace_plot_clip_y_axis is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional PACE PLOT CLIP Y AXIS (eg. 1.3 0.45 | 0 0.45)\n"
        instruction = (
            "Cut out, of the visible part of the pace plot, the top % and bottom %"
            " of data (so the fastest and slowest datapoints) so the plot becomes"
            " less compressed vertically\n  >"
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

    # Optional arg: pace_plot_rolling_window_size.
    is_input_valid = True if pace_plot_rolling_window_size is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional PACE PLOT ROLLING WINDOW SIZE (eg. 60)\n"
        instruction = (
            "To smooth out the peaks in the pace plot that uses a moving average with"
            " a rolling window size that can be customized, defaults to 15"
            " datapoints (about 15 secs)\n  >"
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
                pace_plot_rolling_window_size = questionary_parsers.parse_int_input(
                    x, format_like="60"
                )
            is_input_valid = True

    # Optional arg: do_add_elev_to_pace_plot.
    if do_add_elev_to_pace_plot is None and not do_skip_any_questions:
        text = "Optional ADD ELEVATION TO PACE PLOT\n"
        instruction = "Forcibly add elevation line to the pace plot\n"
        instruction += " If None, the elevation is auto plotted when >300m"
        # do_add_elev_to_pace_plot = questionary.confirm(
        #     text, default=False, instruction=instruction
        # ).unsafe_ask()
        do_add_elev_to_pace_plot = (
            # unsafe_ask() so it can be stopped with ctrl-c.
            # Cannot use `validate=<questionary.Validator subclass>` because that is for
            #  the live validation, it's run on every keystroke and returns None.
            questionary.select(
                text,
                instruction=instruction,
                choices=["*None", "yes", "no"],
                style=QUESTIONARY_STYLE,
            ).unsafe_ask()
            or None
        )
        if do_add_elev_to_pace_plot == "*None":
            do_add_elev_to_pace_plot = None
        elif do_add_elev_to_pace_plot == "yes":
            do_add_elev_to_pace_plot = True
        else:
            do_add_elev_to_pace_plot = False

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
        cli_msg = f"$ san plot-simple-run {activity_id_str}"
        if prev_runs_activity_ids_to_compare:
            cli_msg += f" -vs {' -vs '.join(str(x) for x in prev_runs_activity_ids_to_compare)}"
        if hr_zones_to_hatch is not None:
            cli_msg += f" -hatch {' -hatch '.join(str(x) for x in hr_zones_to_hatch)}"
        if percentile_to_draw is not None:
            cli_msg += f" --percentile-to-draw {percentile_to_draw}"
        if pace_plot_clip_y_axis is not None:
            cli_msg += f" --pace-plot-clip-y-axis {' '.join(str(x) for x in pace_plot_clip_y_axis)}"
        if pace_plot_rolling_window_size is not None:
            cli_msg += (
                f" --pace-plot-rolling-window-size {pace_plot_rolling_window_size}"
            )
        if do_skip_hr_in_pace_plot:
            cli_msg += f" --no-hr-in-pace-plot"
        if do_add_elev_to_pace_plot is True:
            cli_msg += f" --with-elev-in-pace-plot"
        elif do_add_elev_to_pace_plot is False:
            cli_msg += f" --without-elev-in-pace-plot"
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
            "prev_runs_activity_ids_to_compare",
            "hr_zones_to_hatch",
            "percentile_to_draw",
            "pace_plot_clip_y_axis",
            "pace_plot_rolling_window_size",
            "do_skip_hr_in_pace_plot",
            "do_add_elev_to_pace_plot",
            "title",
            "figure_size",
            "do_skip_any_questions",
            "do_debug_args",
        ):
            console.print(f"{arg}: {locals()[arg]} | {type(locals()[arg])}")
        console.print(
            f"dir_or_file_path: {save_to_png_file_path} | {type(save_to_png_file_path)}"
        )

    p = PlotSimpleRunApiCmd(
        garmin_activity_id,
        prev_runs_activity_ids_to_compare=prev_runs_activity_ids_to_compare or None,
        hr_zones_to_hatch=hr_zones_to_hatch or None,
        percentile_to_draw=percentile_to_draw,
        pace_plot_clip_y_axis=pace_plot_clip_y_axis,
        pace_plot_rolling_window_size=pace_plot_rolling_window_size,
        do_skip_hr_in_pace_plot=do_skip_hr_in_pace_plot,
        do_add_elev_to_pace_plot=do_add_elev_to_pace_plot,
        title=title,
        figure_size=figure_size or None,
    )
    return p.plot(save_to_png_file_path=save_to_png_file_path)


class BasePlotSimpleRunApiCliException(Exception): ...


class DirOrFilePathError(BasePlotSimpleRunApiCliException): ...
