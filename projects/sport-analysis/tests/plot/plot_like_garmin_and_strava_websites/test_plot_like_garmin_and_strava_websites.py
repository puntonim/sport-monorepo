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
from sport_analysis.plot.plot_like_garmin_and_strava_websites.plot_like_garmin_and_strava_websites import (
    plot_like_garmin_and_strava_websites_api,
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


class TestPlotLikeGarminAndStravaWebsitesApi:
    # NOTE: these tests create images in tests/test-output-images/.

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
        self.png_file_root = ROOT_DIR / "tests" / "test-output-images"

    def test_1(self):
        strava_activity_id = TEST_ACTIVITIES[0]["strava_activity_id"]
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        plot_like_garmin_and_strava_websites_api(
            strava_activity_id,
            garmin_activity_id,
            title=TEST_ACTIVITIES[0]["title"],
            strava_token_manager=self.strava_token_mgr,
            garmin_connect_token_manager=self.garmin_token_mgr,
            save_to_png_file_path=self.png_file_root
            / "TestPlotLikeGarminAndStravaWebsitesApi-test_1.png",
        )

    def test_2(self):
        strava_activity_id = TEST_ACTIVITIES[1]["strava_activity_id"]
        garmin_activity_id = TEST_ACTIVITIES[1]["garmin_activity_id"]
        plot_like_garmin_and_strava_websites_api(
            strava_activity_id,
            garmin_activity_id,
            title=TEST_ACTIVITIES[1]["title"],
            strava_token_manager=self.strava_token_mgr,
            garmin_connect_token_manager=self.garmin_token_mgr,
            save_to_png_file_path=self.png_file_root
            / "TestPlotLikeGarminAndStravaWebsitesApi-test_2.png",
        )

    def test_3(self):
        strava_activity_id = TEST_ACTIVITIES[2]["strava_activity_id"]
        garmin_activity_id = TEST_ACTIVITIES[2]["garmin_activity_id"]
        plot_like_garmin_and_strava_websites_api(
            strava_activity_id,
            garmin_activity_id,
            title=TEST_ACTIVITIES[2]["title"],
            strava_token_manager=self.strava_token_mgr,
            garmin_connect_token_manager=self.garmin_token_mgr,
            save_to_png_file_path=self.png_file_root
            / "TestPlotLikeGarminAndStravaWebsitesApi-test_3.png",
        )

    def test_4(self):
        strava_activity_id = TEST_ACTIVITIES[3]["strava_activity_id"]
        garmin_activity_id = TEST_ACTIVITIES[3]["garmin_activity_id"]
        plot_like_garmin_and_strava_websites_api(
            strava_activity_id,
            garmin_activity_id,
            title=TEST_ACTIVITIES[3]["title"],
            strava_token_manager=self.strava_token_mgr,
            garmin_connect_token_manager=self.garmin_token_mgr,
            save_to_png_file_path=self.png_file_root
            / "TestPlotLikeGarminAndStravaWebsitesApi-test_4.png",
        )

    def test_5(self):
        strava_activity_id = TEST_ACTIVITIES[4]["strava_activity_id"]
        garmin_activity_id = TEST_ACTIVITIES[4]["garmin_activity_id"]
        plot_like_garmin_and_strava_websites_api(
            strava_activity_id,
            garmin_activity_id,
            title=TEST_ACTIVITIES[4]["title"],
            strava_token_manager=self.strava_token_mgr,
            garmin_connect_token_manager=self.garmin_token_mgr,
            save_to_png_file_path=self.png_file_root
            / "TestPlotLikeGarminAndStravaWebsitesApi-test_5.png",
        )
