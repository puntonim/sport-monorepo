import os
from contextlib import suppress
from pathlib import Path

import click
import datetime_utils
import questionary

from ...base_cli_view import ACTIVITY_ID_TYPE, BaseClickCommand, ConsoleAdapter
from ...conf.settings_module import ROOT_DIR
from .plot_interval_run_api_cmd import DISTANCE_ENUM, PlotIntervalRunApiCmd

QUESTIONARY_SELECT_STYLE = questionary.Style([("highlighted", "fg:red")])

console = ConsoleAdapter()


@click.command(
    cls=BaseClickCommand,
    name="plot-interval-run",
    help="""Plot an interval run.
     
     \b
     EXAMPLES
     \b
     Required args: activity-id, distance.
     So to suppress any interactive questions:
       $ san plot-interval-run 24018992823 -dist 1000 --no-questions
     \b
     Most popular, no questions:
       $ san plot-interval-run LATEST -dist 1000 -n-int 5 --auto-vs-n 3 --no-questions
     To interactively provide input for all filters:
       $ san plot-interval-run
     All possible args, no questions:
       $ san plot-interval-run LATEST-1 -dist 1000 -n-int 5 --auto-vs-n 3 --auto-vs-text '5x1000m 4x1000m' --title 'Ripetute sui mille' --figure-size 5.0 8.5 --dir '/Users/nimiq/workspace/sport-monorepo/projects/sport-analysis/output-images' --no-questions
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
    # REQUIRED arg (via cli arg or questionary).
    "--distance",
    "-dist",
    "distance",
    type=click.Choice((x.value for x in DISTANCE_ENUM), case_sensitive=False),
    help=f"Required distance: {' | '.join(str(x.value) for x in DISTANCE_ENUM)}; eg. -dist 300",
    # required=True,  # `click.option` is NOT required by default (unlike `click.argument`).
)
@click.option(
    # OPTIONAL arg.
    "--n-expected-intervals",
    "-n-int",
    "n_expected_intervals",
    type=int,
    help="Optional # expected intervals in the run; note that intervals shorter/longer than the given distance are auto discarded; omit for default interval ranges; eg. -n-int 5",
)
@click.option(
    # OPTIONAL arg.
    "--activity-id-to-compare",
    "-vs",
    # Note: "prev_runs_activity_ids_*" is plural as this option can be repeated multiple times.
    "prev_runs_activity_ids_to_compare",
    type=int,
    multiple=True,
    help="Optional Garmin activity id of a run to compare; it can be used multiple times; eg. -vs 22407239690 -vs 22214365248 -vs 22038147623",
)
@click.option(
    # OPTIONAL arg.
    "--auto-vs-n",
    "n_prev_runs_to_auto_compare",
    type=int,
    help="Optional # prev runs to AUTO compare; they are searched automatically; eg. --auto-vs-n 3",
)
@click.option(
    # OPTIONAL arg.
    "--auto-vs-text",
    "txt_to_search_for_prev_runs_to_auto_compare",
    type=str,
    help="Optional text used in the search for prev runs to AUTO compare; it's an exact match on Garmin activities' titles; omit this for a smart search like: 1x200m ... 10x200m; eg. --auto-vs-text 5x1000m",
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
    distance: int | DISTANCE_ENUM | None = None,
    n_expected_intervals: int | None = None,
    prev_runs_activity_ids_to_compare: tuple[int] | None = None,
    n_prev_runs_to_auto_compare: int | None = None,
    txt_to_search_for_prev_runs_to_auto_compare: str | None = None,
    title: str | None = None,
    figure_size: tuple[float, float] | None = None,
    dir_or_file_path: Path | None = None,
    do_skip_any_questions: bool = False,
    do_debug_args: bool = False,
) -> None:
    """
    Plot the given Garmin activity id as an interval run.
    """
    # Parse activity_ids_to_compare, n_prev_runs_to_auto_compare,
    #  txt_to_search_for_prev_runs_to_auto_compare.
    if (
        prev_runs_activity_ids_to_compare
        and n_prev_runs_to_auto_compare
        and n_prev_runs_to_auto_compare > 0
    ):
        raise click.BadParameter(
            "--activity-id-to-compare (-vs) and --auto-vs-n args cannot be used together"
        )

    # Parse dir_or_file_path.
    save_to_png_file_path: Path | None = None
    if dir_or_file_path is not None:
        try:
            save_to_png_file_path = _get_png_file_path(dir_or_file_path)
        except DirOrFilePathError as exc:
            raise click.BadParameter(str(exc)) from exc

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
        with suppress(ValidationError):
            garmin_activity_id = _parse_garmin_activity_id_input(
                x, format_like="24018992823 | LATEST-3"
            )
            is_input_valid = True

    # Required arg: distance.
    is_input_valid = True if distance is not None else False
    if not is_input_valid and do_skip_any_questions:
        raise click.BadParameter("--distance required with --no-questions")
    while not is_input_valid:
        text = "*Required* DISTANCE"
        x = (
            # unsafe_ask() so it can be stopped with ctrl-c.
            # Cannot use `validate=<questionary.Validator subclass>` because that is for
            #  the live validation, it's run on every keystroke and returns None.
            questionary.select(
                message=text,
                choices=tuple(str(x.value) for x in DISTANCE_ENUM),
                style=QUESTIONARY_SELECT_STYLE,
            ).unsafe_ask()
            or None
        )
        if x is None:  # Required.
            console.print_error("Required!")
            continue
        with suppress(ValidationError):
            if x is not None:
                distance = _parse_distance_input(x)
            is_input_valid = True

    # Optional arg: n_expected_intervals.
    is_input_valid = True if n_expected_intervals is not None else False
    while not is_input_valid:
        text = "Optional # EXPECTED INTERVALS"
        x = (
            # unsafe_ask() so it can be stopped with ctrl-c.
            # Cannot use `validate=<questionary.Validator subclass>` because that is for
            #  the live validation, it's run on every keystroke and returns None.
            questionary.text(message=text).unsafe_ask()
            or None
        )
        with suppress(ValidationError):
            if x is not None:
                n_expected_intervals = _parse_int_input(x, format_like="5")
            is_input_valid = True

    # Optional arg: prev_runs_activity_ids_to_compare.
    if (
        not n_prev_runs_to_auto_compare
        and not txt_to_search_for_prev_runs_to_auto_compare
    ):  # Cannot be used together.
        is_input_valid = True if prev_runs_activity_ids_to_compare else False
        while not is_input_valid and not do_skip_any_questions:
            text = "Optional ACTIVITIES IDS TO COMPARE (eg. 22407239690 22214365248 22038147623)"
            x = (
                # unsafe_ask() so it can be stopped with ctrl-c.
                # Cannot use `validate=<questionary.Validator subclass>` because that is for
                #  the live validation, it's run on every keystroke and returns None.
                questionary.text(text).unsafe_ask()
                or None
            )
            with suppress(ValidationError):
                if x is not None:
                    prev_runs_activity_ids_to_compare = (
                        _parse_prev_runs_activity_ids_to_compare_input(
                            x, format_like="22407239690 22214365248 22038147623"
                        )
                    )
                is_input_valid = True

    # Optional arg: n_prev_runs_to_auto_compare.
    if not prev_runs_activity_ids_to_compare:  # Cannot be used together.
        is_input_valid = True if n_prev_runs_to_auto_compare is not None else False
        while not is_input_valid and not do_skip_any_questions:
            text = "Optional # PREV RUNS TO AUTO COMPARE (eg. 3)"
            x = (
                # unsafe_ask() so it can be stopped with ctrl-c.
                # Cannot use `validate=<questionary.Validator subclass>` because that is for
                #  the live validation, it's run on every keystroke and returns None.
                questionary.text(message=text).unsafe_ask()
                or None
            )
            if x is None and txt_to_search_for_prev_runs_to_auto_compare:  # Required.
                console.print_error("Required when --auto-vs-text is given!")
                continue
            with suppress(ValidationError):
                if x is not None:
                    n_prev_runs_to_auto_compare = _parse_int_input(x, format_like="5")
                is_input_valid = True

    # Optional arg: txt_to_search_for_prev_runs_to_auto_compare.
    if (
        txt_to_search_for_prev_runs_to_auto_compare is None
        and not do_skip_any_questions
        and n_prev_runs_to_auto_compare
    ):
        text = "Optional TEXT TO SEARCH FOR PREV RUNS TO AUTO COMPARE (eg. 5x1000m)\n  It's an exact match on Garmin activities' titles\n  Leave blank for a smart search like: 1x200m ... 10x200m"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        txt_to_search_for_prev_runs_to_auto_compare = (
            questionary.text(text).unsafe_ask() or None
        )

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
        with suppress(ValidationError):
            if x is not None:
                figure_size = _parse_tuple_of_floats_input(
                    x, tuple_size=2, format_like="5.0 7.0"
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
        with suppress(ValidationError):
            if x is not None:
                save_to_png_file_path = _parse_dir_or_file_path_input(
                    x, format_like="output-images | /tmp/my-dir | /tmp/foo.png"
                )
            is_input_valid = True

    # Print how to re-run this command.
    if not do_skip_any_questions:
        activity_id_str = garmin_activity_id
        if isinstance(garmin_activity_id, tuple):
            activity_id_str = garmin_activity_id[0]
            if garmin_activity_id[1] != 0:
                activity_id_str += str(garmin_activity_id[1])
        cli_msg = f"$ san plot-interval-run {activity_id_str} -dist {distance}"
        if n_expected_intervals is not None:
            cli_msg += f" -n-int {n_expected_intervals}"
        if prev_runs_activity_ids_to_compare:
            cli_msg += f" -vs {' -vs '.join(str(x) for x in prev_runs_activity_ids_to_compare)}"
        if n_prev_runs_to_auto_compare is not None:
            cli_msg += f" --auto-vs-n {n_prev_runs_to_auto_compare}"
        if txt_to_search_for_prev_runs_to_auto_compare:
            cli_msg += (
                f" --auto-vs-text '{txt_to_search_for_prev_runs_to_auto_compare}'"
            )
        if title:
            cli_msg += f" --title '{title}'"
        if figure_size:
            cli_msg += f" --figure-size {' '.join(str(x) for x in figure_size)}"
        if dir_or_file_path:
            cli_msg += f" --dir '{dir_or_file_path}'"
        cli_msg += " --no-questions"
        console.print(f"\nYou can re-run this same command with:\n{cli_msg}\n")

    # If do_debug_args then print all the provided args.
    if do_debug_args:
        for arg in (
            "garmin_activity_id",
            "distance",
            "n_expected_intervals",
            "prev_runs_activity_ids_to_compare",
            "n_prev_runs_to_auto_compare",
            "txt_to_search_for_prev_runs_to_auto_compare",
            "title",
            "figure_size",
            "do_skip_any_questions",
            "do_debug_args",
        ):
            console.print(f"{arg}: {locals()[arg]} | {type(locals()[arg])}")
        console.print(
            f"dir_or_file_path: {save_to_png_file_path} | {type(save_to_png_file_path)}"
        )

    plot_interval = PlotIntervalRunApiCmd(
        garmin_activity_id,
        distance=distance,
        n_expected_intervals=(
            (n_expected_intervals,) if n_expected_intervals is not None else None
        ),
        prev_runs_activity_ids_to_compare=prev_runs_activity_ids_to_compare or None,
        n_prev_runs_to_auto_compare=n_prev_runs_to_auto_compare,
        txt_to_search_for_prev_runs_to_auto_compare=txt_to_search_for_prev_runs_to_auto_compare,
        title=title,
        figure_size=figure_size,
    )
    return plot_interval.plot(save_to_png_file_path=save_to_png_file_path)


def _parse_garmin_activity_id_input(value: str, format_like="24018992823 | LATEST-3"):
    try:
        parsed: int | tuple[str, int] = ACTIVITY_ID_TYPE.convert(value)
    except (ValueError, click.BadParameter) as exc:
        msg = f"{exc}\nFormat like: {format_like}"
        console.print_error(msg)
        raise ValidationError(msg) from exc
    return parsed


def _parse_distance_input(value: str):
    valid_values = " | ".join(str(x.value) for x in DISTANCE_ENUM)
    try:
        value = int(value)
    except ValueError as exc:
        msg = f"{value} is not a int\nValid values: {valid_values}"
        console.print_error(msg)
        raise ValidationError(msg) from exc
    if value not in DISTANCE_ENUM:
        msg = f"Valid values: {valid_values}"
        console.print_error(msg)
        raise ValidationError(msg)
    return value


def _parse_int_input(value: str, format_like="5"):
    try:
        value = int(value)
    except ValueError as exc:
        msg = f"{value} is not a int\nFormat like: {format_like}"
        console.print_error(msg)
        raise ValidationError(msg) from exc
    return value


def _parse_prev_runs_activity_ids_to_compare_input(
    value: str, format_like="22407239690 22214365248 22038147623"
):
    data = value.split(" ")
    to_return = []

    for datum in data:
        try:
            to_return.append(int(datum))
        except ValueError as exc:
            msg = f"{datum} is not a int\nFormat like: {format_like}"
            console.print_error(msg)
            raise ValidationError(msg) from exc
    return tuple(to_return)


def _parse_tuple_of_floats_input(
    value: str, tuple_size: int = 2, format_like: str = "5.0 7.0"
):
    data = value.split(" ")
    if not len(data) == tuple_size:
        msg = f"The len is not {tuple_size}\nFormat like: {format_like}"
        console.print_error(msg)
        raise ValidationError(msg)
    to_return = []
    for datum in data:
        try:
            to_return.append(float(datum))
        except ValueError as exc:
            msg = f"{datum} is not a float\nFormat like: {format_like}"
            console.print_error(msg)
            raise ValidationError(msg) from exc
    return tuple(to_return)


def _parse_dir_or_file_path_input(value: str, format_like="/tmp/my-dir | /tmp/foo.png"):
    try:
        value = click.Path(
            exists=False,
            file_okay=True,
            dir_okay=True,
            readable=True,
            writable=True,
            resolve_path=True,
            path_type=Path,
        ).convert(value, None, None)
    except click.BadParameter as exc:
        msg = f"{exc or 'Invalid input'}\nFormat like: {format_like}"
        console.print_error(msg)
        raise ValidationError(msg) from exc

    try:
        return _get_png_file_path(value)
    except DirOrFilePathError as exc:
        msg = str(exc)
        console.print_error(msg)
        raise ValidationError(msg) from exc


def _get_png_file_path(dir_or_file_path: Path):
    """
    Given a dir path, it creates a .png file path, in that dir and with the current
     timestamp as name, and it makes sure that it does not exist and it is writable.

    Given a .png file path, it makes sure it does not exist and it is writable.
    """
    save_to_png_file_path: Path | None = None

    # If the path is a file (not a dir).
    if dir_or_file_path.suffix:
        # It's a .png file.
        if dir_or_file_path.suffix == ".png":
            if dir_or_file_path.exists():
                raise DirOrFilePathError(
                    f"The given .png file already exists: {dir_or_file_path}"
                )
        # Else, not a .png file.
        else:
            raise DirOrFilePathError(f"Not a .png file path: {dir_or_file_path}")
        save_to_png_file_path: Path = dir_or_file_path

    # Else, the path is a dir.
    else:
        if not dir_or_file_path.exists():
            raise DirOrFilePathError(
                f"The given dir does not exists: {dir_or_file_path}"
            )

        # Eg. "2025-05-13T21:01:33.752427+02:00".
        get_ts = (
            lambda: datetime_utils.now()
            .isoformat()
            .replace(":", "-")
            .replace(".", "-")
            .replace("+", "-")
        )
        while (save_to_png_file_path := dir_or_file_path / f"{get_ts()}.png").exists():
            ...

    # Finally make sure the parent dir is writable.
    if not os.access(save_to_png_file_path.parent, os.W_OK):
        raise DirOrFilePathError(f"Dir not writable: {save_to_png_file_path.parent}")

    return save_to_png_file_path


class BasePlotIntervalRunApiCliException(Exception): ...


class ValidationError(BasePlotIntervalRunApiCliException): ...


class DirOrFilePathError(BasePlotIntervalRunApiCliException): ...
