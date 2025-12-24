from contextlib import suppress
from datetime import datetime

import click
import datetime_utils
import questionary
import strava_db_models

from ...base_cli_view import BaseClickCommand, ConsoleAdapter
from .search_strava_api_cmd import KNOWN_STRAVA_SEGMENTS, SearchStravaApiCmd

__all__ = [
    "search_strava_api_cli_view",
]

# Note: all types described in https://github.com/puntonim/sport-monorepo/blob/main/libs/strava-db-models/strava_db_models/strava_db_models.py#L106.
ALL_ACTIVITY_TYPES = set(
    strava_db_models.STRAVA_ACTIVITY_TYPES
    + strava_db_models.strava_db_models._STRAVA_ACTIVITY_SPORT_TYPES
)


console = ConsoleAdapter()


@click.command(
    cls=BaseClickCommand,
    name="search-strava",
    help="""Search activities in Strava API.
    
    \b
    Eg. san search-strava 
    Eg. san search-strava --start-date-after 2024-01-01T00:00:00+01:00 --start-date-before 2024-12-31T23:59:59+01:00
    Eg. san search-strava --title-contains "back, calisthenics"
    Eg. san search-strava --segment selvino --activity-type ride
    """,  # TODO more examples in docstring
)
@click.option(
    "--start-date-after",
    type=click.DateTime(formats=["%Y-%m-%dT%H:%M:%S%z"]),
    help="Optional filter by start date after; eg. 2024-01-01T00:00:00+01:00",
)
@click.option(
    "--start-date-before",
    type=click.DateTime(formats=["%Y-%m-%dT%H:%M:%S%z"]),
    help="Optional filter by start date before; eg. 2024-12-31T23:59:59+01:00",
)
@click.option(
    "--title-contains",
    type=str,
    help="Optional filter by title's substring; eg. 'back, calisthenics'",
)
@click.option(
    # Note: all types described in https://github.com/puntonim/sport-monorepo/blob/main/libs/strava-db-models/strava_db_models/strava_db_models.py#L106.
    "--activity-type",
    type=click.Choice(ALL_ACTIVITY_TYPES, case_sensitive=False),
    help="Optional filter by activity type; eg. ride | mountainbikeride | weighttraining (full list: https://github.com/puntonim/sport-monorepo/blob/main/libs/strava-db-models/strava_db_models/strava_db_models.py#L106)",
)
@click.option(
    "--start-coords",
    "start_latlng",
    nargs=3,
    type=click.Tuple([float, float, int]),
    help="Optional filter by starting location as lat-float lon-float distance-meters-int; eg. 45.745995 9.762249 250",
)
@click.option(
    "--end-coords",
    "end_latlng",
    nargs=3,
    type=click.Tuple([float, float, int]),
    help="Optional filter by ending location as lat-float lon-float distance-meters-int; eg. 45.745995 9.762249 250",
)
@click.option(
    "--location-visited-coords",
    "location_visited_latlng",
    nargs=3,
    type=click.Tuple([float, float, int]),
    help="Optional filter by visited location as lat-float lon-float distance-meters-int; eg. 45.745995 9.762249 250",
)
@click.option(
    "--segment",
    type=str,
    callback=lambda *args, **kwargs: _click_validate_segment_input(*args, **kwargs),
    help="Optional filter by Strava segment; eg. selvino | stelvio | 15756100 (from https://www.strava.com/segments/15756100)",
)
@click.option(
    "--distance-range",
    nargs=2,
    type=click.Tuple([int, int]),
    help="Optional filter by distance range as min-meters-int max-meters-int; eg. 9500 10500",
)
@click.option(
    "--elevation-gain-range",
    nargs=2,
    type=click.Tuple([int, int]),
    help="Optional filter by elevation gain range as min-meters-int max-meters-int; eg. 800 1500",
)
@click.option(
    "--no-questions",
    "do_skip_any_question",
    is_flag=True,
    default=False,
    help="Do not ask any questions to provide args via user input",
)
def search_strava_api_cli_view(
    start_date_after: datetime | str | None = None,
    start_date_before: datetime | str | None = None,
    title_contains: str | None = None,
    # Note: all types described in https://github.com/puntonim/sport-monorepo/blob/main/libs/strava-db-models/strava_db_models/strava_db_models.py#L106.
    activity_type: str | None = None,
    start_latlng: tuple[float, float, int] | None = None,
    end_latlng: tuple[float, float, int] | None = None,
    location_visited_latlng: tuple[float, float, int] | None = None,
    segment: str | None = None,
    distance_range: tuple[int, int] | None = None,
    elevation_gain_range: tuple[int, int] | None = None,
    do_skip_any_question: bool = False,
) -> None:
    ## Prompt for all args that were not provided in the CLI.
    # start_date_after.
    is_input_valid = True if start_date_after is not None else False
    while not is_input_valid and not do_skip_any_question:
        text = "Optional filter by START DATE AFTER (eg. 2024-01-01T00:00:00+01:00)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            start_date_after = _parse_datetime_input(x)
            is_input_valid = True

    # start_date_before.
    is_input_valid = True if start_date_before is not None else False
    while not is_input_valid and not do_skip_any_question:
        text = "Optional filter by START DATE BEFORE (eg. 2024-12-31T23:59:59+01:00)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                start_date_before = _parse_datetime_input(x)
            is_input_valid = True

    # title_contains.
    if title_contains is None and not do_skip_any_question:
        text = "Optional filter by TITLE'S SUBSTRING (eg. back, calisthenics)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        title_contains = questionary.text(text).unsafe_ask() or None

    # activity_type.
    is_input_valid = True if activity_type is not None else False
    while not is_input_valid and not do_skip_any_question:
        text = "Optional filter by ACTIVITY TYPE"
        x = (
            # unsafe_ask() so it can be stopped with ctrl-c.
            questionary.select(text, choices=("*Any", *ALL_ACTIVITY_TYPES)).unsafe_ask()
            or None
        )
        with suppress(ValidationError):
            if x is not None:
                activity_type = _parse_activity_type_input(x)
            is_input_valid = True

    # start_latlng.
    is_input_valid = True if start_latlng is not None else False
    while not is_input_valid and not do_skip_any_question:
        text = "Optional filter by STARTING LOCATION as lat-float lon-float distance-meters-int (eg. 45.745995 9.762249 250)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                start_latlng = _parse_latlng_input(x)
            is_input_valid = True

    # end_latlng.
    is_input_valid = True if end_latlng is not None else False
    while not is_input_valid and not do_skip_any_question:
        text = "Optional filter by ENDING LOCATION as lat-float lon-float distance-meters-int (eg. 45.745995 9.762249 250)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                end_latlng = _parse_latlng_input(x)
            is_input_valid = True

    # location_visited_latlng.
    is_input_valid = True if location_visited_latlng is not None else False
    while not is_input_valid and not do_skip_any_question:
        text = "Optional filter by LOCATION VISITED as lat-float lon-float distance-meters-int (eg. 45.745995 9.762249 250)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                location_visited_latlng = _parse_latlng_input(x)
            is_input_valid = True

    # segment.
    is_input_valid = False
    segment_id = None
    if segment is not None:
        is_input_valid = True
        segment_id = segment
    while not is_input_valid and not do_skip_any_question:
        text = "Optional filter by Strava SEGMENT (eg. selvino | stelvio | 15756100 (from https://www.strava.com/segments/15756100))"
        # unsafe_ask() so it can be stopped with ctrl-c.
        segment = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if segment is not None:
                segment_id = _parse_segment_input(segment)
            is_input_valid = True

    # distance_range.
    is_input_valid = True if distance_range is not None else False
    while not is_input_valid and not do_skip_any_question:
        text = "Optional filter by DISTANCE RANGE as min-meters-int max-meters-int (eg. 9500 10500)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                distance_range = _parse_int_range_input(x)
            is_input_valid = True

    # elevation_gain_range.
    is_input_valid = True if elevation_gain_range is not None else False
    while not is_input_valid and not do_skip_any_question:
        text = "Optional filter by ELEVATION GAIN RANGE as min-meters-int max-meters-int (eg. 800 1500)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                elevation_gain_range = _parse_int_range_input(x)
            is_input_valid = True

    # Print how to re-run this command.
    if not do_skip_any_question:
        cli_msg = "$ san search-strava"
        if start_date_after:
            cli_msg += f" --start-date-after {start_date_after.isoformat()}"
        if start_date_before:
            cli_msg += f" --start-date-before {start_date_before.isoformat()}"
        if title_contains:
            cli_msg += f" --title-contains {title_contains}"
        if activity_type:
            cli_msg += f" --activity-type {activity_type}"
        if start_latlng:
            cli_msg += f" --start-coords {' '.join(str(x) for x in start_latlng)}"
        if end_latlng:
            cli_msg += f" --end-coords {' '.join(str(x) for x in end_latlng)}"
        if location_visited_latlng:
            cli_msg += f" --location-visited-coords {' '.join(str(x) for x in location_visited_latlng)}"
        if segment:
            cli_msg += f" --segment {segment}"
        if distance_range:
            cli_msg += f" --distance-range {' '.join(str(x) for x in distance_range)}"
        if elevation_gain_range:
            cli_msg += f" --elevation-gain-range {' '.join(str(x) for x in elevation_gain_range)}"
        cli_msg += " --no-questions"
        console.print(f"\nYou can re-run this same command with:\n{cli_msg}\n")

    # TODO deleteme
    print(f"start_date_after: {start_date_after} | {type(start_date_after)}")
    print(f"start_date_before: {start_date_before} | {type(start_date_after)}")
    print(f"title_contains: {title_contains} | {type(title_contains)}")
    print(f"activity_type: {activity_type} | {type(activity_type)}")
    print(f"start_latlng: {start_latlng} | {type(start_latlng)}")
    print(f"end_latlng: {end_latlng} | {type(end_latlng)}")
    print(
        f"location_visited_latlng: {location_visited_latlng} | {type(location_visited_latlng)}"
    )
    print(f"segment_id: {segment_id} | {type(segment_id)}")
    print(f"distance_range: {distance_range} | {type(distance_range)}")
    print(
        f"elevation_gain_range: {elevation_gain_range} | {type(elevation_gain_range)}"
    )
    print(f"do_skip_any_question: {do_skip_any_question}")

    searcher = SearchStravaApiCmd(
        start_date_after=start_date_after,
        start_date_before=start_date_before,
        title_contains=title_contains,
        activity_type=activity_type,
        start_latlng=start_latlng,
        end_latlng=end_latlng,
        location_visited_latlng=location_visited_latlng,
        segment_id=segment_id,
        distance_range=distance_range,
        elevation_gain_range=elevation_gain_range,
    )
    searcher.search()

    # Print again how to re-run this command, as the last line printed so easy
    #  to be found.
    if not do_skip_any_question:
        console.print(f"\nYou can re-run this same command with:\n{cli_msg}\n")


