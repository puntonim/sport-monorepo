import inspect

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
    # 1.
    dict(
        title="Ranica - Selvino - Lonno",
        strava_activity_id=17961512563,
        garmin_activity_id=22393217420,
        start_date="2026-04-03",
    ),
]

FILE_TESTED_PATH = inspect.getfile(PlotClimbRideApi)


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
            strava_token_manager=self.strava_token_mgr,
        )
        plotter.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlotClimbRideApi-test_happy_flow.png",
        )

    def test_generate_sample_image_with_strava_segment(self):
        garmin_activity_id = TEST_ACTIVITIES[1]["garmin_activity_id"]
        plotter = PlotClimbRideApi(
            garmin_activity_id,
            title="Ranica - Selvino - Lonno",
            # segment_start_meters=0,
            # segment_end_meters=21110,
            segment_strava_name="Selvino Fontanella",
            segment_title="Selvino Fontanella",
            figure_size=(5.0, 6.5),
            garmin_connect_token_manager=self.garmin_token_mgr,
            strava_token_manager=self.strava_token_mgr,
            # percentile_to_draw="p80",
        )
        plotter.plot(save_to_png_file_path=FILE_TESTED_PATH.replace(".py", ".png"))

    def test_latest(self):
        garmin_activity_id = ("LATEST", 0)
        plotter = PlotClimbRideApi(
            garmin_activity_id,
            title="Re Stelvio Mapei",
            segment_start_meters=0,
            segment_end_meters=21110,
            segment_title="Climb segment only",
            figure_size=(5.0, 6.5),
            garmin_connect_token_manager=self.garmin_token_mgr,
            strava_token_manager=self.strava_token_mgr,
        )
        plotter.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlotClimbRideApi-test_latest.png",
        )

    def test_percentile_p80(self):
        garmin_activity_id = TEST_ACTIVITIES[1]["garmin_activity_id"]
        plotter = PlotClimbRideApi(
            garmin_activity_id,
            title="Ranica - Selvino - Lonno",
            # segment_start_meters=0,
            # segment_end_meters=21110,
            segment_strava_name="Selvino Fontanella",
            segment_title="Selvino Fontanella",
            figure_size=(5.0, 6.5),
            garmin_connect_token_manager=self.garmin_token_mgr,
            strava_token_manager=self.strava_token_mgr,
            percentile_to_draw="p80",
        )
        plotter.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlotClimbRideApi-test_percentile_p80.png",
        )

    def test_percentile_p98(self):
        garmin_activity_id = TEST_ACTIVITIES[1]["garmin_activity_id"]
        plotter = PlotClimbRideApi(
            garmin_activity_id,
            title="Ranica - Selvino - Lonno",
            # segment_start_meters=0,
            # segment_end_meters=21110,
            segment_strava_name="Selvino Fontanella",
            segment_title="Selvino Fontanella",
            figure_size=(5.0, 6.5),
            garmin_connect_token_manager=self.garmin_token_mgr,
            strava_token_manager=self.strava_token_mgr,
            percentile_to_draw="P98",
        )
        plotter.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlotClimbRideApi-test_percentile_p98.png",
        )
