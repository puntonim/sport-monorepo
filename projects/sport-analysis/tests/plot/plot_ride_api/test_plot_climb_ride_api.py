from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)

from sport_analysis.conf.settings_module import ROOT_DIR
from sport_analysis.plot.plot_ride_api.plot_climb_ride_api import PlotClimbRideApi
from tests.conftest import is_vcr_enabled, is_vcr_record_mode

TEST_ACTIVITIES = [
    # 0.
    dict(
        title="Ride - Re Stelvio Mapei",
        strava_activity_id=15104529341,
        garmin_activity_id=19792668968,
        start_date="2025-07-13",
    ),
]


class TestPlotClimbRideApi:
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
        plotter = PlotClimbRideApi(
            garmin_activity_id,
            title="Re Stelvio Mapei",
            segment_start_meters=0,
            segment_end_meters=21110,
            segment_title="Climb segment only",
            figure_size=(5.0, 6.5),
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        plotter.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlotClimbRideApi-test_happy_flow.png",
        )
