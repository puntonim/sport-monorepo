from pathlib import Path

import click

from ..base_cli_view import (
    ACTIVITY_ID_PARAM_TYPE,
    ACTIVITY_ID_TYPE,
    ActivityId,
    ConsoleAdapter,
)
from ..plot import base_plot

console = ConsoleAdapter()


# TODO deleteme, use parse_activity_id_input instead.
def parse_garmin_activity_id_input(
    value: str, format_like="24018992823 | LATEST-3"
) -> int | tuple[str, int]:
    try:
        parsed: int | tuple[str, int] = ACTIVITY_ID_TYPE.convert(value)
    except (ValueError, click.BadParameter) as exc:
        msg = f"{exc}\nFormat like: {format_like}"
        console.print_error(msg)
        raise ParserValidationError(msg) from exc
    return parsed


def parse_activity_id_input(
    value: str,
    format_like="garmin-23309590263 | g-23309590263 | strava-18988079605 | s-18988079605 | LATEST | LATEST-3",
) -> ActivityId:
    try:
        parsed: ActivityId = ACTIVITY_ID_PARAM_TYPE.convert(value)
    except click.BadParameter as exc:
        msg = f"{exc}\nFormat like: {format_like}"
        console.print_error(msg)
        raise ParserValidationError(msg) from exc
    return parsed


def parse_int_input(value: str, format_like="5"):
    try:
        value = int(value)
    except ValueError as exc:
        msg = f"{value} is not a int\nFormat like: {format_like}"
        console.print_error(msg)
        raise ParserValidationError(msg) from exc
    return value


def parse_multiple_ints_input(
    value: str,
    length: int | None = None,
    format_like: str = "22407239690 22214365248 22038147623",
) -> tuple[int]:
    data = value.split(" ")

    if length is not None and len(data) != length:
        msg = f"The len is not {length}\nFormat like: {format_like}"
        console.print_error(msg)
        raise ParserValidationError(msg)

    to_return = []
    for datum in data:
        try:
            to_return.append(int(datum))
        except ValueError as exc:
            msg = f"{datum} is not a int\nFormat like: {format_like}"
            console.print_error(msg)
            raise ParserValidationError(msg) from exc
    return tuple(to_return)


def parse_float_input(value: str, format_like="0.45"):
    try:
        value = float(value)
    except ValueError as exc:
        msg = f"{value} is not a int\nFormat like: {format_like}"
        console.print_error(msg)
        raise ParserValidationError(msg) from exc
    return value


def parse_multiple_floats_input(
    value: str, length: int | None = None, format_like: str = "5.0 7.0"
):
    data = value.split(" ")

    if length is not None and len(data) != length:
        msg = f"The len is not {length}\nFormat like: {format_like}"
        console.print_error(msg)
        raise ParserValidationError(msg)

    to_return = []
    for datum in data:
        try:
            to_return.append(float(datum))
        except ValueError as exc:
            msg = f"{datum} is not a float\nFormat like: {format_like}"
            console.print_error(msg)
            raise ParserValidationError(msg) from exc
    return tuple(to_return)


def parse_dir_or_file_path_input(value: str, format_like="/tmp/my-dir | /tmp/foo.png"):
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
        raise ParserValidationError(msg) from exc

    try:
        return base_plot.make_png_file_path(value)
    except base_plot.DirOrFilePathError as exc:
        msg = str(exc)
        console.print_error(msg)
        raise ParserValidationError(msg) from exc


class BaseQuestionaryParsersException(Exception): ...


class ParserValidationError(BaseQuestionaryParsersException): ...
