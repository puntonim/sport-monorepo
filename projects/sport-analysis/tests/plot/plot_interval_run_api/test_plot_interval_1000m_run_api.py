from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)

from sport_analysis.conf.settings_module import ROOT_DIR
from sport_analysis.plot.plot_interval_run_api.plot_interval_1000m_run_api import (
    PlotInterval1000mRunApi,
)
from tests.conftest import is_vcr_enabled, is_vcr_record_mode

TEST_ACTIVITIES = [
    # 0.
    dict(
        title="Run - 4x1000m",
        strava_activity_id=14395836152,
        garmin_activity_id=19042748874,
        start_date="2025-05-06",
    ),
]


class TestPlotInterval1000mRunApi:
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
        p = PlotInterval1000mRunApi(
            garmin_activity_id,
            n_previous_activities_to_compare=0,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlotInterval1000mRunApi-test_happy_flow.png",
        )
