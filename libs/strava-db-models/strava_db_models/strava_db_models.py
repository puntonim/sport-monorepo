"""
** STRAVA MONOREPO: STRAVA DB MODELS **
=======================================

```py
import peewee_utils
from strava_db_models import Activity

# Configure peewee_utils with the SQLite DB path.
peewee_utils.configure(sqlite_db_path=":memory:")

activity = Activity.create(
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
assert Activity.select().count() == 2
```
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import peewee
import peewee_utils
from playhouse.sqlite_ext import JSONField

__all__ = [
    "RawActivitySummary",
    "Activity",
]


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


class RawActivitySummary(peewee_utils.BasePeeweeModel):
    """
    The activity summary as received from Strava API list_activities().
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
    raw_summary: dict = JSONField()
    strava_id: int = peewee.IntegerField(unique=True)
    md5_checksum: str = peewee.CharField(max_length=512)

    def __repr__(self) -> str:
        return f"RawActivitySummary(id={self.id!r}, strava_id={self.strava_id!r})"

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

    def extract_local_start_date(self) -> datetime:
        return self.start_date.astimezone(ZoneInfo(self.timezone.split(" ")[1]))

    def __repr__(self) -> str:
        return f"Activity(id={self.id!r}, strava_id={self.strava_id!r}, name={self.name!r})"

    def __str__(self) -> str:
        return self.__repr__()


# Register all tables.
peewee_utils.register_tables(RawActivitySummary, Activity)

# Add a custom SQL function that serves as feature toggle for the updated_at triggers.
#  It returns 1 (True) always and it's invoked by every updated_at trigger.
#  We can overwrite this function to return 0 in order to temp disable triggers.
#  See tests/testfactories/domains/exercise_domain_factory.py.
UPDATED_AT_TRIGGERS_TOGGLE_FUNCTION_NAME = "are_updated_at_triggers_enabled"
peewee_utils.register_sql_function(
    lambda: 1,
    UPDATED_AT_TRIGGERS_TOGGLE_FUNCTION_NAME,
    0,
)

# Register a trigger to update Activity.updated_at on every update.
# Update trigger: https://stackoverflow.com/questions/30780722/sqlite-and-recursive-triggers
# STRFTIME for timestamp with milliseconds: https://stackoverflow.com/questions/17574784/sqlite-current-timestamp-with-milliseconds
peewee_utils.register_trigger(
    """
CREATE TRIGGER IF NOT EXISTS update_activity_updated_at_after_update_on_activity
AFTER UPDATE ON activity
FOR EACH ROW
WHEN (SELECT are_updated_at_triggers_enabled()) = 1
BEGIN
    UPDATE activity
    SET updated_at = STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW');
END;
"""
)

# Register a trigger to update RawActivitySummary.updated_at on every update.
# Update trigger: https://stackoverflow.com/questions/30780722/sqlite-and-recursive-triggers
# STRFTIME for timestamp with milliseconds: https://stackoverflow.com/questions/17574784/sqlite-current-timestamp-with-milliseconds
peewee_utils.register_trigger(
    """
CREATE TRIGGER IF NOT EXISTS update_raw_activity_summary_updated_at_after_update_on_raw_activity_summary
AFTER UPDATE ON raw_activity_summary
FOR EACH ROW
WHEN (SELECT are_updated_at_triggers_enabled()) = 1
BEGIN
    UPDATE raw_activity_summary
    SET updated_at = STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW');
END;
"""
)
