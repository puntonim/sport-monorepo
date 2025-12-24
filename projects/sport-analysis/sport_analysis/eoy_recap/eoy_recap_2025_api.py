from datetime import datetime

import datetime_utils
import log_utils as logger
from strava_client import StravaClient
from strava_client.strava_token_managers import (
    AwsParameterStoreStravaTokenManager,
    FakeTestStravaTokenManager,
    FileStravaTokenManager,
)

from ..conf import settings
from .eoy_stats import EoyStats


class EoyRecap2025Api:
    def __init__(
        self,
        start_date_after: datetime | str = "2025-01-01T00:00:00+01:00",
        start_date_before: datetime | str = "2025-12-31T23:59:59+01:00",
        strava_token_manager: (
            AwsParameterStoreStravaTokenManager
            | FileStravaTokenManager
            | FakeTestStravaTokenManager
            | None
        ) = None,
    ):
        """
        Args:
            start_date_after: eg. "2024-01-01T00:00:01+01:00" or datetime(2024, 1, 6, 17, 20, tzinfo=ZoneInfo("Europe/Rome")).
            start_date_before: eg. "2024-01-01T00:00:01+01:00" or datetime(2024, 1, 6, 17, 20, tzinfo=ZoneInfo("Europe/Rome")).
            strava_token_manager: use FakeTestStravaTokenManager when
             replaying VCR episodes.
        """
        # Parse start_date_after|before.
        self.start_date_after: datetime = datetime_utils.parse_datetime_arg(
            start_date_after
        )
        self.start_date_before: datetime = datetime_utils.parse_datetime_arg(
            start_date_before
        )
        strava_token_manager = (
            strava_token_manager
            or AwsParameterStoreStravaTokenManager(
                settings.TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
                settings.CLIENT_ID_PARAMETER_STORE_KEY_PATH,
                settings.CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            )
        )
        self.strava = StravaClient(strava_token_manager.get_access_token())

    def plot(
        self,
    ):
        """
        Create end-of-year recap for 2025 from activities in Strava API.
        """
        logger.info("[bold underline on white]EOY RECAP 2025[/]")
        logger.info(
            f"[underline]Filter[/]: [bold on yellow]start-date-after[/] = {self.start_date_after.isoformat()}",
            highlight=False,
        )
        logger.info(
            f"[underline]Filter[/]: [bold on yellow]start-date-before[/] = {self.start_date_before.isoformat()}",
            highlight=False,
        )

        ## Collect all Strava activity summaries in 2025.
        page_n = 1
        activities = list()
        while True:
            response = self.strava.list_activities(
                after_ts=self.start_date_after,
                before_ts=self.start_date_before,
                n_results_per_page=100,
                page_n=page_n,
            )
            n = len(response.data)

            activities.extend(response.data)

            # If we got 100 results, then there must be another page, otherwise this was
            #  the last page.
            if n < 100:
                break
            page_n += 1

        ## Build stats.
        stats = EoyStats(
            activities,
            start_date_after=self.start_date_after,
            start_date_before=self.start_date_before,
        )
        stats.plot()


prs_weight_training = {
    "bench press": "105kg",
    "deadlift": "160kg",
    "squat": "110kg",
    "shoulder press": "62kg",
    "pull-up": "40kg??",  # TODO
    "pull-up max rep": "???",  # TODO
    "dip": "???kg",  # TODO
    "dip max rep": "???",  # TODO
}

prs_run = {
    "200m": "29.77s (3 Oct)",
    "300m": "46.73s (16 Oct)",
    "1000m": "3:41 (26 Nov)",
    "5km": "20:14 (9 May at Fosso BG)",
    "10km": "",  # TODO...scrivere codice..............................
    "HM": "1:33:12 (9 Mar in Monza)",
    "longest by km": None,  # To be found automatically in EoyStats.
    "longest by moving time": None,  # To be found automatically in EoyStats.
    "longest by elevation gain": None,  # To be found automatically in EoyStats.
}

prs_ride = {
    "20km Adda": "25.7km/h (20 Jul)",
    "Selvino MTB": "",  # TODO...scrivere codice..............................
    "Selvino road": None,
    "Stelvio road": "1:56:38 (13 Jul at Re Stelvio Mapei)",
    "longest by km": None,  # To be found automatically in EoyStats.
    "longest by moving time": None,  # To be found automatically in EoyStats.
    "longest by elevation gain": None,  # To be found automatically in EoyStats.
}
