from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)

from sport_analysis.conf.settings_module import ROOT_DIR
from sport_analysis.plot.plot_ride_api.plot_simple_ride_api import PlotSimpleRideApi
from tests.conftest import is_vcr_enabled, is_vcr_record_mode

TEST_ACTIVITIES = [
    # 0.
    dict(
        title="Ride - Verdellino - Adda 20km",
        strava_activity_id=15179749926,
        garmin_activity_id=19795436851,
        start_date="2025-07-20",
    ),
]


class TestPlotSimpleRideApi:
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
        plotter = PlotSimpleRideApi(
            garmin_activity_id,
            title="Verdellino - Adda 20km",
            figure_size=(5.0, 6.5),
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        plotter.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlotSimpleRideApi-test_happy_flow.png",
        )
