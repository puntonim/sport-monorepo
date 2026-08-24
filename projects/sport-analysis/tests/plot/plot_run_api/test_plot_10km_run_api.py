import inspect

from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)

from sport_analysis.conf.settings_module import ROOT_DIR
from sport_analysis.plot.plot_run_api.plot_10km_run_api import Plot10KmRunApi
from tests.conftest import is_vcr_enabled, is_vcr_record_mode

TEST_ACTIVITIES = [
    # 0.
    dict(
        title="Run - Fosso 1 Camisano",
        strava_activity_id=18520491638,
        garmin_activity_id=22893403669,
        start_date="2026-05-15",
    ),
    # 1.
    dict(
        title="Run - Fosso 2 Torre",
        strava_activity_id=18679582822,
        garmin_activity_id=23035885088,
        start_date="2026-05-27",
    ),
    # 2.
    dict(
        title="Run - Fosso 4 Arcene",
        strava_activity_id=18894552637,
        garmin_activity_id=23226614861,
        start_date="2026-06-12",
    ),
    # 3.
    dict(
        title="Run - Fosso 5 Zanica",
        strava_activity_id=18988079605,
        garmin_activity_id=23309590263,
        start_date="2026-06-19",
    ),
    # 4.
    dict(
        title="Verdellino Running",  # Run 80/20.
        strava_activity_id=19706505901,
        garmin_activity_id=23945353188,
        start_date="2026-08-12",
    ),
    # 5.
    dict(
        title="Verdellino Running",  # Run slow.
        strava_activity_id=19822600349,
        garmin_activity_id=24048184816,
        start_date="2026-08-12",
    ),
]

FILE_TESTED_PATH = inspect.getfile(Plot10KmRunApi)


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

    def test_generate_sample_image(self):
        garmin_activity_id = TEST_ACTIVITIES[4]["garmin_activity_id"]
        plot_api = Plot10KmRunApi(
            garmin_activity_id,
            activity_ids_to_compare=[],
            percentile_to_draw="p80",
            # title="Verdellino running",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        plot_api.plot(save_to_png_file_path=FILE_TESTED_PATH.replace(".py", "1.png"))

    def test_generate_sample_image_w_comparison(self):
        garmin_activity_id = TEST_ACTIVITIES[3]["garmin_activity_id"]
        plot_api = Plot10KmRunApi(
            garmin_activity_id,
            activity_ids_to_compare=[
                TEST_ACTIVITIES[2]["garmin_activity_id"],
                TEST_ACTIVITIES[1]["garmin_activity_id"],
                TEST_ACTIVITIES[0]["garmin_activity_id"],
            ],
            title="Fosso Bergamasco: Zanica, 5a tappa",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        plot_api.plot(save_to_png_file_path=FILE_TESTED_PATH.replace(".py", "2.png"))

    def test_latest(self):
        garmin_activity_id = ("LATEST", -2)
        plot_api = Plot10KmRunApi(
            garmin_activity_id,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        plot_api.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlot10KmRunApi-test_latest.png",
        )

    def test_percentile_p80(self):
        garmin_activity_id = TEST_ACTIVITIES[4]["garmin_activity_id"]
        plot_api = Plot10KmRunApi(
            garmin_activity_id,
            activity_ids_to_compare=[],
            percentile_to_draw="P80",
            # title="Verdellino running",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        plot_api.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlot10KmRunApi-test_percentile_p80.png"
        )

    def test_percentile_p98(self):
        garmin_activity_id = TEST_ACTIVITIES[5]["garmin_activity_id"]
        plot_api = Plot10KmRunApi(
            garmin_activity_id,
            activity_ids_to_compare=[],
            percentile_to_draw="p98",
            # title="Verdellino running",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        plot_api.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlot10KmRunApi-test_percentile_p98.png"
        )