def _parse_datetime_input(value):
    try:
        return datetime_utils.parse_datetime_arg(value, is_type_str_allowed=True)
    except datetime_utils.datetime_utils.BaseDatetimeUtilsException as exc:
        msg = "Invalid input, format like 2024-01-01T00:00:00+01:00"
        console.print_error(msg)
        raise ValidationError(msg) from exc


def _parse_activity_type_input(value):
    if value == "*Any":
        return None
    # Note: all types described in https://github.com/puntonim/sport-monorepo/blob/main/libs/strava-db-models/strava_db_models/strava_db_models.py#L106.
    if value.lower() not in (x.lower() for x in ALL_ACTIVITY_TYPES):
        msg = f"Invalid input, valid values: {', '.join(ALL_ACTIVITY_TYPES)}"
        console.print_error(msg)
        raise ValidationError(msg)
    return value


def _click_validate_segment_input(ctx, param, value, is_none_allowed=True):
    """
    Used in Click custom validation for options (callback=...).
    It's a wrapper around _parse_segment_input().
    """
    if value is None and is_none_allowed:
        return None
    try:
        return _parse_segment_input(value, do_not_print=True)
    except ValidationError as exc:
        raise click.BadParameter(exc.args[0]) from exc


def _parse_segment_input(value, do_not_print=False):
    if value.lower() in KNOWN_STRAVA_SEGMENTS:
        return KNOWN_STRAVA_SEGMENTS[value]
    try:
        return int(value)
    except ValueError as exc:
        msg = f"Invalid input, valid values: stelvio | selvino | <int> (eg. 14418673 for https://www.strava.com/segments/14418673"
        if not do_not_print:
            console.print_error(msg)
        raise ValidationError(msg) from exc


def _parse_latlng_input(value):
    data = value.split(" ")
    msg = "Invalid input, format like: 45.745995 9.762249 250"
    if not len(data) == 3:
        console.print_error(msg)
        raise ValidationError(msg)
    try:
        data[0] = float(data[0])
    except ValueError as exc:
        console.print_error(msg)
        raise ValidationError(msg)
    try:
        data[1] = float(data[1])
    except ValueError as exc:
        console.print_error(msg)
        raise ValidationError(msg)
    try:
        data[2] = int(data[2])
    except ValueError as exc:
        console.print_error(msg)
        raise ValidationError(msg)
    return tuple(data)


def _parse_int_range_input(value):
    data = value.split(" ")
    msg = "Invalid input, format like: 800 1500"
    if not len(data) == 2:
        console.print_error(msg)
        raise ValidationError(msg)
    try:
        data[0] = int(data[0])
    except ValueError as exc:
        console.print_error(msg)
        raise ValidationError(msg)
    try:
        data[1] = int(data[1])
    except ValueError as exc:
        console.print_error(msg)
        raise ValidationError(msg)
    return tuple(data)


class BaseFooException(Exception): ...


class ValidationError(BaseFooException): ...
