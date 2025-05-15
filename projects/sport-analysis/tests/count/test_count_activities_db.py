from datetime import datetime
from zoneinfo import ZoneInfo

from sport_analysis.count.count_activities_db import count_activities_db


class TestCountActivitiesDb:
    def test_activities_in_2024(self, create_db_fixture):
        assert (
            count_activities_db(
                start_date_after="2024-01-01T00:00:01+01:00",
                start_date_before="2024-12-31T23:59:59+01:00",
            )
            == 358
        )

    def test_rides_in_2024(self, create_db_fixture):
        assert (
            count_activities_db(
                start_date_after=datetime(
                    2024, 1, 1, 0, 0, tzinfo=ZoneInfo("Europe/Rome")
                ),
                start_date_before="2024-12-31T23:59:59+01:00",
                activity_type="ride",
            )
            == 50
        )
