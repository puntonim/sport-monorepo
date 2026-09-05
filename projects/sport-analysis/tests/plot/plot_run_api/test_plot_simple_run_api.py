import inspect

import pytest
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)

from sport_analysis.conf.settings_module import ROOT_DIR
from sport_analysis.plot.plot_run_api.plot_simple_run_api_cmd import PlotSimpleRunApiCmd
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
    # 6.
    dict(
        title="Run - Sarnico-Lovere 2025",
        strava_activity_id=14299142926,
        garmin_activity_id=18948270166,
        start_date="2025-04-27",
    ),
    # 7.
    dict(
        title="Run - Sarnico-Lovere 2026",
        strava_activity_id=18262545803,
        garmin_activity_id=22663177131,
        start_date="2026-04-26",
    ),
]

FILE_TESTED_PATH = inspect.getfile(PlotSimpleRunApiCmd)


class TestPlotSimpleRunApi:
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

    def test_generate_sample_image_10km(self):
        garmin_activity_id = TEST_ACTIVITIES[4]["garmin_activity_id"]
        p = PlotSimpleRunApiCmd(
            garmin_activity_id,
            percentile_to_draw="p80",
            hr_zones_to_hatch=("Z3",),
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(save_to_png_file_path=FILE_TESTED_PATH.replace("_cmd.py", "-10km.png"))

    def test_generate_sample_image_21km(self):
        garmin_activity_id = TEST_ACTIVITIES[6]["garmin_activity_id"]
        p = PlotSimpleRunApiCmd(
            garmin_activity_id,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(save_to_png_file_path=FILE_TESTED_PATH.replace("_cmd.py", "-21km.png"))

    def test_generate_sample_image_w_comparison(self):
        garmin_activity_id = TEST_ACTIVITIES[3]["garmin_activity_id"]
        p = PlotSimpleRunApiCmd(
            garmin_activity_id,
            prev_runs_activity_ids_to_compare=[
                TEST_ACTIVITIES[2]["garmin_activity_id"],
                TEST_ACTIVITIES[1]["garmin_activity_id"],
                TEST_ACTIVITIES[0]["garmin_activity_id"],
            ],
            title="Fosso Bergamasco: Zanica, 5a tappa",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=FILE_TESTED_PATH.replace(
                "_cmd.py", "-7km-comparison.png"
            )
        )

    def test_required_args(self):
        # Required args: garmin_activity_id.
        with pytest.raises(TypeError):
            PlotSimpleRunApiCmd()
        p = PlotSimpleRunApiCmd(TEST_ACTIVITIES[3]["garmin_activity_id"])
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_latest_3(self):
        garmin_activity_id = ("LATEST", -3)
        p = PlotSimpleRunApiCmd(
            garmin_activity_id,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_prev_runs_activity_ids_to_compare_none(self):
        garmin_activity_id = TEST_ACTIVITIES[3]["garmin_activity_id"]
        p = PlotSimpleRunApiCmd(
            garmin_activity_id,
            prev_runs_activity_ids_to_compare=None,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_prev_runs_activity_ids_to_compare_empty_list(self):
        garmin_activity_id = TEST_ACTIVITIES[3]["garmin_activity_id"]
        p = PlotSimpleRunApiCmd(
            garmin_activity_id,
            prev_runs_activity_ids_to_compare=[],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_prev_runs_activity_ids_to_compare_1(self):
        garmin_activity_id = TEST_ACTIVITIES[3]["garmin_activity_id"]
        p = PlotSimpleRunApiCmd(
            garmin_activity_id,
            prev_runs_activity_ids_to_compare=[
                TEST_ACTIVITIES[2]["garmin_activity_id"]
            ],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_prev_runs_activity_ids_to_compare_2(self):
        garmin_activity_id = TEST_ACTIVITIES[3]["garmin_activity_id"]
        p = PlotSimpleRunApiCmd(
            garmin_activity_id,
            prev_runs_activity_ids_to_compare=[
                TEST_ACTIVITIES[1]["garmin_activity_id"]
            ],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_all_zones_hatched(self):
        garmin_activity_id = TEST_ACTIVITIES[4]["garmin_activity_id"]
        p = PlotSimpleRunApiCmd(
            garmin_activity_id,
            hr_zones_to_hatch=("z5", "Z0", "z1", "z2", "z4", "Z3"),
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_percentile_p80(self):
        garmin_activity_id = TEST_ACTIVITIES[4]["garmin_activity_id"]
        p = PlotSimpleRunApiCmd(
            garmin_activity_id,
            percentile_to_draw="P80",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_percentile_p98(self):
        garmin_activity_id = TEST_ACTIVITIES[5]["garmin_activity_id"]
        p = PlotSimpleRunApiCmd(
            garmin_activity_id,
            percentile_to_draw="p98",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_percentile_invalid(self):
        garmin_activity_id = TEST_ACTIVITIES[5]["garmin_activity_id"]
        with pytest.raises(ValueError):
            PlotSimpleRunApiCmd(
                garmin_activity_id,
                percentile_to_draw="XXX",
                garmin_connect_token_manager=self.garmin_token_mgr,
            )

    def test_pace_plot_set_y_axis_bottom_to_slowest_pace_perc(self):
        # To best test this we use a run with a fast pace and compare it with one with
        #  a slow pace.
        p = PlotSimpleRunApiCmd(
            22975082447,
            prev_runs_activity_ids_to_compare=(24048184816,),
            garmin_connect_token_manager=self.garmin_token_mgr,
            pace_plot_set_y_axis_bottom_to_slowest_pace_perc=4.0,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_pace_plot_set_y_axis_bottom_to_slowest_pace_perc_long_distance(self):
        # Actual real case that inspired this feature.
        p = PlotSimpleRunApiCmd(
            TEST_ACTIVITIES[7]["garmin_activity_id"],
            prev_runs_activity_ids_to_compare=(
                TEST_ACTIVITIES[6]["garmin_activity_id"],
            ),
            garmin_connect_token_manager=self.garmin_token_mgr,
            pace_plot_set_y_axis_bottom_to_slowest_pace_perc=4.0,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_do_skip_hr_in_pace_plot_true(self):
        garmin_activity_id = TEST_ACTIVITIES[4]["garmin_activity_id"]
        p = PlotSimpleRunApiCmd(
            garmin_activity_id,
            do_skip_hr_in_pace_plot=True,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_do_skip_hr_in_pace_plot_false(self):
        garmin_activity_id = TEST_ACTIVITIES[4]["garmin_activity_id"]
        p = PlotSimpleRunApiCmd(
            garmin_activity_id,
            do_skip_hr_in_pace_plot=False,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_do_skip_hr_in_pace_plot_with_prev_runs_activity_ids_to_compare(self):
        garmin_activity_id = TEST_ACTIVITIES[4]["garmin_activity_id"]
        p = PlotSimpleRunApiCmd(
            garmin_activity_id,
            prev_runs_activity_ids_to_compare=[
                TEST_ACTIVITIES[2]["garmin_activity_id"]
            ],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_do_skip_hr_in_pace_plot_forced_with_prev_runs_activity_ids_to_compare(
        self,
    ):
        # This test makes sure that do_skip_hr_in_pace_plot is forced to True
        #  when prev_runs_activity_ids_to_compare is given.
        garmin_activity_id = TEST_ACTIVITIES[4]["garmin_activity_id"]
        p = PlotSimpleRunApiCmd(
            garmin_activity_id,
            do_skip_hr_in_pace_plot=False,
            prev_runs_activity_ids_to_compare=[
                TEST_ACTIVITIES[2]["garmin_activity_id"]
            ],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_title(self):
        p = PlotSimpleRunApiCmd(
            TEST_ACTIVITIES[4]["garmin_activity_id"],
            title="My Title",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_figure_size(self):
        p = PlotSimpleRunApiCmd(
            TEST_ACTIVITIES[4]["garmin_activity_id"],
            figure_size=(5, 8.5),
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )
