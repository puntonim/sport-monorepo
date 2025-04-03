from datetime import datetime, timezone

from strava_db_models import Activity


class Test:
    # Note: the DB magic is done in conftest::create_db_fixture

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
            heartrate_avg=123.3,
            heartrate_max=139.9,
            description="My description",
            gear_name="My gear name",
            gear_distance=99999,
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
            # heartrate_avg=123.3,
            # heartrate_max=139.9,
            description="My description",
            gear_name="My gear name",
            gear_distance=99999,
        )
        assert Activity.select().count() == 2

    def test_without_details(self):
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
            heartrate_avg=123.3,
            heartrate_max=139.9,
            # description="My description",
            # gear_name="My gear name",
            # gear_distance=99999,
        )
        assert Activity.select().count() == 1
        assert Activity.get().description is None
        assert Activity.get().gear_name is None
        assert Activity.get().gear_distance is None
