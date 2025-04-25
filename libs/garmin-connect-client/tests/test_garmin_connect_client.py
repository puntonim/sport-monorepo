from datetime import datetime
from statistics import mean

import pytest

from garmin_connect_client import GarminConnectClient
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)

from .conftest import is_vcr_record_mode

TEST_ACTIVITIES = [
    dict(
        title="Bike, Selvino and Salmezza",
        # strava_activity_id=14038286532,
        garmin_activity_id=18689027868,
        start_date="2025-03-31",
    ),
    dict(
        title="Bike, Selvino and Salmezza - Selvino record with road bike",
        # strava_activity_id=11681601053,
        garmin_activity_id=15974223178,
        start_date="2024-06-18",
    ),
    dict(
        title="Run, Milano21",
        # strava_activity_id=10283002244,
        garmin_activity_id=12877651519,
        start_date="2023-11-26",
    ),
    dict(
        title="Bike, 1st Sellaronda - long activity with many pauses",
        # strava_activity_id=9240064780,
        garmin_activity_id=11313479371,
        start_date="2023-06-10",
    ),
    dict(
        title="Snowboarding - never paused the watch, but many not moving times",
        # strava_activity_id=13983015686,
        garmin_activity_id=18633237715,
        start_date="2025-03-25",
    ),
    # It was a 5x40s but I messed up with the first interval, pressing the
    #  lap button by mistake, so I pressed it again.
    dict(
        title="Bike - Selvino 5x40s",
        # strava_activity_id=14211292173,
        garmin_activity_id=18861865288,
        start_date="2025-04-18",
    ),
    dict(
        title="Run - Limone Sunset Running Race",
        # strava_activity_id=13956710205,
        garmin_activity_id=18606916834,
        start_date="2025-03-22",
    ),
]


class TestListActivities:
    def setup_method(self):
        self.token_mgr = (
            # Use the regular file token manager when recording vcr episodes.
            FileGarminConnectTokenManager()
            if is_vcr_record_mode()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestGarminConnectTokenManager()
        )

    def test_happy_flow(self):
        client = GarminConnectClient(self.token_mgr)
        response = client.list_activities("2025-03-22")
        activities = list(response.get_activities())
        assert len(activities) == 2
        assert activities[0]["activityId"] == 18603794245
        assert activities[0]["activityName"] == "Strength"
        assert activities[1]["activityId"] == 18606916834
        assert activities[1]["activityName"] == "Limone Piemonte Trail Running"

    def test_datetime(self):
        client = GarminConnectClient(self.token_mgr)
        response = client.list_activities(datetime(2025, 3, 22))
        activities = list(response.get_activities())
        assert len(activities) == 2

        assert activities[0]["activityId"] == 18603794245
        assert activities[0]["activityName"] == "Strength"
        assert activities[1]["activityId"] == 18606916834
        assert activities[1]["activityName"] == "Limone Piemonte Trail Running"

    def test_ensure_avg_hr_same_as_in_get_activity_summary(self):
        """
        The goal of this test is to ensure that the avg HR
         return by client.list_activities(<date>)
         is the same as the one in client.get_activity_summary(<id>).
        """
        client = GarminConnectClient(self.token_mgr)
        for test_activity in TEST_ACTIVITIES:
            response = client.list_activities(test_activity["start_date"])
            activities = list(response.get_activities())
            found = False
            for a in activities:
                if a["activityId"] == test_activity["garmin_activity_id"]:
                    found = a
                    break
            assert found

            # Get the summary.
            response = client.get_activity_summary(found["activityId"])
            assert found["averageHR"] == response.summary["averageHR"]


