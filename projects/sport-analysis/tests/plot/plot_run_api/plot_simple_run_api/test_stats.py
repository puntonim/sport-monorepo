import copy

import pandas as pd
import pytest
import speed_utils
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)

from sport_analysis.conf.settings_module import ROOT_DIR
from sport_analysis.plot.base_api import MixinGarminRequestsApi
from sport_analysis.plot.plot_run_api.plot_simple_run_api.stats import (
    compute_stats_for_custom_splits,
)
from tests.conftest import is_vcr_enabled, is_vcr_record_mode

TEST_ACTIVITIES = [
    # 0.
    dict(
        title="Run - Sarnico-Lovere 2025",  # Run length 24.8km.
        strava_activity_id=14299142926,
        garmin_activity_id=18948270166,
        start_date="2025-04-27",
    ),
    # 1.
    dict(
        title="Arenzano Mari e Monti",  # Trail w/ 719m elevation.
        strava_activity_id=20140488707,
        garmin_activity_id=24330701697,
        start_date="2026-09-12",
    ),
]


class TestComputeStatsForCustomSplits:
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

    def test_happy_flow(self):
        details_resp = MixinGarminRequestsApi(
            self.garmin_token_mgr
        )._api_get_activity_details(
            TEST_ACTIVITIES[0]["garmin_activity_id"],
        )
        #           start_distance  end_distance  start_moving_time  end_moving_time  split_hr_avg  split_speed_avg split_speed_avg_str
        # split_id
        # 0               0.000000   4987.770020                0.0           1432.0    142.345946         3.483080                4:47
        # 1            5001.240234   9994.530273             1436.0           2916.0    141.110512         3.373845                4:56
        # 2           10008.860352  14994.480469             2920.0           4397.0    145.310992         3.375504                4:56
        # 3           15005.059570  19994.320312             4401.0           5865.0    149.882834         3.407965                4:53
        # 4           20007.509766  24811.689453             5869.0           7239.0    155.931034         3.506701                4:45
        custom_splits = compute_stats_for_custom_splits(
            distance_stream=details_resp.get_distance_stream(),
            moving_time_stream=details_resp.get_moving_time_stream(),
            hr_stream=details_resp.get_heartrate_stream(),
            splits_distance=5000,
        )

        # Assertions.
        df = pd.DataFrame(
            {
                "moving_time": details_resp.get_moving_time_stream(),
                "distance": details_resp.get_distance_stream(),
                "hr": details_resp.get_heartrate_stream(),
            }
        )
        _ = lambda x: speed_utils.minpkm_base10_to_base60(
            speed_utils.mps_to_minpkm_base10(x)
        )
        # Km 0-5.
        slice = df[df.distance <= 5000]
        a = slice.iloc[0]
        b = slice.iloc[-1]
        split_speed_avg = (b.distance - a.distance) / (b.moving_time - a.moving_time)
        assert custom_splits.iloc[0]["split_speed_avg"] == split_speed_avg
        assert custom_splits.iloc[0]["split_speed_avg_str"] == _(split_speed_avg)
        assert custom_splits.iloc[0]["split_hr_avg"] == slice["hr"].mean()
        assert custom_splits.iloc[0]["start_distance"] == a["distance"]
        assert custom_splits.iloc[0]["end_distance"] == b["distance"]
        assert custom_splits.iloc[0]["start_moving_time"] == a["moving_time"]
        assert custom_splits.iloc[0]["end_moving_time"] == b["moving_time"]
        # Km 5-10.
        slice = df[(df.distance > 5000) & (df.distance <= 10000)]
        a = slice.iloc[0]
        b = slice.iloc[-1]
        split_speed_avg = (b.distance - a.distance) / (b.moving_time - a.moving_time)
        assert custom_splits.iloc[1]["split_speed_avg"] == split_speed_avg
        assert custom_splits.iloc[1]["split_speed_avg_str"] == _(split_speed_avg)
        assert custom_splits.iloc[1]["split_hr_avg"] == slice["hr"].mean()
        assert custom_splits.iloc[1]["start_distance"] == a["distance"]
        assert custom_splits.iloc[1]["end_distance"] == b["distance"]
        assert custom_splits.iloc[1]["start_moving_time"] == a["moving_time"]
        assert custom_splits.iloc[1]["end_moving_time"] == b["moving_time"]
        # Km 10-15.
        slice = df[(df.distance > 10000) & (df.distance <= 15000)]
        a = slice.iloc[0]
        b = slice.iloc[-1]
        split_speed_avg = (b.distance - a.distance) / (b.moving_time - a.moving_time)
        assert custom_splits.iloc[2]["split_speed_avg"] == split_speed_avg
        assert custom_splits.iloc[2]["split_speed_avg_str"] == _(split_speed_avg)
        assert custom_splits.iloc[2]["split_hr_avg"] == slice["hr"].mean()
        assert custom_splits.iloc[2]["start_distance"] == a["distance"]
        assert custom_splits.iloc[2]["end_distance"] == b["distance"]
        assert custom_splits.iloc[2]["start_moving_time"] == a["moving_time"]
        assert custom_splits.iloc[2]["end_moving_time"] == b["moving_time"]
        # Km 15-20.
        slice = df[(df.distance > 15000) & (df.distance <= 20000)]
        a = slice.iloc[0]
        b = slice.iloc[-1]
        split_speed_avg = (b.distance - a.distance) / (b.moving_time - a.moving_time)
        assert custom_splits.iloc[3]["split_speed_avg"] == split_speed_avg
        assert custom_splits.iloc[3]["split_speed_avg_str"] == _(split_speed_avg)
        assert custom_splits.iloc[3]["split_hr_avg"] == slice["hr"].mean()
        assert custom_splits.iloc[3]["start_distance"] == a["distance"]
        assert custom_splits.iloc[3]["end_distance"] == b["distance"]
        assert custom_splits.iloc[3]["start_moving_time"] == a["moving_time"]
        assert custom_splits.iloc[3]["end_moving_time"] == b["moving_time"]
        # Km 20-.
        slice = df[df.distance > 20000]
        a = slice.iloc[0]
        b = slice.iloc[-1]
        split_speed_avg = (b.distance - a.distance) / (b.moving_time - a.moving_time)
        assert custom_splits.iloc[4]["split_speed_avg"] == split_speed_avg
        assert custom_splits.iloc[4]["split_speed_avg_str"] == _(split_speed_avg)
        assert custom_splits.iloc[4]["split_hr_avg"] == slice["hr"].mean()
        assert custom_splits.iloc[4]["start_distance"] == a["distance"]
        assert custom_splits.iloc[4]["end_distance"] == b["distance"]
        assert custom_splits.iloc[4]["start_moving_time"] == a["moving_time"]
        assert custom_splits.iloc[4]["end_moving_time"] == b["moving_time"]

    def test_required_args(self):
        kwargs = dict(
            distance_stream=[0, 1200],
            moving_time_stream=[0, 1200],
            hr_stream=[56, 89],
            split_distance="AUTO",
        )
        for kwarg_name in [
            "distance_stream",
            "moving_time_stream",
            "hr_stream",
            "split_distance",
        ]:
            actual_kwargs = copy.deepcopy(kwargs)
            del actual_kwargs[kwarg_name]
            with pytest.raises(TypeError):
                compute_stats_for_custom_splits(**actual_kwargs)

    def test_split_distance_AUTO_and_len_bigger_15_km(self):
        details_resp = MixinGarminRequestsApi(
            self.garmin_token_mgr
        )._api_get_activity_details(
            TEST_ACTIVITIES[0]["garmin_activity_id"],
        )
        custom_splits = compute_stats_for_custom_splits(
            distance_stream=details_resp.get_distance_stream(segment_end_meters=15_010),
            moving_time_stream=details_resp.get_moving_time_stream(
                segment_end_meters=15_010
            ),
            hr_stream=details_resp.get_heartrate_stream(segment_end_meters=15_010),
            splits_distance="AUTO",
        )

        assert len(custom_splits) == 3  # Splits are 5000m long.
        assert custom_splits.iloc[-1]["start_distance"] - 10_000 <= 9
        assert custom_splits.iloc[-1]["end_distance"] - 15_010 <= 9

    def test_split_distance_AUTO_and_len_smaller_15_km(self):
        details_resp = MixinGarminRequestsApi(
            self.garmin_token_mgr
        )._api_get_activity_details(
            TEST_ACTIVITIES[0]["garmin_activity_id"],
        )
        custom_splits = compute_stats_for_custom_splits(
            distance_stream=details_resp.get_distance_stream(segment_end_meters=14_990),
            moving_time_stream=details_resp.get_moving_time_stream(
                segment_end_meters=14_990
            ),
            hr_stream=details_resp.get_heartrate_stream(segment_end_meters=14_990),
            splits_distance="AUTO",
        )

        assert len(custom_splits) == 7  # Splits are 2000m long.
        assert custom_splits.iloc[-1]["start_distance"] - 12_000 <= 9
        assert custom_splits.iloc[-1]["end_distance"] - 14_990 <= 9

    def test_last_split_less_than_half_split_distance(self):
        details_resp = MixinGarminRequestsApi(
            self.garmin_token_mgr
        )._api_get_activity_details(
            TEST_ACTIVITIES[0]["garmin_activity_id"],
        )
        custom_splits = compute_stats_for_custom_splits(
            distance_stream=details_resp.get_distance_stream(segment_end_meters=4_959),
            moving_time_stream=details_resp.get_moving_time_stream(
                segment_end_meters=4_959
            ),
            hr_stream=details_resp.get_heartrate_stream(segment_end_meters=4_959),
            splits_distance="AUTO",
        )

        assert len(custom_splits) == 2  # Splits are 2000m long.
        assert custom_splits.iloc[-1]["start_distance"] - 2_000 <= 15
        assert custom_splits.iloc[-1]["end_distance"] - 4_959 <= 9

    def test_last_split_more_than_half_split_distance(self):
        details_resp = MixinGarminRequestsApi(
            self.garmin_token_mgr
        )._api_get_activity_details(
            TEST_ACTIVITIES[0]["garmin_activity_id"],
        )
        custom_splits = compute_stats_for_custom_splits(
            distance_stream=details_resp.get_distance_stream(segment_end_meters=5_003),
            moving_time_stream=details_resp.get_moving_time_stream(
                segment_end_meters=5_003
            ),
            hr_stream=details_resp.get_heartrate_stream(segment_end_meters=5_003),
            splits_distance="AUTO",
        )

        assert len(custom_splits) == 3  # Splits are 2000m long.
        assert custom_splits.iloc[-1]["start_distance"] - 4_000 <= 9
        assert custom_splits.iloc[-1]["end_distance"] - 5_003 <= 9
