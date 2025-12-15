from datetime import datetime
from zoneinfo import ZoneInfo

from sport_analysis.eoy_recap.eoy_recap_api import eoy_recap_api


class TestEoyRecapApiCountActivitiesDb:
    def test_2025(self):
        eoy_recap_api(
            start_date_after="2025-01-01T00:00:00+00:00",
            start_date_before="2025-12-31T23:59:59+00:00",
        )