class TestGetActivitySummary:
    def setup_method(self):
        self.token_mgr = (
            # Use the regular file token manager when recording vcr episodes.
            FileGarminConnectTokenManager()
            if is_vcr_record_mode()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestGarminConnectTokenManager()
        )

    def test_happy_flow(self):
        client = GarminConnectClient(self.token_mgr)
        activity_id = 18606916834
        response = client.get_activity_summary(activity_id)
        assert response.data["activityId"] == activity_id
        assert response.data["activityName"] == "Limone Piemonte Trail Running"

    def test_ensure_hr_avg_min_max_match_the_computed_from_streams(self):
        """
        The goal of this test is to ensure that the HR avg|max|min returned by
         the method get_activity_summary(<id>)
         are very close to the one I can compute directly from the HR stream dataset.
        """
        client = GarminConnectClient(self.token_mgr)
        for test_activity in TEST_ACTIVITIES:
            activity_id = test_activity["garmin_activity_id"]

            response = client.get_activity_summary(activity_id)
            avg_hr_summary = response.summary["averageHR"]
            max_hr_summary = response.summary["maxHR"]
            min_hr_summary = response.summary["minHR"]

            # Compute those values from the streams.
            response = client.get_activity_details(
                activity_id,
                max_metrics_data_count=100 * 1000,
                do_include_polyline=False,
                # max_polyline_count: int = 4000,
                do_keep_raw_data=False,
            )
            hr_stream = response.get_heartrate_stream(do_remove_none_values=True)
            avg_hr_computed = mean(hr_stream)
            max_hr_computed = max(hr_stream)
            min_hr_computed = min(hr_stream)

            assert abs(avg_hr_summary - avg_hr_computed) < 6
            assert abs(max_hr_summary - max_hr_computed) <= 1
            assert min_hr_summary == min_hr_computed


class TestGetActivityDetails:
    def setup_method(self):
        self.token_mgr = (
            # Use the regular file token manager when recording vcr episodes.
            FileGarminConnectTokenManager()
            if is_vcr_record_mode()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestGarminConnectTokenManager()
        )

    def test_happy_flow(self):
        client = GarminConnectClient(self.token_mgr)
        activity_id = 18606916834
        response = client.get_activity_details(
            activity_id,
            max_metrics_data_count=50,
            do_include_polyline=False,
            # max_polyline_count: int = 4000,
            do_keep_raw_data=False,
        )
        assert response.activity_id == activity_id
        assert response.original_dataset_size == 4179
        assert response.streams_size == 75
        assert len(response.get_elapsed_time_stream()) == 75
        assert len(response.get_moving_time_stream()) == 75
        assert len(response.get_non_paused_time_stream()) == 75
        assert len(response.get_ts_stream()) == 75
        assert len(response.get_distance_stream()) == 75
        assert len(response.get_speed_stream()) == 75
        assert len(response.get_lat_stream()) == 75
        assert len(response.get_lng_stream()) == 75
        assert len(response.get_altitude_stream()) == 75
        assert len(response.get_heartrate_stream()) == 75
        assert response.get_elapsed_time_stream()[3] == 17.0

        for i in range(len(response.get_elapsed_time_stream())):
            assert (
                response.get_non_paused_time_stream()[i]
                == response.get_elapsed_time_stream()[i]
            )

    def test_check_for_none_values_in_streams(self):
        """
        The goal fo this test is to check which streams can contain None values.
        And what I found is that None values can be found in:
            heartrate_stream
            speed_stream
            lat_stream
            lng_stream
        """
        client = GarminConnectClient(self.token_mgr)
        for test_activity in TEST_ACTIVITIES:
            activity_id = test_activity["garmin_activity_id"]
            response = client.get_activity_details(
                activity_id,
                max_metrics_data_count=100 * 1000,
                do_include_polyline=False,
                # max_polyline_count: int = 4000,
                do_keep_raw_data=False,
            )

            for n in response._all_stream_names:
                stream_data = getattr(response, f"get{n}")()
                assert stream_data
                for x in stream_data:
                    try:
                        assert x is not None
                    except AssertionError:
                        if n not in (
                            "_heartrate_stream",
                            "_speed_stream",
                            "_lat_stream",
                            "_lng_stream",
                        ):
                            raise
                        break

    def test_ensure_stream_data_size_match_original_data_size(self):
        client = GarminConnectClient(self.token_mgr)
        for test_activity in TEST_ACTIVITIES:
            activity_id = test_activity["garmin_activity_id"]
            response = client.get_activity_details(
                activity_id,
                max_metrics_data_count=100 * 1000,
                do_include_polyline=False,
                # max_polyline_count: int = 4000,
                do_keep_raw_data=False,
            )

            for n in response._all_stream_names:
                stream_data = getattr(response, f"get{n}")()
                assert stream_data
                assert (
                    len(stream_data)
                    == response.original_dataset_size
                    == response.streams_size
                )


