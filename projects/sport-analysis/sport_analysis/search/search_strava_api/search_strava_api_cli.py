from contextlib import suppress
from datetime import datetime

import click
import datetime_utils
import questionary
import speed_utils
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
    EXAMPLES
    \b
    Required args: none, all args are optional filters.
    So to suppress any interactive questions:
      $ san search-strava --no-questions
    \b
    To interactively provide input for all filters:
      $ san search-strava 
    Most popular:
      $ san search-strava --no-questions --activity-type ride
    \b
    $ san search-strava --start-date-after 2024-01-01T00:00:00+01:00 --start-date-before 2024-12-31T23:59:59+01:00
    $ san search-strava --title-contains "back, calisthenics"
    $ san search-strava --activity-type ride
    $ san search-strava --start-coords 45.609045 9.616716 100  # Verdellino.
    $ san search-strava --end-coords 46.428331 10.355555 100  # Hotel Cepina.
    $ san search-strava --location-visited-coords 46.515631 10.314396 100  # Laghi di Cancano.
    $ san search-strava --segment selvino --activity-type ride
    $ san search-strava --distance-range 30000 150000 --activity-type ride
    $ san search-strava --moving-time-range 60 120 --activity-type run
    $ san search-strava --elapsed-time-range 60 120 --activity-type run
    $ san search-strava --elevation-gain-range 1500 9000 --activity-type ride
    $ san search-strava --elevation-highest-range 2000 9000 --activity-type ride
    $ san search-strava --elevation-lowest-range 1000 9000 --activity-type ride
    $ san search-strava --speed-avg-range 14.2 20.0 --activity-type ride
    $ san search-strava --speed-max-range 60.0 150.0 --activity-type ride
    $ san search-strava --pace-avg-range 4:30 4:45 --activity-type run
    $ san search-strava --pace-max-range 2:00 2:30 --activity-type run
    $ san search-strava --hr-avg-range 110 180 --with-hr-band-only
    $ san search-strava --hr-max-range 160 220 --with-hr-band-only
    \b
    To debug args:
      $ san search-strava --activity-type ride --debug-args
    """,
)
@click.option(
    # OPTIONAL arg.
    "--start-date-after",
    type=click.DateTime(formats=["%Y-%m-%dT%H:%M:%S%z"]),
    help="Optional filter by start date after; eg. --start-date-after 2024-01-01T00:00:00+01:00",
)
@click.option(
    # OPTIONAL arg.
    "--start-date-before",
    type=click.DateTime(formats=["%Y-%m-%dT%H:%M:%S%z"]),
    help="Optional filter by start date before; eg. --start-date-before 2024-12-31T23:59:59+01:00",
)
@click.option(
    # OPTIONAL arg.
    "--title-contains",
    type=str,
    help="Optional filter by title's substring; eg. --title-contains 'back, calisthenics'",
)
@click.option(
    # OPTIONAL arg.
    # Note: all types described in https://github.com/puntonim/sport-monorepo/blob/main/libs/strava-db-models/strava_db_models/strava_db_models.py#L106.
    "--activity-type",
    type=click.Choice(ALL_ACTIVITY_TYPES, case_sensitive=False),
    help="Optional filter by activity type; eg. --activity-type ride | --activity-type mountainbikeride | --activity-type weighttraining (full list: https://github.com/puntonim/sport-monorepo/blob/main/libs/strava-db-models/strava_db_models/strava_db_models.py#L106)",
)
@click.option(
    # OPTIONAL arg.
    "--start-coords",
    "start_latlng",
    nargs=3,
    type=click.Tuple([float, float, int]),
    help="Optional filter by starting location as lat-float lon-float distance-meters-int; eg. --start-coords 45.745995 9.762249 250",
)
@click.option(
    # OPTIONAL arg.
    "--end-coords",
    "end_latlng",
    nargs=3,
    type=click.Tuple([float, float, int]),
    help="Optional filter by ending location as lat-float lon-float distance-meters-int; eg. --end-coords 45.745995 9.762249 250",
)
@click.option(
    # OPTIONAL arg.
    "--location-visited-coords",
    "location_visited_latlng",
    nargs=3,
    type=click.Tuple([float, float, int]),
    help="Optional filter by visited location as lat-float lon-float distance-meters-int; eg. --location-visited-coords 45.745995 9.762249 250",
)
@click.option(
    # OPTIONAL arg.
    "--segment",
    type=str,
    callback=lambda *args, **kwargs: _click_validate_segment_input(*args, **kwargs),
    help="Optional filter by Strava segment; eg. --segment selvino | --segment stelvio | --segment 15756100 (from https://www.strava.com/segments/15756100)",
)
@click.option(
    # OPTIONAL arg.
    "--distance-range",
    nargs=2,
    type=click.Tuple([int, int]),
    help="Optional filter by distance range as min-meters-int max-meters-int; eg. --distance-range 9500 10500",
)
@click.option(
    # OPTIONAL arg.
    "--moving-time-range",
    nargs=2,
    type=click.Tuple([int, int]),
    help="Optional filter by moving time range as min-minutes-int max-minutes-int; eg. --moving-time-range 60 120",
)
@click.option(
    # OPTIONAL arg.
    "--elapsed-time-range",
    nargs=2,
    type=click.Tuple([int, int]),
    help="Optional filter by elapsed time range as min-minutes-int max-minutes-int; eg. -elapsed-time-range 60 120",
)
@click.option(
    # OPTIONAL arg.
    "--elevation-gain-range",
    nargs=2,
    type=click.Tuple([int, int]),
    help="Optional filter by elevation gain range as min-meters-int max-meters-int; eg. --elevation-gain-range 800 1500",
)
@click.option(
    # OPTIONAL arg.
    "--elevation-highest-range",
    nargs=2,
    type=click.Tuple([int, int]),
    help="Optional filter by highest elevation visited range as min-meters-int max-meters-int; eg. -elevation-highest-range 800 1500",
)
@click.option(
    # OPTIONAL arg.
    "--elevation-lowest-range",
    nargs=2,
    type=click.Tuple([int, int]),
    help="Optional filter by lowest elevation visited range as min-meters-int max-meters-int; eg. --elevation-lowest-range 800 1500",
)
@click.option(
    # OPTIONAL arg.
    "--speed-avg-range",
    nargs=2,
    type=click.Tuple([float, float]),
    help="Optional filter by average speed range in km/h as min-kmph-float max-kmph-float; eg. --speed-avg-range 14.2 20.0",
)
@click.option(
    # OPTIONAL arg.
    "--speed-max-range",
    nargs=2,
    type=click.Tuple([float, float]),
    help="Optional filter by max speed range in km/h as min-kmph-float max-kmph-float; eg. --speed-max-range 14.2 20.0",
)
@click.option(
    # OPTIONAL arg.
    "--pace-avg-range",
    nargs=2,
    type=click.Tuple([str, str]),
    callback=lambda *args, **kwargs: _click_validate_pace_range_input(*args, **kwargs),
    help="Optional filter by average pace range in min/km as min-minpkm-str max-minpkm-str; eg. --pace-avg-range 5:30 5:45",
)
@click.option(
    # OPTIONAL arg.
    "--pace-max-range",
    nargs=2,
    type=click.Tuple([str, str]),
    callback=lambda *args, **kwargs: _click_validate_pace_range_input(*args, **kwargs),
    help="Optional filter by max pace range in min/km as min-minpkm-str max-minpkm-str; eg. --pace-max-range 5:30 5:45",
)
@click.option(
    # OPTIONAL arg.
    "--hr-avg-range",
    nargs=2,
    type=click.Tuple([int, int]),
    help="Optional filter by average heart rate range as min-bpm-int max-bpm-int; eg. --hr-avg-range 110 160",
)
@click.option(
    # OPTIONAL arg.
    "--hr-max-range",
    nargs=2,
    type=click.Tuple([int, int]),
    help="Optional filter by average heart rate range as min-bpm-int max-bpm-int; eg. --hr-max-range 110 160",
)
@click.option(
    # OPTIONAL arg.
    "--with-hr-band-only",
    "do_select_only_if_with_hr_band",
    is_flag=True,
    default=False,
    help="Optional filter to select only activities with heart rate band monitor",
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
    moving_time_range: tuple[int, int] | None = None,
    elapsed_time_range: tuple[int, int] | None = None,
    elevation_gain_range: tuple[int, int] | None = None,
    elevation_highest_range: tuple[int, int] | None = None,
    elevation_lowest_range: tuple[int, int] | None = None,
    speed_avg_range: tuple[float, float] | None = None,
    speed_max_range: tuple[float, float] | None = None,
    pace_avg_range: tuple[str, str] | None = None,
    pace_max_range: tuple[str, str] | None = None,
    hr_avg_range: tuple[int, int] | None = None,
    hr_max_range: tuple[int, int] | None = None,
    do_select_only_if_with_hr_band: bool = False,
    do_skip_any_questions: bool = False,
    do_debug_args: bool = False,
) -> None:
    ## Prompt for all args that were not provided in the CLI.
    # Optional arg: start_date_after.
    is_input_valid = True if start_date_after is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by START DATE AFTER (eg. 2024-01-01T00:00:00+01:00)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            start_date_after = _parse_datetime_input(x)
            is_input_valid = True

    # Optional arg: start_date_before.
    is_input_valid = True if start_date_before is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by START DATE BEFORE (eg. 2024-12-31T23:59:59+01:00)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                start_date_before = _parse_datetime_input(x)
            is_input_valid = True

    # Optional arg: title_contains.
    if title_contains is None and not do_skip_any_questions:
        text = "Optional filter by TITLE'S SUBSTRING (eg. back, calisthenics)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        title_contains = questionary.text(text).unsafe_ask() or None

    # Optional arg: activity_type.
    is_input_valid = True if activity_type is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by ACTIVITY TYPE"
        x = (
            # unsafe_ask() so it can be stopped with ctrl-c.
            # Cannot use `validate=<questionary.Validator subclass>` because that is for
            #  the live validation, it's run on every keystroke and returns None.
            questionary.select(text, choices=("*Any", *ALL_ACTIVITY_TYPES)).unsafe_ask()
            or None
        )
        with suppress(ValidationError):
            if x is not None:
                activity_type = _parse_activity_type_input(x)
            is_input_valid = True

    # Optional arg: start_latlng.
    is_input_valid = True if start_latlng is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by STARTING LOCATION as lat-float lon-float distance-meters-int (eg. 45.745995 9.762249 250)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                start_latlng = _parse_latlng_input(x)
            is_input_valid = True

    # Optional arg: end_latlng.
    is_input_valid = True if end_latlng is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by ENDING LOCATION as lat-float lon-float distance-meters-int (eg. 45.745995 9.762249 250)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                end_latlng = _parse_latlng_input(x)
            is_input_valid = True

    # Optional arg: location_visited_latlng.
    is_input_valid = True if location_visited_latlng is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by LOCATION VISITED as lat-float lon-float distance-meters-int (eg. 45.745995 9.762249 250)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                location_visited_latlng = _parse_latlng_input(x)
            is_input_valid = True

    # Optional arg: segment.
    is_input_valid = False
    segment_id = None
    if segment is not None:
        is_input_valid = True
        segment_id = segment
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by Strava SEGMENT (eg. selvino | stelvio | 15756100 (from https://www.strava.com/segments/15756100))"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        segment = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if segment is not None:
                segment_id = _parse_segment_input(segment)
            is_input_valid = True

    # Optional arg: distance_range.
    is_input_valid = True if distance_range is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by DISTANCE RANGE as min-meters-int max-meters-int (eg. 9500 10500)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                distance_range = _parse_int_range_input(x, format_like="9500 10500")
            is_input_valid = True

    # Optional arg: moving_time_range.
    is_input_valid = True if moving_time_range is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by MOVING TIME RANGE as min-minutes-int max-minutes-int (eg. 60 120)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                moving_time_range = _parse_int_range_input(x, format_like="60 120")
            is_input_valid = True

    # Optional arg: elapsed_time_range.
    is_input_valid = True if elapsed_time_range is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by ELAPSED TIME RANGE as min-minutes-int max-minutes-int (eg. 60 120)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                elapsed_time_range = _parse_int_range_input(x, format_like="60 120")
            is_input_valid = True

    # Optional arg: elevation_gain_range.
    is_input_valid = True if elevation_gain_range is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by ELEVATION GAIN RANGE as min-meters-int max-meters-int (eg. 800 1500)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                elevation_gain_range = _parse_int_range_input(x, format_like="800 1500")
            is_input_valid = True

    # Optional arg: elevation_highest_range.
    is_input_valid = True if elevation_highest_range is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by ELEVATION HIGHEST RANGE as min-meters-int max-meters-int (eg. 800 1500)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                elevation_highest_range = _parse_int_range_input(
                    x, format_like="800 1500"
                )
            is_input_valid = True

    # Optional arg: elevation_lowest_range.
    is_input_valid = True if elevation_lowest_range is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by ELEVATION LOWEST RANGE as min-meters-int max-meters-int (eg. 800 1500)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                elevation_lowest_range = _parse_int_range_input(
                    x, format_like="800 1500"
                )
            is_input_valid = True

    # Optional arg: speed_avg_range.
    is_input_valid = True if speed_avg_range is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by AVERAGE SPEED RANGE in km/h as min-kmph-float max-kmph-float (eg. 14.2 20.0)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                speed_avg_range = _parse_float_range_input(x, format_like="14.2 20.0")
            is_input_valid = True

    # Optional arg: speed_max_range.
    is_input_valid = True if speed_max_range is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by MAX SPEED RANGE in km/h as min-kmph-float max-kmph-float (eg. 14.2 20.0)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                speed_max_range = _parse_float_range_input(x, format_like="14.2 20.0")
            is_input_valid = True

    # Optional arg: pace_avg_range.
    is_input_valid = True if pace_avg_range is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by AVERAGE PACE RANGE in min/km as min-minpkm-str max-minpkm-str (eg. 5:30 5:45)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                pace_avg_range = _parse_pace_range_input(x)
            is_input_valid = True

    # Optional arg: pace_max_range.
    is_input_valid = True if pace_max_range is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by MAX PACE RANGE in min/km as min-minpkm-str max-minpkm-str (eg. 5:30 5:45)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                pace_max_range = _parse_pace_range_input(x)
            is_input_valid = True

    # Optional arg: hr_avg_range.
    is_input_valid = True if hr_avg_range is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by AVERAGE HEART RATE RANGE as min-bpm-int max-bpm-int (eg. 110 160)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                hr_avg_range = _parse_int_range_input(x, format_like="110 160")
            is_input_valid = True

    # Optional arg: hr_max_range.
    is_input_valid = True if hr_max_range is not None else False
    while not is_input_valid and not do_skip_any_questions:
        text = "Optional filter by MAX HEART RATE RANGE as min-bpm-int max-bpm-int (eg. 110 160)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            if x is not None:
                hr_max_range = _parse_int_range_input(x, format_like="110 160")
            is_input_valid = True

    # Optional arg: do_select_only_if_with_hr_band.
    if not do_select_only_if_with_hr_band and not do_skip_any_questions:
        text = "Optional filter to select only activities with HEART REATE BAND monitor"
        # unsafe_ask() so it can be stopped with ctrl-c.
        # Cannot use `validate=<questionary.Validator subclass>` because that is for
        #  the live validation, it's run on every keystroke and returns None.
        x = questionary.confirm(text, default=False).unsafe_ask() or None
        do_select_only_if_with_hr_band = bool(x)

    # Print how to re-run this command.
    if not do_skip_any_questions:
        cli_msg = "$ san search-strava"
        if start_date_after:
            cli_msg += f" --start-date-after {start_date_after.isoformat()}"
        if start_date_before:
            cli_msg += f" --start-date-before {start_date_before.isoformat()}"
        if title_contains:
            cli_msg += f" --title-contains '{title_contains}'"
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
        if moving_time_range:
            cli_msg += (
                f" --moving-time-range {' '.join(str(x) for x in moving_time_range)}"
            )
        if elapsed_time_range:
            cli_msg += (
                f" --elapsed-time-range {' '.join(str(x) for x in elapsed_time_range)}"
            )
        if elevation_gain_range:
            cli_msg += f" --elevation-gain-range {' '.join(str(x) for x in elevation_gain_range)}"
        if elevation_highest_range:
            cli_msg += f" --elevation-highest-range {' '.join(str(x) for x in elevation_highest_range)}"
        if elevation_lowest_range:
            cli_msg += f" --elevation-lowest-range {' '.join(str(x) for x in elevation_lowest_range)}"
        if speed_avg_range:
            cli_msg += f" --speed-avg-range {' '.join(str(x) for x in speed_avg_range)}"
        if speed_max_range:
            cli_msg += f" --speed-max-range {' '.join(str(x) for x in speed_max_range)}"
        if pace_avg_range:
            cli_msg += f" --pace-avg-range {' '.join(str(x) for x in pace_avg_range)}"
        if pace_max_range:
            cli_msg += f" --pace-max-range {' '.join(str(x) for x in pace_max_range)}"
        if hr_avg_range:
            cli_msg += f" --hr-avg-range {' '.join(str(x) for x in hr_avg_range)}"
        if hr_max_range:
            cli_msg += f" --hr-max-range {' '.join(str(x) for x in hr_max_range)}"
        if do_select_only_if_with_hr_band:
            cli_msg += f" --with-hr-band-only"
        cli_msg += " --no-questions"
        console.print(f"\nYou can re-run this same command with:\n{cli_msg}\n")

    # If do_debug_args then print all the provided args.
    if do_debug_args:
        for arg in (
            "start_date_after",
            "start_date_before",
            "title_contains",
            "activity_type",
            "start_latlng",
            "end_latlng",
            "location_visited_latlng",
            "segment_id",
            "distance_range",
            "moving_time_range",
            "elapsed_time_range",
            "elevation_gain_range",
            "elevation_highest_range",
            "elevation_lowest_range",
            "speed_avg_range",
            "speed_max_range",
            "pace_avg_range",
            "pace_max_range",
            "hr_avg_range",
            "hr_max_range",
            "do_skip_any_questions",
            "do_select_only_if_with_hr_band",
            "do_debug_args",
        ):
            console.print(f"{arg}: {locals()[arg]} | {type(locals()[arg])}")

    if do_select_only_if_with_hr_band:
        console.log(
            "[italic]We will use Garmin API to check if the HR band was used[/italic]"
        )

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
        moving_time_range=moving_time_range,
        elapsed_time_range=elapsed_time_range,
        elevation_gain_range=elevation_gain_range,
        elevation_highest_range=elevation_highest_range,
        elevation_lowest_range=elevation_lowest_range,
        speed_avg_range=speed_avg_range,
        speed_max_range=speed_max_range,
        pace_avg_range=pace_avg_range,
        pace_max_range=pace_max_range,
        hr_avg_range=hr_avg_range,
        hr_max_range=hr_max_range,
        do_select_only_if_with_hr_band=do_select_only_if_with_hr_band,
    )
    searcher.search()

    # Print again how to re-run this command, as the last line printed so easy
    #  to be found.
    if not do_skip_any_questions:
        console.print(f"\nYou can re-run this same command with:\n{cli_msg}\n")


def _parse_datetime_input(value: str):
    try:
        return datetime_utils.parse_datetime_arg(value, is_type_str_allowed=True)
    except datetime_utils.datetime_utils.BaseDatetimeUtilsException as exc:
        msg = "Invalid input, format like 2024-01-01T00:00:00+01:00"
        console.print_error(msg)
        raise ValidationError(msg) from exc


def _parse_activity_type_input(value: str):
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


def _parse_segment_input(value: str, do_not_print=False):
    if value.lower() in KNOWN_STRAVA_SEGMENTS:
        return KNOWN_STRAVA_SEGMENTS[value]
    try:
        return int(value)
    except ValueError as exc:
        msg = f"Invalid input, valid values: stelvio | selvino | <int> (eg. 14418673 for https://www.strava.com/segments/14418673"
        if not do_not_print:
            console.print_error(msg)
        raise ValidationError(msg) from exc


def _parse_latlng_input(value: str):
    data = value.split(" ")
    msg = "Invalid input, format like: 45.745995 9.762249 250"
    if not len(data) == 3:
        console.print_error(msg)
        raise ValidationError(msg)
    try:
        data[0] = float(data[0])
    except ValueError as exc:
        console.print_error(msg)
        raise ValidationError(msg) from exc
    try:
        data[1] = float(data[1])
    except ValueError as exc:
        console.print_error(msg)
        raise ValidationError(msg) from exc
    try:
        data[2] = int(data[2])
    except ValueError as exc:
        console.print_error(msg)
        raise ValidationError(msg) from exc
    return tuple(data)


def _parse_int_range_input(value: str, format_like="800 1200"):
    data = value.split(" ")
    msg = f"Invalid input, format like: {format_like}"
    if not len(data) == 2:
        console.print_error(msg)
        raise ValidationError(msg)
    try:
        data[0] = int(data[0])
    except ValueError as exc:
        console.print_error(msg)
        raise ValidationError(msg) from exc
    try:
        data[1] = int(data[1])
    except ValueError as exc:
        console.print_error(msg)
        raise ValidationError(msg) from exc
    return tuple(data)


def _parse_float_range_input(value: str, format_like="10.5 20.0"):
    data = value.split(" ")
    msg = f"Invalid input, format like: {format_like}"
    if not len(data) == 2:
        console.print_error(msg)
        raise ValidationError(msg)
    try:
        data[0] = float(data[0])
    except ValueError as exc:
        console.print_error(msg)
        raise ValidationError(msg) from exc
    try:
        data[1] = float(data[1])
    except ValueError as exc:
        console.print_error(msg)
        raise ValidationError(msg) from exc
    return tuple(data)


def _click_validate_pace_range_input(ctx, param, value, is_none_allowed=True):
    """
    Used in Click custom validation for options (callback=...).
    It's a wrapper around _parse_pace_range_input().
    """
    if value is None and is_none_allowed:
        return None
    try:
        return _parse_pace_range_input(" ".join(value), do_not_print=True)
    except ValidationError as exc:
        raise click.BadParameter(exc.args[0]) from exc


def _parse_pace_range_input(value: str, do_not_print=False):
    data = value.split(" ")
    msg = "Invalid input, format like: 5:30 5:45"
    if not len(data) == 2:
        if not do_not_print:
            console.print_error(msg)
        raise ValidationError(msg)
    try:
        speed_utils.minpkm_base60_to_base10(data[0])
        speed_utils.minpkm_base60_to_base10(data[1])
    except ValueError as exc:
        if not do_not_print:
            console.print_error(msg)
        raise ValidationError(msg) from exc
    return tuple(data)


class BaseSearchStravaApiCliException(Exception): ...


class ValidationError(BaseSearchStravaApiCliException): ...
