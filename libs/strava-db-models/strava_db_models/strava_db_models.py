"""
** SPORT MONOREPO: STRAVA DB MODELS **
=======================================

Used, at the moment, by:
 - strava-exporter-to-db in sport-monorepo

Basic use
---------
```py
import peewee_utils
import strava_db_models

# Configure peewee_utils with the SQLite DB path.
peewee_utils.configure(sqlite_db_path=":memory:")

# Register all default tables, triggers and sql_functions.
strava_db_models.register_default_tables_and_triggers_and_sql_functions()

@peewee_utils.use_db
def create_activity():
    activity = strava_db_models.Activity.create(
        strava_id=123,
        name="My activity",
        distance=0.0,
        moving_time=60,
        elapsed_time=60,
        total_elevation_gain=0.0,
        type="My type",
        sport_type="My sport type",
        start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        start_date_local_str="2025-01-01T17:00:07Z",
        timezone="(GMT+01:00) Europe/Rome",
        utc_offset=3600.0,
        gear_id="My gear id",
    )
    assert strava_db_models.Activity.select().count() == 2
```

Extend models
-------------
You can extend models with inheritance:
```py
class Activity(strava_db_models.Activity):
    foo: str = peewee.CharField(max_length=512, null=True)

# Configure peewee_utils with the SQLite DB path.
peewee_utils.configure(sqlite_db_path=":memory:")

# Register the *new* table and the default ones.
peewee_utils.register_tables(Activity, strava_db_models.RawActivitySummary, strava_db_models.RawActivityDetails)

# Register the default triggers and sql functions.
for trigger in strava_db_models.triggers:
    peewee_utils.register_trigger(trigger)
for sql_function in strava_db_models.sql_functions:
    peewee_utils.register_sql_function(**sql_function)
```

Tests
-----
For tests, just use this fixture in conftest.py (see example in tests/conftest.py):
```py
@pytest.fixture(autouse=True, scope="function")
def create_db_fixture(test_settings_fixture, monkeypatch, request):
    # Note that the signature includes `test_settings_fixture` because we need that
    #  fixture to be executed before this one.

    # Configure peewee_utils with the SQLite DB path.
    peewee_utils.configure(sqlite_db_path=":memory:")

    # Register all default tables, triggers and sql_functions.
    strava_db_models.register_default_tables_and_triggers_and_sql_functions()

    # To achieve tests isolation we create a new (in-memory) database (invoking db_init()
    #  a new time) for every test method, and then we create all tables.
    peewee_utils._db_init()
    peewee_utils.create_all_tables()
    yield
    if not peewee_utils.db.is_closed():
        peewee_utils.db.close()
```
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import peewee
import peewee_utils
from playhouse.sqlite_ext import JSONField

__all__ = [
    "RawActivitySummary",
    "RawActivityDetails",
    "Activity",
    "sql_functions",
    "triggers",
    "register_default_tables_and_triggers_and_sql_functions",
]


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


class RawActivitySummary(peewee_utils.BasePeeweeModel):
    """
    The activity summary as received from Strava API list_activities().
    See API specs in "docs/activity summary.md".
    """

    # The `id` would be implicitly added even of we comment this line, as we did
    #  not specify a primary key.
    id: int = peewee.AutoField()
    created_at: datetime = peewee_utils.UtcDateTimeField(default=_now_utc)
    # See trigger `update_raw_activity_summary_updated_at_after_update_on_raw_activity_summary`
    #  defined later.
    # Mind that you have to reload the model to get a fresh value for `updated_at`.
    updated_at: datetime = peewee_utils.UtcDateTimeField(default=_now_utc)

    # Summary data.
    # See API specs in "docs/activity summary.md".
    raw_summary: dict = JSONField()
    strava_id: int = peewee.IntegerField(unique=True)
    md5_checksum: str = peewee.CharField(max_length=512)

    def __repr__(self) -> str:
        return f"RawActivitySummary(id={self.id!r}, strava_id={self.strava_id!r})"

    def __str__(self) -> str:
        return self.__repr__()


class RawActivityDetails(peewee_utils.BasePeeweeModel):
    """
    The activity details as received from Strava API get_activity_details().
    See API specs in "docs/activity details.md".
    """

    # The `id` would be implicitly added even of we comment this line, as we did
    #  not specify a primary key.
    id: int = peewee.AutoField()
    created_at: datetime = peewee_utils.UtcDateTimeField(default=_now_utc)
    # See trigger `update_raw_activity_summary_updated_at_after_update_on_raw_activity_summary`
    #  defined later.
    # Mind that you have to reload the model to get a fresh value for `updated_at`.
    updated_at: datetime = peewee_utils.UtcDateTimeField(default=_now_utc)

    # Summary data.
    # See API specs in "docs/activity details.md".
    raw_details: dict = JSONField()
    strava_id: int = peewee.IntegerField(unique=True)
    md5_checksum: str = peewee.CharField(max_length=512)

    def __repr__(self) -> str:
        return f"RawActivityDetails(id={self.id!r}, strava_id={self.strava_id!r})"

    def __str__(self) -> str:
        return self.__repr__()


class Activity(peewee_utils.BasePeeweeModel):
    """
    The main activity model created after processing the data received from Strava.
    """

    # The `id` would be implicitly added even of we comment this line, as we did
    #  not specify a primary key.
    id: int = peewee.AutoField()
    created_at: datetime = peewee_utils.UtcDateTimeField(default=_now_utc)
    # See trigger `update_activity_updated_at_after_update_on_activity` defined later.
    # Mind that you have to reload the model to get a fresh value for `updated_at`.
    updated_at: datetime = peewee_utils.UtcDateTimeField(default=_now_utc)

    # Data extracted from RawActivitySummary.
    # They are all filled at model creation, so they don't have null = True (unless
    #  they can actually be null in the API).
    strava_id: int = peewee.IntegerField(unique=True)
    name: str = peewee.CharField(max_length=512)
    distance: float = peewee.FloatField()
    moving_time: int = peewee.IntegerField()
    elapsed_time: int = peewee.IntegerField()
    total_elevation_gain: float = peewee.FloatField()
    type: str = peewee.CharField(max_length=64)
    sport_type: str = peewee.CharField(max_length=64)
    # Eg: "2025-01-18T16:00:07Z"
    start_date: datetime = peewee_utils.UtcDateTimeField()
    # Eg: "2025-01-18T17:00:07Z"
    start_date_local_str: str = peewee.CharField(max_length=64)
    # Eg: "(GMT+01:00) Europe/Rome"
    timezone: str = peewee.CharField(max_length=64)
    # Eg: 3600.0
    utc_offset: float = peewee.FloatField()
    ## Useless cause always null.
    # location_city: str | None = peewee.CharField(max_length=64, null=True)
    ## Useless cause always null.
    # location_state: str | None = peewee.CharField(max_length=64, null=True)
    ## Useless cause always "Italy".
    # location_country: str | None = peewee.CharField(max_length=64, null=True)
    gear_id: str | None = peewee.CharField(max_length=64, null=True)
    # Eg. 125.3.
    heartrate_avg: float = peewee.FloatField(null=True)
    # Eg. 137.0.
    heartrate_max: float = peewee.FloatField(null=True)

    # Data extracted from RawActivityDetails.
    # They are filled at a later time (not at creation time) with an update query, so
    #  they all must have null = True.
    description: str | None = peewee.TextField(null=True)
    gear_name: str | None = peewee.CharField(max_length=64, null=True)
    gear_distance: int | None = peewee.IntegerField(null=True)

    def extract_local_start_date(self) -> datetime:
        return self.start_date.astimezone(ZoneInfo(self.timezone.split(" ")[1]))

    def __repr__(self) -> str:
        return f"Activity(id={self.id!r}, strava_id={self.strava_id!r}, name={self.name!r})"

    def __str__(self) -> str:
        return self.__repr__()


# Add a custom SQL function that serves as feature toggle for the updated_at triggers.
#  It returns 1 (True) always and it's invoked by every updated_at trigger.
#  We can overwrite this function to return 0 in order to temp disable triggers.
#  See tests/testfactories/domains/exercise_domain_factory.py.
UPDATED_AT_TRIGGERS_TOGGLE_FUNCTION_NAME = "are_updated_at_triggers_enabled"
sql_functions = [
    # Custom SQL function that serves as feature toggle for the updated_at triggers.
    #  It returns 1 (True) always and it's invoked by every updated_at trigger.
    #  We can overwrite this function to return 0 in order to temp disable triggers.
    #  See gymiq/tests/testfactories/domains/exercise_domain_factory.py.
    dict(
        fn=lambda: 1,
        name=UPDATED_AT_TRIGGERS_TOGGLE_FUNCTION_NAME,
        num_params=0,
    ),
]

triggers = [
    # Trigger to update Activity.updated_at on every update.
    # Update trigger: https://stackoverflow.com/questions/30780722/sqlite-and-recursive-triggers
    # STRFTIME for timestamp with milliseconds: https://stackoverflow.com/questions/17574784/sqlite-current-timestamp-with-milliseconds
    """
