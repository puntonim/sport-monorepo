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
        title="Run - 10x200m",
        strava_activity_id=16022354250,
        garmin_activity_id=20579416584,
        start_date="2025-10-03",
    ),
]
FILE_TESTED_PATH = inspect.getfile(PlotIntervalRunApiCmd)


class TestPlotInterval200mRunApi:
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
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        plot_200m_api = PlotIntervalRunApiCmd(
            garmin_activity_id,
            distance=200,
            n_prev_activities_to_auto_compare=10,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        plot_200m_api.plot(
            save_to_png_file_path=FILE_TESTED_PATH.replace(".py", "-200m.png")
        )

    ## At the time of writing I only have 1 activity with 200m, so I cannot really
    ## record these next 2 test that compares to 1 and 2 prev activities.

    # def test_n_previous_activity_to_compare_1(self):
    #     garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
    #     plot_200m_api = PlotIntervalRunApiCmd(
    #         garmin_activity_id,
    #         distance=200,
    #         n_prev_activities_to_auto_compare=1,
    #         # figure_size=(5, 7),
    #         garmin_connect_token_manager=self.garmin_token_mgr,
    #     )
    #     plot_200m_api.plot(
    #         save_to_png_file_path=self.png_file_root
    #         / "TestPlotInterval200mRunApi-test_n_previous_activity_to_compare_1.png",
    #     )
    #
    # def test_n_previous_activity_to_compare_2(self):
    #     garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
    #     plot_200m_api = PlotIntervalRunApiCmd(
    #         garmin_activity_id,
    #         distance=200,
    #         n_prev_activities_to_auto_compare=2,
    #         # figure_size=(5, 8),
    #         garmin_connect_token_manager=self.garmin_token_mgr,
    #     )
    #     plot_200m_api.plot(
    #         save_to_png_file_path=self.png_file_root
    #         / "TestPlotInterval200mRunApi-test_n_previous_activity_to_compare_2.png",
    #     )

    def test_n_previous_activity_to_compare_0(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        plot_200m_api = PlotIntervalRunApiCmd(
            garmin_activity_id,
            distance=200,
            n_prev_activities_to_auto_compare=0,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        plot_200m_api.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlotInterval200mRunApi-test_n_previous_activity_to_compare_0.png",
        )
