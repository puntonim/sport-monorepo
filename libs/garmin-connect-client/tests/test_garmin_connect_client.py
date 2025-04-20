from datetime import datetime

from garmin_connect_client import GarminConnectClient
from garmin_connect_client.garmin_connect_token_managers import (
    FileGarminConnectTokenManager,
)

# IMP: run tests using `do_use_fake_test_token=True`, but record new episodes
#  with `do_use_fake_test_token=False`.


class TestListActivities:
    def test_happy_flow(self):
        client = GarminConnectClient(
            # Note: use do_use_fake_test_token=False when recording new episodes.
            FileGarminConnectTokenManager(do_use_fake_test_token=True)
        )
        response = client.list_activities("2025-03-22")
        activities = list(response.get_activities())
        assert len(activities) == 2
        assert activities[0]["activityId"] == 18603794245
        assert activities[0]["activityName"] == "Strength"
        assert activities[1]["activityId"] == 18606916834
        assert activities[1]["activityName"] == "Limone Piemonte Trail Running"

    def test_datetime(self):
        client = GarminConnectClient(
            # Note: use do_use_fake_test_token=False when recording new episodes.
            FileGarminConnectTokenManager(do_use_fake_test_token=True)
        )
        response = client.list_activities(datetime(2025, 3, 22))
        activities = list(response.get_activities())
        assert len(activities) == 2

        assert activities[0]["activityId"] == 18603794245
        assert activities[0]["activityName"] == "Strength"
        assert activities[1]["activityId"] == 18606916834
        assert activities[1]["activityName"] == "Limone Piemonte Trail Running"


class TestGetActivitySummary:
    def test_happy_flow(self):
        client = GarminConnectClient(
            # Note: use do_use_fake_test_token=False when recording new episodes.
            FileGarminConnectTokenManager(do_use_fake_test_token=True)
        )
        activity_id = 18606916834
        response = client.get_activity_summary(activity_id)
        assert response.data["activityId"] == activity_id
        assert response.data["activityName"] == "Limone Piemonte Trail Running"


class TestGetActivityDetails:
    def test_happy_flow(self):
        client = GarminConnectClient(
            # Note: use do_use_fake_test_token=False when recording new episodes.
            FileGarminConnectTokenManager(do_use_fake_test_token=True)
        )
        activity_id = 18606916834
        response = client.get_activity_details(
            activity_id,
            max_metrics_data_count=50,
            do_include_polyline=False,
            # max_polyline_count: int = 4000,
            do_keep_raw_data=False,
        )
        assert response.activity_id == activity_id
        assert response.original_size == 4179
        assert response.streams_size == 75
        assert len(response.elapsed_time_stream) == 75
        assert len(response.moving_time_stream) == 75
        assert len(response.non_paused_time_stream) == 75
        assert len(response.ts_stream) == 75
        assert len(response.distance_stream) == 75
        assert len(response.speed_stream) == 75
        assert len(response.lat_stream) == 75
        assert len(response.lng_stream) == 75
        assert len(response.altitude_stream) == 75
        assert len(response.heartrate_stream) == 75
        assert response.elapsed_time_stream[3] == 17.0

        for i in range(len(response.elapsed_time_stream)):
            assert response.non_paused_time_stream[i] == response.elapsed_time_stream[i]
