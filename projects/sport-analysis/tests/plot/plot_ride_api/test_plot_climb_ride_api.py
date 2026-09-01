import inspect

import pytest
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
from sport_analysis.plot.plot_ride_api.plot_climb_ride_api_cmd import (
    PlotClimbRideApiCmd,
    StravaSegmentEffortNotFound,
)
from tests.conftest import is_vcr_enabled, is_vcr_record_mode

TEST_ACTIVITIES = [
    # 0.
    dict(
        title="Ride - Re Stelvio Mapei",
        strava_activity_id=19280944043,
        garmin_activity_id=23569511098,
        start_date="2026-07-12",
    ),
    # 1.
    dict(
        title="Ranica - Selvino - Lonno",
        strava_activity_id=17961512563,
        garmin_activity_id=22393217420,
        start_date="2026-04-03",
    ),
    # 2.
    dict(
        title="PR Selvino MTB",
        strava_activity_id=12591555468,
        garmin_activity_id=17219352641,
        start_date="2024-10-06",
    ),
    # 3.
    dict(
        title="PR Selvino BDC",
        strava_activity_id=11681601053,
        garmin_activity_id=15974223178,
        start_date="2024-06-18",
    ),
    # # 3.
    # dict(
    #     title="PR Stelvio",  # Note: broken activity because I switched sport half way.
    #     strava_activity_id=15104529341,
    #     garmin_activity_id=19792668848,
    #     start_date="2025-07-13",
    # ),
    # 4.
    dict(
        title="2nd best time Stelvio",
        strava_activity_id=19280944043,
        garmin_activity_id=23569511098,
        start_date="2025-07-12",
    ),
]

STRAVA_SEGMENT_SELVINO = {"id": 14418673, "name": "Selvino Fontanella"}
STRAVA_SEGMENT_STELVIO = {"id": 15756100, "name": "Passo Stelvio (via Bormio)"}

FILE_TESTED_PATH = inspect.getfile(PlotClimbRideApiCmd)


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

    def test_generate_sample_image(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        p = PlotClimbRideApiCmd(
            garmin_activity_id,
            title="Re Stelvio Mapei",
            segment_start_meters=0,
            segment_end_meters=21110,
            segment_title="climb",
            figure_size=(5.0, 6.5),
            garmin_connect_token_manager=self.garmin_token_mgr,
            strava_token_manager=self.strava_token_mgr,
        )
        p.plot(save_to_png_file_path=FILE_TESTED_PATH.replace(".py", ".png"))

    def test_required_args(self):
        # Required args: garmin_activity_id.
        with pytest.raises(TypeError):
            PlotClimbRideApiCmd()
        p = PlotClimbRideApiCmd(
            TEST_ACTIVITIES[0]["garmin_activity_id"],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_latest_6(self):
        garmin_activity_id = ("LATEST", -6)
        p = PlotClimbRideApiCmd(
            garmin_activity_id,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_all_zones_hatched(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        p = PlotClimbRideApiCmd(
            garmin_activity_id,
            hr_zones_to_hatch=("z5", "Z0", "z1", "z2", "z4", "Z3"),
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_percentile_p80(self):
        garmin_activity_id = TEST_ACTIVITIES[1]["garmin_activity_id"]
        p = PlotClimbRideApiCmd(
            garmin_activity_id,
            percentile_to_draw="p80",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_percentile_p98(self):
        garmin_activity_id = TEST_ACTIVITIES[1]["garmin_activity_id"]
        p = PlotClimbRideApiCmd(
            garmin_activity_id,
            percentile_to_draw="P98",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_percentile_invalid(self):
        garmin_activity_id = TEST_ACTIVITIES[1]["garmin_activity_id"]
        with pytest.raises(ValueError):
            PlotClimbRideApiCmd(
                garmin_activity_id,
                percentile_to_draw="XXX",
                garmin_connect_token_manager=self.garmin_token_mgr,
            )

    def test_segment(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        p = PlotClimbRideApiCmd(
            garmin_activity_id,
            segment_start_meters=3000,
            segment_end_meters=21110,
            segment_title="climb",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_no_segment_start(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        p = PlotClimbRideApiCmd(
            garmin_activity_id,
            # segment_start_meters=21110,
            segment_end_meters=21110,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_no_segment_end(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        p = PlotClimbRideApiCmd(
            garmin_activity_id,
            segment_start_meters=21110,
            # segment_end_meters=21110,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_segment_title(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        p = PlotClimbRideApiCmd(
            garmin_activity_id,
            title="Re Stelvio Mapei",
            segment_start_meters=0,
            segment_end_meters=21110,
            segment_title="MY CLIMB",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_no_segment_title(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        p = PlotClimbRideApiCmd(
            garmin_activity_id,
            title="Re Stelvio Mapei",
            segment_start_meters=0,
            segment_end_meters=21110,
            # segment_title="climb",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_strava_segment_selvino(self):
        garmin_activity_id = TEST_ACTIVITIES[3]["garmin_activity_id"]
        p = PlotClimbRideApiCmd(
            garmin_activity_id,
            segment_title="Selvino",
            segment_strava_name=STRAVA_SEGMENT_SELVINO["name"],
            title="PR Selvino BDC",
            garmin_connect_token_manager=self.garmin_token_mgr,
            strava_token_manager=self.strava_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_strava_segment_stelvio(self):
        garmin_activity_id = TEST_ACTIVITIES[4]["garmin_activity_id"]
        p = PlotClimbRideApiCmd(
            garmin_activity_id,
            segment_title="Stelvio",
            segment_strava_name=STRAVA_SEGMENT_STELVIO["name"],
            title="2nd best time Stelvio BDC",
            garmin_connect_token_manager=self.garmin_token_mgr,
            strava_token_manager=self.strava_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_strava_segment_does_not_exist(self):
        garmin_activity_id = TEST_ACTIVITIES[3]["garmin_activity_id"]
        p = PlotClimbRideApiCmd(
            garmin_activity_id,
            segment_strava_name="XXX",
            garmin_connect_token_manager=self.garmin_token_mgr,
            strava_token_manager=self.strava_token_mgr,
        )
        with pytest.raises(StravaSegmentEffortNotFound):
            p.plot(
                save_to_png_file_path=self.png_file_root
                / f"{inspect.currentframe().f_code.co_qualname}.png"
            )

    def test_no_segment(self):
        garmin_activity_id = TEST_ACTIVITIES[1]["garmin_activity_id"]
        p = PlotClimbRideApiCmd(
            garmin_activity_id,
            title="Ranica - Selvino - Lonno",
            # segment_start_meters=0,
            # segment_end_meters=21110,
            # segment_strava_name="Selvino Fontanella",
            # segment_title="Selvino Fontanella",
            figure_size=(5.0, 6.5),
            garmin_connect_token_manager=self.garmin_token_mgr,
            strava_token_manager=self.strava_token_mgr,
            # percentile_to_draw="p80",
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_title(self):
        p = PlotClimbRideApiCmd(
            TEST_ACTIVITIES[0]["garmin_activity_id"],
            title="My Title",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_figure_size(self):
        p = PlotClimbRideApiCmd(
            TEST_ACTIVITIES[0]["garmin_activity_id"],
            figure_size=(5, 9.5),
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )
