from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)
from strava_client.strava_token_managers import (
    AwsParameterStoreStravaTokenManager,
    FakeTestStravaTokenManager,
)

from sport_analysis.conf import settings
from sport_analysis.conf.settings_module import ROOT_DIR
from sport_analysis.search.search_matching_activity_api import (
    search_garmin_activity_matching_strava_activity_api,
    search_strava_activity_matching_garmin_activity_api,
)
from tests.conftest import is_vcr_enabled, is_vcr_record_mode

TEST_ACTIVITIES = [
    # 0.
    dict(
        title="Bike, Selvino and Salmezza",
        strava_activity_id=14038286532,
        garmin_activity_id=18689027868,
        start_date="2025-03-31",
    ),
    # 1.
    dict(
        title="Bike, Selvino and Salmezza - Selvino record with road bike",
        strava_activity_id=11681601053,
        garmin_activity_id=15974223178,
        start_date="2024-06-18",
    ),
    # 2.
    dict(
        title="Run, Milano21",
        strava_activity_id=10283002244,
        garmin_activity_id=12877651519,
        start_date="2023-11-26",
    ),
    # 3.
    dict(
        title="Bike, 1st Sellaronda - long activity with many pauses",
        strava_activity_id=9240064780,
        garmin_activity_id=11313479371,
        start_date="2023-06-10",
    ),
    # 4.
    dict(
        title="Snowboarding - never paused the watch, but many not moving times",
        strava_activity_id=13983015686,
        garmin_activity_id=18633237715,
        start_date="2025-03-25",
    ),
    # 5.
    # It was a 5x40s but I messed up with the first interval, pressing the
    #  lap button by mistake, so I pressed it again.
    dict(
        title="Bike - Selvino 5x40s",
        strava_activity_id=14211292173,
        garmin_activity_id=18861865288,
        start_date="2025-04-18",
    ),
    # 6.
    dict(
        title="Run - Limone Sunset Running Race",
        strava_activity_id=13956710205,
        garmin_activity_id=18606916834,
        start_date="2025-03-22",
    ),
    # 7.
    dict(
        title="Run - 6x300m",
        strava_activity_id=14273546414,
        garmin_activity_id=18923007987,
        start_date="2025-04-24",
    ),
]


class TestSearchGarminActivityMatchingStravaActivity:
    def setup_method(self):
        self.garmin_token_mgr = (
            # Use the regular file token manager when recording vcr episodes.
            FileGarminConnectTokenManager(
                token_file_path=ROOT_DIR / "garmin-connect-token.json"
            )
            if is_vcr_record_mode() or not is_vcr_enabled()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestGarminConnectTokenManager()
        )
        self.strava_token_mgr = (
            # Use AWS Param Store token manager when recording vcr episodes.
            AwsParameterStoreStravaTokenManager(
                settings.TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
                settings.CLIENT_ID_PARAMETER_STORE_KEY_PATH,
                settings.CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            )
            if is_vcr_record_mode() or not is_vcr_enabled()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestStravaTokenManager()
        )

    def test_happy_flow(self):
        for activity in TEST_ACTIVITIES[:3]:
            found = search_garmin_activity_matching_strava_activity_api(
                activity["strava_activity_id"],
                strava_token_manager=self.strava_token_mgr,
                garmin_connect_token_manager=self.garmin_token_mgr,
            )
            assert found["activityId"] == activity["garmin_activity_id"]


class TestSearchStravaActivityMatchingGarminActivityApi:
    def setup_method(self):
        self.garmin_token_mgr = (
            # Use the regular file token manager when recording vcr episodes.
            FileGarminConnectTokenManager(
                token_file_path=ROOT_DIR / "garmin-connect-token.json"
            )
            if is_vcr_record_mode() or not is_vcr_enabled()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestGarminConnectTokenManager()
        )
        self.strava_token_mgr = (
            # Use AWS Param Store token manager when recording vcr episodes.
            AwsParameterStoreStravaTokenManager(
                settings.TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
                settings.CLIENT_ID_PARAMETER_STORE_KEY_PATH,
                settings.CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            )
            if is_vcr_record_mode() or not is_vcr_enabled()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestStravaTokenManager()
        )

    def test_happy_flow(self):
        for activity in TEST_ACTIVITIES[:3]:
            found = search_strava_activity_matching_garmin_activity_api(
                activity["garmin_activity_id"],
                strava_token_manager=self.strava_token_mgr,
                garmin_connect_token_manager=self.garmin_token_mgr,
            )
            assert found["id"] == activity["strava_activity_id"]
