import inspect

import pytest
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

FILE_TESTED_PATH = inspect.getfile(PlotSimpleRideApi)


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

    def test_generate_sample_image(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        p = PlotSimpleRideApi(
            garmin_activity_id,
            title="Verdellino - Adda 20km",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(save_to_png_file_path=FILE_TESTED_PATH.replace(".py", ".png"))

    def test_required_args(self):
        # Required args: garmin_activity_id.
        with pytest.raises(TypeError):
            PlotSimpleRideApi()
        p = PlotSimpleRideApi(
            TEST_ACTIVITIES[0]["garmin_activity_id"],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_latest_1(self):
        garmin_activity_id = ("LATEST", -1)
        p = PlotSimpleRideApi(
            garmin_activity_id,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_all_zones_hatched(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        p = PlotSimpleRideApi(
            garmin_activity_id,
            hr_zones_to_hatch=("z5", "Z0", "z1", "z2", "z4", "Z3"),
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_percentile_p80(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        p = PlotSimpleRideApi(
            garmin_activity_id,
            percentile_to_draw="P80",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_percentile_p98(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        p = PlotSimpleRideApi(
            garmin_activity_id,
            percentile_to_draw="p98",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_percentile_invalid(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        with pytest.raises(ValueError):
            PlotSimpleRideApi(
                garmin_activity_id,
                percentile_to_draw="XXX",
                garmin_connect_token_manager=self.garmin_token_mgr,
            )

    def test_title(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        p = PlotSimpleRideApi(
            garmin_activity_id,
            title="My Title",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_figure_size(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        p = PlotSimpleRideApi(
            garmin_activity_id,
            figure_size=(5, 9.5),
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )
