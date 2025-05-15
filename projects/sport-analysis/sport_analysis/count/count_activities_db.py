from datetime import datetime, timezone

import click
import datetime_utils
import log_utils as logger
import peewee_utils
import strava_db_models

from ..base_cli_view import BaseClickCommand
from ..conf import settings

# Configure peewee_utils with the SQLite DB path.
peewee_utils.configure(sqlite_db_path=settings.DB_PATH)

# Register all default tables, triggers and sql_functions.
strava_db_models.register_default_tables_and_triggers_and_sql_functions()

ACTIVITY_TYPES = (
    "BackcountrySki",
    "Hike",
    "Kayaking",
    "NordicSki",
    "Ride",
    "RockClimbing",
    "Run",
    "Snowboard",
    "Snowshoe",
    "Walk",
    "WeightTraining",
    "Workout",
)


@click.command(
    cls=BaseClickCommand,
    name="db-count",
    help="Count activities in the DB; eg. analysis db-count --start-date-after 2024-01-01T00:00:01+01:00 --start-date-before 2024-12-31T23:59:59+01:00 --activity-type ride",
)
@click.option(
    "--start-date-after",
    type=click.DateTime(formats=["%Y-%m-%dT%H:%M:%S%z"]),
    help="Filter on activity's start date; eg. 2024-01-01T00:00:01+01:00",
)
@click.option(
    "--start-date-before",
    type=click.DateTime(formats=["%Y-%m-%dT%H:%M:%S%z"]),
    help="Filter on activity's start date; eg. 2024-01-01T00:00:01+01:00",
)
@click.option("--activity-type", type=str, help=f"One of: {', '.join(ACTIVITY_TYPES)}")
@peewee_utils.use_db
def count_activities_db_cli_view(
    start_date_after: datetime | str | None = None,
    start_date_before: datetime | str | None = None,
    activity_type: str | None = None,
) -> int:
    return count_activities_db(start_date_after, start_date_before, activity_type)


def count_activities_db(
    start_date_after: datetime | str | None = None,
    start_date_before: datetime | str | None = None,
    activity_type: str | None = None,
) -> int:
    """
    Count activities in the DB, filtering by start date and activity type.

    Args:
        start_date_after: eg. "2024-01-01T00:00:01+01:00" or datetime(2024, 1, 6, 17, 20, tzinfo=ZoneInfo("Europe/Rome")).
        start_date_before: eg. "2024-01-01T00:00:01+01:00" or datetime(2024, 1, 6, 17, 20, tzinfo=ZoneInfo("Europe/Rome")).
        activity_type [str]: one of ACTIVITY_TYPES, case-insensitive; eg. ride.
    """
    # Parse start_date_after.
    if start_date_after:
        if isinstance(start_date_after, str):
            try:
                start_date_after: datetime = datetime_utils.iso_string_to_date(
                    start_date_after
                )
            except ValueError as exc:
                raise InvalidDatetime(start_date_after) from exc

        if isinstance(start_date_after, datetime):
            if datetime_utils.is_naive(start_date_after):
                raise NaiveDatetime(start_date_after)
        else:
            raise InvalidDatetime(start_date_after)
        logger.info(f"Filter: start-date-after = {start_date_after.isoformat()}")

    # Parse start_date_before.
    if start_date_before:
        if isinstance(start_date_before, str):
            try:
                start_date_before: datetime = datetime_utils.iso_string_to_date(
                    start_date_before
                )
            except ValueError as exc:
                raise InvalidDatetime(start_date_before) from exc

        if isinstance(start_date_before, datetime):
            if datetime_utils.is_naive(start_date_before):
                raise NaiveDatetime(start_date_before)
        else:
            raise InvalidDatetime(start_date_before)
        logger.info(f"Filter: start-date-before = {start_date_before.isoformat()}")

    # Parse activity_type.
    if activity_type:
        if activity_type.lower() not in (x.lower() for x in ACTIVITY_TYPES):
            raise UnknownActivityType(activity_type)
        logger.info(f"Filter: activity-type = {start_date_before.isoformat()}")

    query = strava_db_models.Activity.select()
    if start_date_after:
        query = query.where(
            strava_db_models.Activity.start_date
            >= start_date_after.astimezone(timezone.utc)
        )
    if start_date_before:
        query = query.where(
            strava_db_models.Activity.start_date
            <= start_date_before.astimezone(timezone.utc),
        )
    if activity_type:
        # The operator `**` is ILIKE (case-insensitive).
        # NOTE: since we previously check that the given `activity_type` is listed
        #  in ACTIVITY_TYPES, then this works like a case-insens ==.
        query = query.where(strava_db_models.Activity.type**activity_type)

    count = query.count()
    logger.info(f"DB filtered activities #: {count}")
    logger.info(f"DB TOT activities #: {len(strava_db_models.Activity.select())}")
    return count


class BaseCountActivitiesDbException(Exception):
    pass


class InvalidDatetime(BaseCountActivitiesDbException):
    def __init__(self, value):
        self.value = value


class NaiveDatetime(BaseCountActivitiesDbException):
    def __init__(self, value):
        self.value = value


class UnknownActivityType(BaseCountActivitiesDbException):
    def __init__(self, activity_type):
        self.activity_type = activity_type