class TestDownloadFitContent:
    def setup_method(self):
        self.token_mgr = (
            # Use the regular file token manager when recording vcr episodes.
            FileGarminConnectTokenManager()
            if is_vcr_record_mode()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestGarminConnectTokenManager()
        )

    def test_happy_flow(self):
        client = GarminConnectClient(self.token_mgr)
        # activity_id = 18606916834  # Limone.
        activity_id = 18861865288  # Selvino 5x40s.
        response = client.download_fit_content(activity_id)
        hr_stream = response.get_stream("heart_rate")
        assert hr_stream

    # Slow tests are skipped by default, but can be run with: pytest -m slow tests/
    @pytest.mark.slow
    def test_ensure_same_data_as_in_get_activity_details(self):
        """
        The goal of this test is to ensure that the method download_fit_content()
         is useless because it returns exactly the same data as get_activity_details()
         which is better because it returns also other data.
        """
        client = GarminConnectClient(self.token_mgr)

        for activity in TEST_ACTIVITIES:
            activity_id = activity["garmin_activity_id"]

            # Get the HR stream with `download_fit_content()`.
            response = client.download_fit_content(activity_id)
            fit_hr_stream = response.get_stream("heart_rate")

            # Get the HR stream with `get_activity_details()`.
            response = client.get_activity_details(
                activity_id,
                max_metrics_data_count=100 * 1000,
                do_include_polyline=False,
            )
            details_hr_stream = response.get_heartrate_stream()
            details_original_dataset_size = response.original_dataset_size
            details_streams_size = response.streams_size

            # Ensure that all streams sizes in `get_activity_details()` are
            #  equal to the original dataset size.
            assert (
                len(details_hr_stream)
                == details_original_dataset_size
                == details_streams_size
            )

            # Remove the None datapoints in the details HR stream.
            details_hr_stream = response.get_heartrate_stream(
                do_remove_none_values=True
            )

            assert fit_hr_stream == details_hr_stream


class TestGetActivitySplits:
    def setup_method(self):
        self.token_mgr = (
            # Use the regular file token manager when recording vcr episodes.
            FileGarminConnectTokenManager()
            if is_vcr_record_mode()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestGarminConnectTokenManager()
        )

    def test_happy_flow(self):
        client = GarminConnectClient(self.token_mgr)
        activity_id = 18923007987  # 6x300m.

        response = client.get_activity_splits(activity_id)

        active_splits = list(response.get_interval_active_splits())

        assert len(active_splits) == 6

        assert active_splits[0]["distance"] == 300
        assert active_splits[0]["elapsedDuration"] == 49.99
        assert active_splits[0]["averageHR"] == 134.0
        assert active_splits[0]["maxHR"] == 160.0

        assert active_splits[5]["distance"] == 300
        assert active_splits[5]["elapsedDuration"] == 54.165
        assert active_splits[5]["averageHR"] == 134.0
        assert active_splits[5]["maxHR"] == 155.0

    def test_count_active_splits(self):
        """
        The goal of this test is to ensure that for some activities, when I never
         pressed the lap button, still have 1 single INTERVAL_ACTIVE split which is
          the whole activity.
        """
        client = GarminConnectClient(self.token_mgr)

        lengths = []
        for activity in TEST_ACTIVITIES:
            response = client.get_activity_splits(activity["garmin_activity_id"])

            active_splits = list(response.get_interval_active_splits())
            lengths.append(len(active_splits))

        assert lengths[0] == 0
        assert lengths[1] == 1
        assert lengths[2] == 1
        assert lengths[3] == 1
        assert lengths[4] == 0
        # It was a 5x40s but I messed up with the first interval, pressing the
        #  lap button by mistake, so I pressed it again.
        assert lengths[5] == 4
        assert lengths[6] == 1
