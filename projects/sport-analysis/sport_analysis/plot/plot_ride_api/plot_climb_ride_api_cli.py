from contextlib import suppress
from pathlib import Path

import click
import questionary

from ...base_cli_view import ACTIVITY_ID_TYPE, BaseClickCommand, ConsoleAdapter
from ...conf.settings_module import ROOT_DIR
from .. import base_plot, questionary_parsers
from ..base_plot import PERCENTILE_TO_DRAW_ENUM
from .plot_climb_ride_api_cmd import PlotClimbRideApiCmd

QUESTIONARY_SELECT_STYLE = questionary.Style([("highlighted", "fg:red")])

console = ConsoleAdapter()


@click.command(
    cls=BaseClickCommand,
    name="plot-climb-ride",
    help="""
    Plot a climb ride.
    
    \b
    EXAMPLES
    \b
     Required args: activity-id.
     So to suppress any interactive questions:
       $ san plot-climb-ride LATEST --no-questions
    \b
    Popular for Selvino:
      $ san plot-climb-ride LATEST --segment-strava-name 'Selvino Fontanella' --segment-tile climb
    Popular for Stelvio:
      $ san plot-climb-ride LATEST --segment-start-meters 0 --segment-end-meters 21110 --segment-tile climb
    To interactively provide input for all options:
      $ san plot-climb-ride
    All possible args, no questions:
      $ san plot-climb-ride 23569511098 -hatch Z0 --percentile-to-draw P98 --segment-start-meters 0 --segment-end-meters 21110 --segment-title 'climb' --title 'Re Stelvio Mapei' --figure-size 5.0 6.5 --dir '/tmp'
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
    "--segment-start-meters",
    type=int,
    help="Optional start of the desired segment, in meters; eg. --segment-start-meters 0",
)
@click.option(
    # OPTIONAL arg.
    "--segment-end-meters",
    type=int,
    help="Optional end of the desired segment, in meters; eg. --segment-end-meters 21110",
)
@click.option(
    # OPTIONAL arg.
    "--segment-title",
    type=str,
    help="Optional segment name to draw; eg. --segment-title 'Selvino Fontanella'",
)
@click.option(
    # OPTIONAL arg.
    "--segment-strava-name",
    type=str,
    help="Optional name of the Strava segment; it cannot be used together with segment_start|end_meters; eg. --segment-strava-name 'Selvino Fontanella'",
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
def plot_climb_ride_api_cli_view(
    # id (int) of Garmin activity to analyze or ("LATEST", 0) or ("LATEST", -3).
    garmin_activity_id: int | tuple[str, int],
    # List of HR zones that are "disabled" by hatching (drawing 45deg grey lines).
    hr_zones_to_hatch: tuple[str] | None = None,
    percentile_to_draw: PERCENTILE_TO_DRAW_ENUM | None = None,
    segment_start_meters: int | None = None,
    segment_end_meters: int | None = None,
    segment_title: str | None = None,
    segment_strava_name: str | None = None,
    title: str | None = None,
    figure_size: tuple[float] | None = None,
    dir_or_file_path: Path = ROOT_DIR / "output-images",
    do_skip_any_questions: bool = False,
    do_debug_args: bool = False,
) -> None:
    """
    Plot the HR histogram for the given Garmin activity id as a bike ride.
    """
    # Parse dir_or_file_path.
    save_to_png_file_path: Path | None = None
    if dir_or_file_path is not None:
        try:
            save_to_png_file_path = base_plot.make_png_file_path(dir_or_file_path)
        except base_plot.DirOrFilePathError as exc:
            raise click.BadParameter(str(exc)) from exc

    # Ensure that
    #   segment_start|end_meters AND segment_strava_name
    #  are NOT given together.
    if segment_strava_name and (segment_start_meters or segment_end_meters):
        raise click.BadParameter(
            "Either segment-strava-name or (segment-start-meters and segment-end-meters)"
        )

    ## Prompt for all args that were not provided in the CLI.
    # Required arg: garmin_activity_id.
    is_input_valid = True if garmin_activity_id else False
    if not is_input_valid and do_skip_any_questions:
        raise click.BadParameter("activity id required with --no-questions")
    while not is_input_valid:
        text = "*Required* Garmin ACTIVITY ID (eg. 24018992823 | LATEST-3)"
        x = (
            # unsafe_ask() so it can be stopped with ctrl-c.
            # Cannot use `validate=<questionary.Validator subclass>` because that is for
            #  the live validation, it's run on every keystroke and returns None.
            questionary.text(text).unsafe_ask()
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

    # Optional arg: hr_zones_to_hatch.
    if not hr_zones_to_hatch and not do_skip_any_questions:
        text = (
            "Optional HR ZONES TO HATCH\n"
            'HR zone to "disable" by hatching (45deg grey lines)\n'
            "Use Z3 for a 80/20 run (when you want to avoid Z3)\n"
            "Use Z4 and Z5 for a slow run"
        )
        zones = ("Z0", "Z1", "Z2", "Z3", "Z4", "Z5")
        hr_zones_to_hatch = (
            # unsafe_ask() so it can be stopped with ctrl-c.
            # Cannot use `validate=<questionary.Validator subclass>` because that is for
            #  the live validation, it's run on every keystroke and returns None.
            questionary.checkbox(
                text, choices=zones, style=QUESTIONARY_SELECT_STYLE
            ).unsafe_ask()
            or None
        )

    # Optional arg: percentile_to_draw.
    if not percentile_to_draw and not do_skip_any_questions:
        text = (
            "Optional PERCENTILE TO DRAW\n"
            "Use P80 for a 80/20 run\n"
            "Use P98 for a run entirely slow or fast (like a race)"
        )
        percentile_to_draw = (
            # unsafe_ask() so it can be stopped with ctrl-c.
            # Cannot use `validate=<questionary.Validator subclass>` because that is for
            #  the live validation, it's run on every keystroke and returns None.
            questionary.select(
                text,
                choices=["*None", *base_plot.PERCENTILE_TO_DRAW_ENUM],
                style=QUESTIONARY_SELECT_STYLE,
            ).unsafe_ask()
            or None
        )
        if percentile_to_draw == "*None":
            percentile_to_draw = None

    # Optional arg: segment_start_meters.
    if segment_strava_name is None:
        is_input_valid = True if segment_start_meters is not None else False
        while not is_input_valid and not do_skip_any_questions:
            text = "Optional SEGMENT START METERS (eg. 5000)"
            # unsafe_ask() so it can be stopped with ctrl-c.
            # Cannot use `validate=<questionary.Validator subclass>` because that is for
            #  the live validation, it's run on every keystroke and returns None.
            x = questionary.text(text).unsafe_ask() or None
            with suppress(questionary_parsers.ParserValidationError):
                if x is not None:
                    segment_start_meters = questionary_parsers.parse_int_input(
                        x, format_like="5000"
                    )
                is_input_valid = True

    # Optional arg: segment_end_meters.
    if segment_strava_name is None:
        is_input_valid = True if segment_end_meters is not None else False
        while not is_input_valid and not do_skip_any_questions:
            text = "Optional SEGMENT END METERS (eg. 21110)"
            # unsafe_ask() so it can be stopped with ctrl-c.
            # Cannot use `validate=<questionary.Validator subclass>` because that is for
            #  the live validation, it's run on every keystroke and returns None.
            x = questionary.text(text).unsafe_ask() or None
            with suppress(questionary_parsers.ParserValidationError):
                if x is not None:
                    segment_end_meters = questionary_parsers.parse_int_input(
                        x, format_like="21110"
                    )
                is_input_valid = True

    # Optional arg: segment_title.
    if segment_title is None and not do_skip_any_questions:
        text = "Optional SEGMENT TITLE (eg. Selvino Fontanella)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        segment_title = questionary.text(text).unsafe_ask() or None

    # Optional arg: segment_strava_name.
    if segment_start_meters is None and segment_end_meters is None:
        if segment_strava_name is None and not do_skip_any_questions:
            text = (
                "Optional SEGMENT STRAVA NAME\n"
                "Known segments:\n"
                "  Selvino Fontanella\n"
                "  Passo Stelvio (via Bormio)\n"
                "  (dm) Maresana\n"
                "  Salita Croce dei Morti da Maresana fontanella"
            )
            # TODO change this ^^ into a proper Select
            # unsafe_ask() so it can be stopped with ctrl-c.
            # Cannot use `validate=<questionary.Validator subclass>` because that is for
            #  the live validation, it's run on every keystroke and returns None.
            segment_strava_name = questionary.text(text).unsafe_ask() or None

    # Optional arg: title.
    if title is None and not do_skip_any_questions:
        text = "Optional TITLE (eg. 80/20 run)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        title = questionary.text(text).unsafe_ask() or None

    # Optional arg: figure_size.
    is_input_valid = True if figure_size is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional FIGURE SIZE (eg. 5.0 7.0)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(questionary_parsers.ParserValidationError):
            if x is not None:
                figure_size = questionary_parsers.parse_multiple_floats_input(
                    x, length=2, format_like="5.0 7.0"
                )
            is_input_valid = True

    # Optional arg: dir_or_file_path.
    is_input_valid = True if save_to_png_file_path is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = (
            "Optional DIR or FILE PATH (eg. output-images | /tmp/my-dir | /tmp/foo.png)"
        )
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = (
            questionary.text(
                text, default=str((ROOT_DIR / "output-images").relative_to(ROOT_DIR))
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

    # Print how to re-run this command.
    if not do_skip_any_questions:
        activity_id_str = garmin_activity_id
        if isinstance(garmin_activity_id, tuple):
            activity_id_str = garmin_activity_id[0]
            if garmin_activity_id[1] != 0:
                activity_id_str += str(garmin_activity_id[1])
        cli_msg = f"$ san plot-climb-ride {activity_id_str}"
        if hr_zones_to_hatch is not None:
            cli_msg += f" -hatch {' -hatch '.join(str(x) for x in hr_zones_to_hatch)}"
        if percentile_to_draw is not None:
            cli_msg += f" --percentile-to-draw {percentile_to_draw}"
        if segment_start_meters is not None:
            cli_msg += f" --segment-start-meters {segment_start_meters}"
        if segment_end_meters is not None:
            cli_msg += f" --segment-end-meters {segment_end_meters}"
        if segment_title is not None:
            cli_msg += f" --segment-title '{segment_title}'"
        if segment_strava_name is not None:
            cli_msg += f" --segment-strava-name '{segment_strava_name}'"
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
            "hr_zones_to_hatch",
            "percentile_to_draw",
            "segment_start_meters",
            "segment_end_meters",
            "segment_title",
            "segment_strava_name",
            "title",
            "figure_size",
            "do_skip_any_questions",
            "do_debug_args",
        ):
            console.print(f"{arg}: {locals()[arg]} | {type(locals()[arg])}")
        console.print(
            f"dir_or_file_path: {save_to_png_file_path} | {type(save_to_png_file_path)}"
        )

    plot_ride = PlotClimbRideApiCmd(
        garmin_activity_id,
        hr_zones_to_hatch=hr_zones_to_hatch or None,
        percentile_to_draw=percentile_to_draw,
        title=title,
        segment_start_meters=segment_start_meters,
        segment_end_meters=segment_end_meters,
        segment_title=segment_title,
        segment_strava_name=segment_strava_name,
        figure_size=figure_size,
    )
    return plot_ride.plot(save_to_png_file_path=save_to_png_file_path)
