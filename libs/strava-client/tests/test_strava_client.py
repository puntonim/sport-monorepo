from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from strava_client import (
    ActivityNotFound,
    AfterTsInTheFuture,
    NaiveDatetime,
    PossibleDuplicatedActivity,
    RequestedResultsPageDoesNotExist,
    SegmentEffortNotFound,
    SegmentNameMismatch,
    SportTypeInvalid,
    StravaApiRateLimitExceeded,
    StravaClient,
    StreamNotFound,
)
from strava_client.conf.settings_module import ROOT_DIR
from strava_client.strava_token_managers import (
    AwsParameterStoreStravaTokenManager,
    FileStravaTokenManager,
)
from tests.conftest import is_vcr_episode_or_error

# TODO use valid creds only when recording cassettes. Do not commit valid ones.
#  Find valid creds in Parameter Store for the project `strava-facade-api`.
#  Trick: first write your new test copying the setup_method in TestParamStoreToken,
#   then record the new cassette
#   then delete the first few requests to Param Store in the cassette
#   finally replace the setup_method with the one in TestListActivities.
#   Doing so you don't need to write here valid creds.
CLIENT_ID = "XXXid"
CLIENT_SECRET = "XXXsecret"

TOKEN_JSON_PARAMETER_STORE_KEY_PATH = (
    "/strava-facade-api/production/strava-api-token-json"
)
CLIENT_ID_PARAMETER_STORE_KEY_PATH = (
    "/strava-facade-api/production/strava-api-client-id"
)
CLIENT_SECRET_PARAMETER_STORE_KEY_PATH = (
    "/strava-facade-api/production/strava-api-client-secret"
)


