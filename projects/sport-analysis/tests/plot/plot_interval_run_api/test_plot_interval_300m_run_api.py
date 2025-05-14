import json

from garmin_connect_client import ActivityTypedSplitsResponse
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)

from sport_analysis.conf.settings_module import ROOT_DIR
from sport_analysis.plot.plot_interval_run_api.plot_interval_300m_run_api import (
    PlotInterval300mRunApi,
)
from tests.conftest import is_vcr_enabled, is_vcr_record_mode

TEST_ACTIVITIES = [
    # 0.
    dict(
        title="Run - 6x300m",
        strava_activity_id=14273546414,
        garmin_activity_id=18923007987,
        start_date="2025-04-24",
    ),
]


class TestPlotInterval300mRunApi:
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
        plot_6x300m_api = PlotInterval300mRunApi(
            garmin_activity_id,
            # n_previous_activities_to_compare=4,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        plot_6x300m_api.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlotInterval300mRunApi-test_happy_flow.png",
        )

    def test_n_previous_activity_to_compare_1(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        plot_6x300m_api = PlotInterval300mRunApi(
            garmin_activity_id,
            n_previous_activities_to_compare=1,
            # figure_size=(5, 7),
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        plot_6x300m_api.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlotInterval300mRunApi-test_n_previous_activity_to_compare_1.png",
        )

    def test_n_previous_activity_to_compare_2(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        plot_6x300m_api = PlotInterval300mRunApi(
            garmin_activity_id,
            n_previous_activities_to_compare=2,
            # figure_size=(5, 8),
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        plot_6x300m_api.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlotInterval300mRunApi-test_n_previous_activity_to_compare_2.png",
        )

    def test_n_previous_activity_to_compare_0(self):
        garmin_activity_id = TEST_ACTIVITIES[0]["garmin_activity_id"]
        plot_6x300m_api = PlotInterval300mRunApi(
            garmin_activity_id,
            n_previous_activities_to_compare=0,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        plot_6x300m_api.plot(
            save_to_png_file_path=self.png_file_root
            / "TestPlotInterval300mRunApi-test_n_previous_activity_to_compare_0.png",
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
