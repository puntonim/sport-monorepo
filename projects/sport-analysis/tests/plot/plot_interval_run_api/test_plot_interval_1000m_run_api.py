import inspect

from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)

from sport_analysis.conf.settings_module import ROOT_DIR
from sport_analysis.plot.plot_interval_run_api.plot_interval_run_api_cmd import (
    PlotIntervalRunApiCmd,
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
    # 1.
    dict(
        title="Run - 5x1000m",
        strava_activity_id=19789659538,
        garmin_activity_id=24018992823,
        start_date="2026-08-18",
    ),
]

FILE_TESTED_PATH = inspect.getfile(PlotIntervalRunApiCmd)


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

    def test_generate_sample_image(self):
        p = PlotIntervalRunApiCmd(
            TEST_ACTIVITIES[1]["garmin_activity_id"],
            distance=1000,
            activity_ids_to_compare=[TEST_ACTIVITIES[0]["garmin_activity_id"]],
            n_prev_activities_to_auto_compare=0,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(save_to_png_file_path=FILE_TESTED_PATH.replace(".py", "-1000m.png"))

    def test_n_previous_activity_to_compare_2(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        p = PlotIntervalRunApiCmd(
            garmin_activity_id,
            distance=1000,
            n_prev_activities_to_auto_compare=2,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlotInterval1000mRunApi-test_n_previous_activity_to_compare_2.png",
        )

    def test_diff_n_intervals(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        p = PlotIntervalRunApiCmd(
            garmin_activity_id,
            distance=1000,
            n_prev_activities_to_auto_compare=1,
            txt_to_search_for_prev_activities_to_auto_compare="3x1000m",
            n_expected_intervals=[3, 4],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlotInterval1000mRunApi-test_diff_n_intervals.png",
        )

    def test_latest(self):
        garmin_activity_id = ("LATEST", -1)
        p = PlotIntervalRunApiCmd(
            garmin_activity_id,
            distance=1000,
            n_expected_intervals=[5],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlotInterval1000mRunApi-test_latest.png",
        )
