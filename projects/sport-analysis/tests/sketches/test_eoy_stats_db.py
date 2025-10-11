from datetime import datetime
from zoneinfo import ZoneInfo

from sport_analysis.sketches.eoy_stats_db import eoy_stats_db


class TestEoyStatsDb:
    def test_happy_flow(self, create_db_fixture):
        eoy_stats_db(
            start_date_after="2024-01-02T00:00:00+01:00",
            start_date_before="2024-12-31T23:59:59+01:00",
        )