class TestParamStoreToken:
    def setup_method(self):
        do_force_skip_refresh_token = True if is_vcr_episode_or_error() else False
        self.token_mgr = AwsParameterStoreStravaTokenManager(
            TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
            CLIENT_ID_PARAMETER_STORE_KEY_PATH,
            CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            # Set `do_force_skip_refresh_token` to False when recording cassettes.
            do_force_skip_refresh_token=do_force_skip_refresh_token,
        )

    def test_happy_flow(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=datetime(2025, 1, 18, 6, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=2,
        )
        assert len(response.data) == 2
        assert response.data[0]["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response.data[0]["id"] == 13389554554


class TestListActivities:
    def setup_method(self):
        do_force_skip_refresh_token = True if is_vcr_episode_or_error() else False
        self.token_mgr = FileStravaTokenManager(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_json_file_path=ROOT_DIR / "strava-api-token.json",
            # Set `do_force_skip_refresh_token` to False when recording cassettes.
            do_force_skip_refresh_token=do_force_skip_refresh_token,
        )

    def test_happy_flow(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            n_results_per_page=3,
        )
        assert len(response.data) == 3
        assert response.data[0]["name"] == "Weight training: biceps 🦠"
        assert response.data[0]["id"] == 13451142175

    def test_after_ts(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=datetime(2025, 1, 18, 6, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=2,
        )
        assert len(response.data) == 2
        assert response.data[0]["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response.data[0]["id"] == 13389554554

    def test_after_ts_in_the_future(self):
        client = StravaClient(self.token_mgr.get_access_token())
        with pytest.raises(AfterTsInTheFuture):
            client.list_activities(
                after_ts=datetime(2099, 1, 18, 6, 0, tzinfo=ZoneInfo("Europe/Rome")),
                n_results_per_page=2,
            )

    def test_before_ts(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 1, 18, 6, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=2,
        )
        assert len(response.data) == 2
        assert response.data[0]["name"] == "Weight training: calisthenics"
        assert response.data[0]["id"] == 13381920990

    def test_before_ts_in_the_future(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2099, 1, 18, 6, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=2,
        )
        assert len(response.data) == 2

    def test_activity_type(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(n_results_per_page=10)
        assert len(response.data) == 10

        activities = list(response.filter_by_activity_type("Run"))
        assert len(activities) == 2
        assert activities[0]["name"] == "Dobbiaco Winter Night Run 🦠"
        assert activities[0]["id"] == 13389554554
        assert activities[1]["name"] == "6x300m"
        assert activities[1]["id"] == 13361068984

    def test_page_n(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 1, 18, 6, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=2,
            page_n=9,
        )
        assert len(response.data) == 2
        assert (
            response.data[0]["name"]
            == "Weight training: ring muscle-up progression day #6, biceps"
        )
        assert response.data[0]["id"] == 13266747846

    def test_page_n_does_not_exist(self):
        client = StravaClient(self.token_mgr.get_access_token())
        with pytest.raises(RequestedResultsPageDoesNotExist):
            client.list_activities(
                after_ts=datetime(2025, 1, 18, 6, 0, tzinfo=ZoneInfo("Europe/Rome")),
                n_results_per_page=2,
                page_n=99,
            )


class TestGetActivityDetails:
    def setup_method(self):
        do_force_skip_refresh_token = True if is_vcr_episode_or_error() else False
        self.token_mgr = FileStravaTokenManager(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_json_file_path=ROOT_DIR / "strava-api-token.json",
            # Set `do_force_skip_refresh_token` to False when recording cassettes.
            do_force_skip_refresh_token=do_force_skip_refresh_token,
        )

    def test_happy_flow(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_activity_details(13389554554)
        assert response.data["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response.data["id"] == 13389554554
        assert "description" in response.data

    def test_not_found(self):
        client = StravaClient(self.token_mgr.get_access_token())
        with pytest.raises(ActivityNotFound):
            client.get_activity_details(99989554554)

    def test_get_segment_efforts(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_activity_details(13389554554)
        assert response.data["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response.data["id"] == 13389554554
        assert "description" in response.data

        segment_efforts = response.get_segment_efforts(
            [(30559592, "Pista Blu Dobbiaco")]
        )
        assert len(segment_efforts) == 1
        assert segment_efforts[0]["start_index"] == 1130
        assert segment_efforts[0]["end_index"] == 1349
        assert segment_efforts[0]["average_heartrate"] == 129.8

        # Case insensitive.
        response.get_segment_efforts([(30559592, "pistA BLU dobbiaco")])
        assert len(segment_efforts) == 1

    def test_get_segment_efforts_not_found(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_activity_details(13389554554)
        assert response.data["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response.data["id"] == 13389554554
        assert "description" in response.data

        with pytest.raises(SegmentEffortNotFound):
            response.get_segment_efforts([(999, "Pista Blu Dobbiaco")])
        with pytest.raises(SegmentNameMismatch):
            response.get_segment_efforts([(30559592, "xxx")])
        with pytest.raises(SegmentEffortNotFound):
            response.get_segment_efforts(
                [
                    (30559592, "Pista Blu Dobbiaco"),
                    (999, "Pista Blu Dobbiaco"),
                ]
            )
        with pytest.raises(SegmentEffortNotFound):
            response.get_segment_efforts(
                [
                    (999, "Pista Blu Dobbiaco"),
                    (30559592, "Pista Blu Dobbiaco"),
                ]
            )

    def test_get_segment_efforts_no_filter(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_activity_details(13389554554)
        assert response.data["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response.data["id"] == 13389554554
        assert "description" in response.data

        segment_efforts = response.get_segment_efforts()
        assert len(segment_efforts) == 7

    def test_get_segment_efforts_many(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_activity_details(13389554554)
        assert response.data["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response.data["id"] == 13389554554
        assert "description" in response.data

        segment_efforts = response.get_segment_efforts(
            [
                (30559592, "Pista Blu Dobbiaco"),
                (38460423, "Winter Night Run 2024"),
            ]
        )
        assert len(segment_efforts) == 2

    def test_get_segment_efforts_n_times_same_segment(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_activity_details(13679778676)
        assert response.data["name"] == "6x300m"
        assert response.data["id"] == 13679778676
        assert "description" in response.data

        segment_efforts = response.get_segment_efforts(
            [
                (8167025, "Via Solferino"),
                (38355448, "300m stazione Levate"),
            ]
        )
        assert len(segment_efforts) == 7
        assert segment_efforts[0]["name"] == "Via Solferino"
        for i in range(1, 6):
            assert segment_efforts[i]["name"] == "300m stazione Levate"


class TestUpdateActivity:
    def setup_method(self):
        do_force_skip_refresh_token = True if is_vcr_episode_or_error() else False
        self.token_mgr = FileStravaTokenManager(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_json_file_path=ROOT_DIR / "strava-api-token.json",
            # Set `do_force_skip_refresh_token` to False when recording cassettes.
            do_force_skip_refresh_token=do_force_skip_refresh_token,
        )

    def test_happy_flow(self):
        client = StravaClient(self.token_mgr.get_access_token())
        data = {
            "name": "test Weight training",
            "description": "bla bla",
        }
        response = client.update_activity(13381920990, data)
        assert response.data["id"] == 13381920990
        assert response.data["name"] == "test Weight training"
        assert response.data["description"] == "bla bla"

    def test_not_found(self):
        client = StravaClient(self.token_mgr.get_access_token())
        data = {"name": "test Weight training"}
        with pytest.raises(ActivityNotFound):
            client.update_activity(99989554554, data)


class TestCreateActivity:
    def setup_method(self):
        do_force_skip_refresh_token = True if is_vcr_episode_or_error() else False
        self.token_mgr = FileStravaTokenManager(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_json_file_path=ROOT_DIR / "strava-api-token.json",
            # Set `do_force_skip_refresh_token` to False when recording cassettes.
            do_force_skip_refresh_token=do_force_skip_refresh_token,
        )

    def test_happy_flow(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.create_activity(
            name="test create 1",
            sport_type="WeightTraining",
            start_date=datetime(2025, 1, 26, 16, 0, tzinfo=timezone.utc),
            duration_seconds=60 * 60,
            description="test create description",
            do_detect_duplicates=False,
        )
        assert response.data["id"] == 13461246226
        assert response.data["name"] == "test create 1"
        assert response.data["description"] == "test create description"

    def test_sport_type_invalid(self):
        client = StravaClient(self.token_mgr.get_access_token())
        with pytest.raises(SportTypeInvalid):
            client.create_activity(
                name="test create 1",
                sport_type="XXX",
                start_date=datetime(2025, 1, 26, 16, 0, tzinfo=timezone.utc),
                duration_seconds=60 * 60,
                description="test create description",
                do_detect_duplicates=False,
            )

    def test_start_date_naive(self):
        client = StravaClient(self.token_mgr.get_access_token())
        with pytest.raises(NaiveDatetime):
            client.create_activity(
                name="test create 1",
                sport_type="XXX",
                start_date=datetime(2025, 1, 26, 16, 0),
                duration_seconds=60 * 60,
                description="test create description",
                do_detect_duplicates=False,
            )

    def test_duplicate(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.create_activity(
            name="test create 1",
            sport_type="WeightTraining",
            start_date=datetime(2025, 1, 26, 16, 0, tzinfo=timezone.utc),
            duration_seconds=60 * 60,
            description="test create description",
            do_detect_duplicates=True,
        )
        assert response.data["id"] == 13461322692
        assert response.data["name"] == "test create 1"
        assert response.data["description"] == "test create description"

        with pytest.raises(PossibleDuplicatedActivity):
            client.create_activity(
                name="test create 2",
                sport_type="WeightTraining",
                start_date=datetime(2025, 1, 26, 17, 10, tzinfo=timezone.utc),
                duration_seconds=60 * 60,
                description="test create description 2",
                do_detect_duplicates=True,
            )


class TestGetStreams:
    def setup_method(self):
        do_force_skip_refresh_token = True if is_vcr_episode_or_error() else False
        self.token_mgr = FileStravaTokenManager(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_json_file_path=ROOT_DIR / "strava-api-token.json",
            # Set `do_force_skip_refresh_token` to False when recording cassettes.
            do_force_skip_refresh_token=do_force_skip_refresh_token,
        )

    def test_happy_flow(self):
        client = StravaClient(self.token_mgr.get_access_token())
        stream_types = [
            "time",
            "distance",
            "latlng",
            "altitude",
            "heartrate",
            "moving",
        ]
        response = client.get_streams(13389554554, stream_types=stream_types)
        assert len(response.data) == 6
        for stream in response.data:
            assert stream["type"] in stream_types
            assert stream["data"]
            assert stream["series_type"] == "distance"
            assert stream["original_size"]
            assert stream["resolution"]
            assert stream["data"]
        assert response.get_moving_stream() == response.data[0]["data"]
        assert response.get_latlng_stream() == response.data[1]["data"]
        assert response.get_distance_stream() == response.data[2]["data"]
        assert response.get_heartrate_stream() == response.data[3]["data"]
        assert response.get_altitude_stream() == response.data[4]["data"]
        assert response.get_elapsed_time_stream() == response.data[5]["data"]
        assert response.get_moving_time_stream()

    def test_single_type(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_streams(13389554554, stream_types=["heartrate"])
        assert len(response.data) == 2
        assert response.get_distance_stream() == response.data[0]["data"]
        assert response.get_heartrate_stream() == response.data[1]["data"]

    def test_stream_not_found(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_streams(13389554554, stream_types=["heartrate"])
        assert len(response.data) == 2
        assert response.get_distance_stream() == response.data[0]["data"]
        assert response.get_heartrate_stream() == response.data[1]["data"]
        with pytest.raises(StreamNotFound):
            response.get_altitude_stream()


class TestRateLimit:
    def setup_method(self):
        do_force_skip_refresh_token = True if is_vcr_episode_or_error() else False
        self.token_mgr = FileStravaTokenManager(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_json_file_path=ROOT_DIR / "strava-api-token.json",
            # Set `do_force_skip_refresh_token` to False when recording cassettes.
            do_force_skip_refresh_token=do_force_skip_refresh_token,
        )

    def test_happy_flow(self):
        client = StravaClient(self.token_mgr.get_access_token())
        with pytest.raises(StravaApiRateLimitExceeded):
            # Any requests will fail after exceeding the API rate limit.
            client.list_activities(
                after_ts=datetime(2025, 1, 18, 6, 0, tzinfo=ZoneInfo("Europe/Rome")),
                n_results_per_page=2,
            )