CREATE TRIGGER IF NOT EXISTS update_activity_updated_at_after_update_on_activity
AFTER UPDATE ON activity
FOR EACH ROW
WHEN (SELECT are_updated_at_triggers_enabled()) = 1
BEGIN
    UPDATE activity
    SET updated_at = STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW');
END;
""",
    # Trigger to update RawActivitySummary.updated_at on every update.
    # Update trigger: https://stackoverflow.com/questions/30780722/sqlite-and-recursive-triggers
    # STRFTIME for timestamp with milliseconds: https://stackoverflow.com/questions/17574784/sqlite-current-timestamp-with-milliseconds
    """
CREATE TRIGGER IF NOT EXISTS update_raw_activity_summary_updated_at_after_update_on_raw_activity_summary
AFTER UPDATE ON raw_activity_summary
FOR EACH ROW
WHEN (SELECT are_updated_at_triggers_enabled()) = 1
BEGIN
    UPDATE raw_activity_summary
    SET updated_at = STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW');
END;
""",
]


def register_default_tables_and_triggers_and_sql_functions():
    """
    Register all tables, triggers and sql functions defined here.
    """
    peewee_utils.register_tables(RawActivitySummary, RawActivityDetails, Activity)
    for trigger in triggers:
        peewee_utils.register_trigger(trigger)
    for sql_function in sql_functions:
        peewee_utils.register_sql_function(
            fn=sql_function["fn"],
            name=sql_function["name"],
            num_params=sql_function["num_params"],
        )
