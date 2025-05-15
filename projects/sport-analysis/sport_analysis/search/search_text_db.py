from collections.abc import Generator

import click
import log_utils as logger
import peewee_utils
import strava_db_models

from ..base_cli_view import BaseClickCommand
from ..conf import settings

# Configure peewee_utils with the SQLite DB path.
peewee_utils.configure(sqlite_db_path=settings.DB_PATH)

# Register all default tables, triggers and sql_functions.
strava_db_models.register_default_tables_and_triggers_and_sql_functions()


@click.command(
    cls=BaseClickCommand,
    name="db-search-text",
    help="Search for text in activities' titles and description in the DB; eg. analysis db-search-text 'del mortirolo'",
)
@click.argument("text", nargs=1, type=str)
@peewee_utils.use_db
def search_text_db_cli_view(text: str):
    for activity in search_text_db(text):
        activity: strava_db_models.Activity
        logger.info(f"https://www.strava.com/activities/{activity.strava_id}")


def search_text_db(text: str) -> Generator[strava_db_models.Activity]:
    for activity in strava_db_models.Activity.select().iterator():
        if (
            activity.description
            and text.lower() in activity.description.lower()
            or text.lower() in activity.name.lower()
        ):
            # print(f"Name: {activity.name}")
            # print(f"Type: {activity.type}")
            # print(f"Strava id: {activity.strava_id}")
            # print(f"Start date: {activity.start_date}")
            # print(f"Local start date: {activity.extract_local_start_date()}")
            # print(f"Descr: {activity.description}")
            # print(f"HR max: {activity.heartrate_max}")
            # print(f"HR avg: {activity.heartrate_avg}")
            # print(f"Moving time: {activity.moving_time}")
            # print("==============================\n")
            yield activity
