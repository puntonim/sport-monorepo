import inspect

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
        title="Run - Sarnico-Lovere 2025",
        strava_activity_id=14299142926,
        garmin_activity_id=18948270166,
        start_date="2025-04-27",
    ),
    # 1.
    dict(
        title="Run - Sarnico-Lovere 2026",
        strava_activity_id=18262545803,
        garmin_activity_id=22663177131,
        start_date="2026-04-26",
    ),
]

FILE_TESTED_PATH = inspect.getfile(Plot21KmRunApi)


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

    def test_generate_sample_image(self):
        plot_half_marathon_api = Plot21KmRunApi(
            TEST_ACTIVITIES[1]["garmin_activity_id"],
            activity_ids_to_compare=[TEST_ACTIVITIES[0]["garmin_activity_id"]],
            garmin_connect_token_manager=self.garmin_token_mgr,
            pace_plot_set_y_axis_bottom_to_slowest_pace_perc=4.0,
        )
        plot_half_marathon_api.plot(
            save_to_png_file_path=FILE_TESTED_PATH.replace(".py", ".png")
        )

    def test_latest(self):
        garmin_activity_id = ("LATEST", -2)
        plot_half_marathon_api = Plot21KmRunApi(
            garmin_activity_id,
            garmin_connect_token_manager=self.garmin_token_mgr,
            pace_plot_set_y_axis_bottom_to_slowest_pace_perc=4.0,
        )
        plot_half_marathon_api.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlot21KmRunApi-test_latest.png",
        )
