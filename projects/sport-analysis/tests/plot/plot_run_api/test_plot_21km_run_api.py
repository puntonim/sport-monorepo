from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)

from sport_analysis.conf.settings_module import ROOT_DIR
from sport_analysis.plot.plot_run_api.plot_21km_run_api import Plot21KmRunApi
from tests.conftest import is_vcr_enabled, is_vcr_record_mode

TEST_ACTIVITIES = [
    # 0.
    dict(
        title="Run - Sarnico-Lovere",
        strava_activity_id=14299142926,
        garmin_activity_id=18948270166,
        start_date="2025-04-27",
    ),
]


class TestPlot21KmRunApi:
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
        self.png_file_root = ROOT_DIR / "tests" / "test-output-images"

    def test_happy_flow(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        plot_half_marathon_api = Plot21KmRunApi(
            garmin_activity_id,
            garmin_connect_token_manager=self.garmin_token_mgr,
            pace_plot_set_y_axis_bottom_to_slowest_pace_perc=4.0,
        )
        plot_half_marathon_api.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlot21KmRunApi-test_happy_flow.png",
        )
