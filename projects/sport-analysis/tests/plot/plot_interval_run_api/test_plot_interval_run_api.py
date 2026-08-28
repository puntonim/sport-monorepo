import inspect
import json

import pytest
from garmin_connect_client import ActivityTypedSplitsResponse
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)

from sport_analysis.conf.settings_module import ROOT_DIR
from sport_analysis.plot.plot_interval_run_api.plot_interval_run_api_cmd import (
    DistanceNotSupported,
    IncompatibleArgs,
    NumberOfExpectedIntervalsError,
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
    # 2.
    dict(
        title="Run - 10x200m",
        strava_activity_id=16022354250,
        garmin_activity_id=20579416584,
        start_date="2025-10-03",
    ),
    # 3.
    dict(
        title="Run - 6x300m",
        strava_activity_id=14273546414,
        garmin_activity_id=18923007987,
        start_date="2025-04-24",
    ),
    # 4.
    dict(
        title="7x100m",
        strava_activity_id=17999703826,
        garmin_activity_id=22427297044,
        start_date="2026-04-26",
    ),
]

FILE_TESTED_PATH = inspect.getfile(PlotIntervalRunApiCmd)


class TestPlotIntervalRunApi:
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

    def test_generate_sample_image_1000m(self):
        p = PlotIntervalRunApiCmd(
            TEST_ACTIVITIES[1]["garmin_activity_id"],
            distance=1000,
            prev_runs_activity_ids_to_compare=[
                TEST_ACTIVITIES[0]["garmin_activity_id"]
            ],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(save_to_png_file_path=FILE_TESTED_PATH.replace(".py", "-1000m.png"))

    def test_generate_sample_image_100m(self):
        garmin_activity_id = TEST_ACTIVITIES[4]["garmin_activity_id"]
        p = PlotIntervalRunApiCmd(
            garmin_activity_id,
            distance=100,
            n_expected_intervals=[7],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(save_to_png_file_path=FILE_TESTED_PATH.replace(".py", "-100m.png"))

    def test_generate_sample_image_200m(self):
        garmin_activity_id = TEST_ACTIVITIES[2]["garmin_activity_id"]
        p = PlotIntervalRunApiCmd(
            garmin_activity_id,
            distance=200,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(save_to_png_file_path=FILE_TESTED_PATH.replace(".py", "-200m.png"))

    def test_generate_sample_image_300m(self):
        garmin_activity_id = TEST_ACTIVITIES[3]["garmin_activity_id"]
        p = PlotIntervalRunApiCmd(
            garmin_activity_id,
            distance=300,
            n_prev_runs_to_auto_compare=10,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(save_to_png_file_path=FILE_TESTED_PATH.replace(".py", "-300m.png"))

    def test_required_args(self):
        # Required args: garmin_activity_id, distance.
        with pytest.raises(TypeError):
            p = PlotIntervalRunApiCmd(
                # TEST_ACTIVITIES[1]["garmin_activity_id"],
                # distance=1000,
                garmin_connect_token_manager=self.garmin_token_mgr,
            )
        with pytest.raises(TypeError):
            p = PlotIntervalRunApiCmd(
                TEST_ACTIVITIES[1]["garmin_activity_id"],
                # distance=1000,
                garmin_connect_token_manager=self.garmin_token_mgr,
            )
        with pytest.raises(TypeError):
            p = PlotIntervalRunApiCmd(
                # TEST_ACTIVITIES[1]["garmin_activity_id"],
                distance=1000,
                garmin_connect_token_manager=self.garmin_token_mgr,
            )

        p = PlotIntervalRunApiCmd(
            TEST_ACTIVITIES[1]["garmin_activity_id"],
            distance=1000,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_latest_3(self):
        garmin_activity_id = ("LATEST", -3)
        p = PlotIntervalRunApiCmd(
            garmin_activity_id,
            distance=1000,
            n_expected_intervals=[5],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_wrong_distance(self):
        p = PlotIntervalRunApiCmd(
            TEST_ACTIVITIES[1]["garmin_activity_id"],
            distance=300,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        with pytest.raises(NumberOfExpectedIntervalsError):
            p.plot(
                save_to_png_file_path=self.png_file_root
                / f"{inspect.currentframe().f_code.co_qualname}.png"
            )

    def test_not_supported_distance(self):
        with pytest.raises(DistanceNotSupported):
            PlotIntervalRunApiCmd(
                TEST_ACTIVITIES[1]["garmin_activity_id"],
                distance=333,
                garmin_connect_token_manager=self.garmin_token_mgr,
            )

    def test_n_expected_intervals_auto(self):
        p = PlotIntervalRunApiCmd(
            TEST_ACTIVITIES[1]["garmin_activity_id"],
            distance=1000,
            # n_expected_intervals
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_n_expected_intervals_list_single_int(self):
        p = PlotIntervalRunApiCmd(
            TEST_ACTIVITIES[1]["garmin_activity_id"],
            distance=1000,
            n_expected_intervals=[5],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_n_expected_intervals_list(self):
        p = PlotIntervalRunApiCmd(
            TEST_ACTIVITIES[1]["garmin_activity_id"],
            distance=1000,
            n_expected_intervals=[3, 4, 5, 6],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_n_expected_intervals_wrong(self):
        p = PlotIntervalRunApiCmd(
            TEST_ACTIVITIES[1]["garmin_activity_id"],
            distance=1000,
            n_expected_intervals=[3, 4, 6],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        with pytest.raises(NumberOfExpectedIntervalsError):
            p.plot(
                save_to_png_file_path=self.png_file_root
                / f"{inspect.currentframe().f_code.co_qualname}.png"
            )

    def test_prev_runs_activity_ids_to_compare_none(self):
        p = PlotIntervalRunApiCmd(
            TEST_ACTIVITIES[1]["garmin_activity_id"],
            distance=1000,
            prev_runs_activity_ids_to_compare=None,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_prev_runs_activity_ids_to_compare_empty_list(self):
        p = PlotIntervalRunApiCmd(
            TEST_ACTIVITIES[1]["garmin_activity_id"],
            distance=1000,
            prev_runs_activity_ids_to_compare=[],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_prev_runs_activity_ids_to_compare_1(self):
        p = PlotIntervalRunApiCmd(
            TEST_ACTIVITIES[1]["garmin_activity_id"],
            distance=1000,
            prev_runs_activity_ids_to_compare=[22407239690],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_prev_runs_activity_ids_to_compare_2(self):
        p = PlotIntervalRunApiCmd(
            TEST_ACTIVITIES[1]["garmin_activity_id"],
            distance=1000,
            prev_runs_activity_ids_to_compare=[
                22407239690,
                22214365248,
            ],
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_prev_runs_activity_ids_to_compare_or_n_prev_runs_to_auto_compare(self):
        with pytest.raises(IncompatibleArgs):
            PlotIntervalRunApiCmd(
                TEST_ACTIVITIES[1]["garmin_activity_id"],
                distance=1000,
                prev_runs_activity_ids_to_compare=[22407239690],
                n_prev_runs_to_auto_compare=3,
                garmin_connect_token_manager=self.garmin_token_mgr,
            )

    def test_n_previous_activity_to_auto_compare_1(self):
        p = PlotIntervalRunApiCmd(
            22407239690,
            distance=1000,
            n_prev_runs_to_auto_compare=1,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_n_previous_activity_to_auto_compare_0(self):
        p = PlotIntervalRunApiCmd(
            22407239690,
            distance=1000,
            n_prev_runs_to_auto_compare=0,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_n_previous_activity_to_auto_compare_2(self):
        p = PlotIntervalRunApiCmd(
            22407239690,
            distance=1000,
            n_prev_runs_to_auto_compare=2,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_txt_to_search_for_prev_runs_to_auto_compare(self):
        p = PlotIntervalRunApiCmd(
            22407239690,
            distance=1000,
            n_prev_runs_to_auto_compare=2,
            txt_to_search_for_prev_runs_to_auto_compare="5x1000m",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_txt_to_search_for_prev_runs_to_auto_compare_no_results(self):
        p = PlotIntervalRunApiCmd(
            22407239690,
            distance=1000,
            n_prev_runs_to_auto_compare=2,
            txt_to_search_for_prev_runs_to_auto_compare="XXXX",
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_title(self):
        p = PlotIntervalRunApiCmd(
            TEST_ACTIVITIES[1]["garmin_activity_id"],
            distance=1000,
            title="My title",
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )

    def test_figure_size(self):
        p = PlotIntervalRunApiCmd(
            TEST_ACTIVITIES[1]["garmin_activity_id"],
            distance=1000,
            figure_size=(5, 8.5),
        )
        p.plot(
            save_to_png_file_path=self.png_file_root
            / f"{inspect.currentframe().f_code.co_qualname}.png"
        )


class TestPlotInterval300mRunApiFixtures:
    def _get_splits(self, response: ActivityTypedSplitsResponse):
        splits = list()
        for split in response.get_interval_active_splits():
            if abs(split["distance"] - 300) < 3:
                splits.append(split)

        return splits

    def test_merged_activities_6x300m_on_13_03_2025(self):
        """
        On 13/03/2025 I was running a 6x300m, but the watch stopped for an Incident
         Detection while I've just finished the 5th lap.
        It was indeed a false positive, but I had to start a new activity for the
         6th lap. SO I ended up with 2 activities:
        https://connect.garmin.com/modern/activity/18520928352
        https://connect.garmin.com/modern/activity/18520928686
        Now it gets difficult to analyze the data, so I collected all the splits from
         the 2 activities and merged them into one JSON fixture.
        """
        with open(
            ROOT_DIR
            / "fixtures"
            / "garmin-activities-typed-splits-18520928352-and-18520928686-merged.json",
            "r",
        ) as fin:
            data = json.loads(fin.read())
        response = ActivityTypedSplitsResponse(data)
        splits = self._get_splits(response)
        assert len(splits) == 6
        for split in splits:
            assert abs(split["elapsedDuration"] - 50) < 5
