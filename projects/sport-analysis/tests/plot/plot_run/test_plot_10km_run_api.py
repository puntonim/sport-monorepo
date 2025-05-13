from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)

from sport_analysis.conf.settings_module import ROOT_DIR
from sport_analysis.plot.plot_run.plot_10km_run_api import Plot10KmRunApi
from tests.conftest import is_vcr_enabled, is_vcr_record_mode

TEST_ACTIVITIES = [
    # 0.
    dict(
        title="Run - Fosso 1 Cologno",
        strava_activity_id=14357511465,
        garmin_activity_id=19005790234,
        start_date="2025-05-02",
    ),
]


class TestPlot10KmRunApi:
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
        plot_half_marathon_api = Plot10KmRunApi(
            garmin_activity_id,
            activity_ids_to_compare=[
                19074660632,
            ],
            title="Fosso Bergamasco: Cologno al Serio, 1a tappa",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        plot_half_marathon_api.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlot10KmRunApi-test_happy_flow.png",
        )
