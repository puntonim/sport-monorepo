from datetime import datetime, timezone

import click
import datetime_utils
import log_utils as logger
import pandas as pd
import peewee_utils
import strava_db_models

from ..base_cli_view import BaseClickCommand
from ..conf import settings

# Configure peewee_utils with the SQLite DB path.
peewee_utils.configure(sqlite_db_path=settings.DB_PATH)

# Register all default tables, triggers and sql_functions.
strava_db_models.register_default_tables_and_triggers_and_sql_functions()

#
#
#
# TODO this is unfinished code !!!!!!!!!!!!!
#
#
#


def eoy_stats_db(
    start_date_after: datetime | str | None = None,
    start_date_before: datetime | str | None = None,
) -> None:
    # Parse start_date_after.
    start_date_after = datetime_utils.parse_datetime_arg(start_date_after)
    start_date_before = datetime_utils.parse_datetime_arg(start_date_before)
    if start_date_after:
        logger.info(f"Filter: start-date-after = {start_date_after.isoformat()}")
    if start_date_before:
        logger.info(f"Filter: start-date-before = {start_date_before.isoformat()}")

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

    # Convert do Dataframe.
    df = pd.DataFrame(query.dicts())
    df.set_index("id")

    assert len(df) == query.count()
    del query

    logger.info(f"DB filtered activities #: {len(df)}")
    logger.info(f"DB TOT activities #: {strava_db_models.Activity.select().count()}")

    # Types.
    logger.info("\n\nDB TYPES")
    activity_types = []
    for ix, row in df.groupby("type").count().iterrows():
        activity_types.append(row.name)
        logger.info(f"{row.name}: {row.id}")

    # Durations per type.
    logger.info("\n\nDB DURATIONS")
    for activity_type in activity_types:
        x = df[df["type"].str.contains(activity_type, na=False, case=False)]
        mean = datetime_utils.seconds_to_hh_mm_ss(round(x.elapsed_time.mean()))
        min = datetime_utils.seconds_to_hh_mm_ss(round(x.elapsed_time.min()))
        max = datetime_utils.seconds_to_hh_mm_ss(round(x.elapsed_time.max()))
        min_max = f" [min: {min} max:{max}]" if len(x) > 1 else ""
        logger.info(f"{activity_type} #{len(x)}: {mean}{min_max}")

    # TODO this is unfinished code !!!!!!!!!!!!!

    ## Regular run.
    # Distance and time (avg and max).
    # Avg and best pace for a <10km run, and 21km.
    ## Trail run.
    # Distance and time and elevation (avg and max).

    ## Bike
    # Distance and time and elevation (avg and max).

    ## Weighttraining.
    # Duration (avg and max)
    # % biceps, back, cali, etc
