from datetime import datetime, timezone

import peewee_utils

from strava_db_models import Activity


class Test:
    def setup_method(self):
        # Configure peewee_utils with the SQLite DB path.
        peewee_utils.configure(sqlite_db_path=":memory:")

    @peewee_utils.use_db
    def test_happy_flow(self):
        Activity.create(
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
        Activity.create(
            strava_id=124,
            name="My activity2",
            distance=0.0,
            moving_time=60,
            elapsed_time=60,
            total_elevation_gain=0.0,
            type="My type",
            sport_type="My sport type",
            start_date=datetime(2025, 1, 2, tzinfo=timezone.utc),
            start_date_local_str="2025-01-02T17:00:07Z",
            timezone="(GMT+01:00) Europe/Rome",
            utc_offset=3600.0,
            gear_id="My gear id",
        )
        assert Activity.select().count() == 2
