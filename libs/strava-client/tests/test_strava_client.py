from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from strava_client import (
    ActivityNotFound,
    NaiveDatetime,
    PossibleDuplicatedActivity,
    RequestedResultsPageDoesNotExist,
    SportTypeInvalid,
    StravaClient,
)
from strava_client.conf.settings_module import ROOT_DIR
from strava_client.token_managers import AwsParameterStoreTokenManager, FileTokenManager
from tests.conftest import is_vcr_episode_or_error

# TODO use valid creds only when recording cassettes. Do not commit valid ones.
#  Find valid creds in Parameter Store for the project `strava-facade-api`.
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
        self.token_mgr = AwsParameterStoreTokenManager(
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
        assert len(response) == 2
        assert response[0]["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response[0]["id"] == 13389554554


class TestListActivities:
    def setup_method(self):
        do_force_skip_refresh_token = True if is_vcr_episode_or_error() else False
        self.token_mgr = FileTokenManager(
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
        assert len(response) == 3
        assert response[0]["name"] == "Weight training: biceps 🦠"
        assert response[0]["id"] == 13451142175

    def test_after_ts(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=datetime(2025, 1, 18, 6, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=2,
        )
        assert len(response) == 2
        assert response[0]["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response[0]["id"] == 13389554554

    def test_before_ts(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 1, 18, 6, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=2,
        )
        assert len(response) == 2
        assert response[0]["name"] == "Weight training: calisthenics"
        assert response[0]["id"] == 13381920990

    def test_activity_type(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            activity_type="Run",
            n_results_per_page=10,
        )
        assert len(response) == 2
        assert response[0]["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response[0]["id"] == 13389554554
        assert response[1]["name"] == "6x300m"
        assert response[1]["id"] == 13361068984

    def test_page_n(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 1, 18, 6, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=2,
            page_n=9,
        )
        assert len(response) == 2
        assert (
            response[0]["name"]
            == "Weight training: ring muscle-up progression day #6, biceps"
        )
        assert response[0]["id"] == 13266747846

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
        self.token_mgr = FileTokenManager(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_json_file_path=ROOT_DIR / "strava-api-token.json",
            # Set `do_force_skip_refresh_token` to False when recording cassettes.
            do_force_skip_refresh_token=do_force_skip_refresh_token,
        )

    def test_happy_flow(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_activity_details(13389554554)
        assert response["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response["id"] == 13389554554
        assert "description" in response

    def test_not_found(self):
        client = StravaClient(self.token_mgr.get_access_token())
        with pytest.raises(ActivityNotFound):
            client.get_activity_details(99989554554)


class TestUpdateActivity:
    def setup_method(self):
        do_force_skip_refresh_token = True if is_vcr_episode_or_error() else False
        self.token_mgr = FileTokenManager(
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
        assert response["id"] == 13381920990
        assert response["name"] == "test Weight training"
        assert response["description"] == "bla bla"

    def test_not_found(self):
        client = StravaClient(self.token_mgr.get_access_token())
        data = {"name": "test Weight training"}
        with pytest.raises(ActivityNotFound):
            client.update_activity(99989554554, data)


class TestCreateActivity:
    def setup_method(self):
        do_force_skip_refresh_token = True if is_vcr_episode_or_error() else False
        self.token_mgr = FileTokenManager(
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
        assert response["id"] == 13461246226
        assert response["name"] == "test create 1"
        assert response["description"] == "test create description"

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
        assert response["id"] == 13461322692
        assert response["name"] == "test create 1"
        assert response["description"] == "test create description"

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
        self.token_mgr = FileTokenManager(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_json_file_path=ROOT_DIR / "strava-api-token.json",
            # Set `do_force_skip_refresh_token` to False when recording cassettes.
            do_force_skip_refresh_token=do_force_skip_refresh_token,
        )

    def test_happy_flow(self):
        client = StravaClient(self.token_mgr.get_access_token())
        stream_types = (
            "time",
            "distance",
            "latlng",
            "altitude",
            "heartrate",
        )
        response = client.get_streams(13389554554, stream_types=stream_types)
        assert len(response) == 5
        for stream in response:
            assert stream["type"] in stream_types
            assert stream["data"]
            assert stream["series_type"] == "distance"
            assert stream["original_size"]
            assert stream["resolution"]
            assert stream["data"]

    def test_single_type(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_streams(13389554554, stream_types=["heartrate"])
        assert len(response) == 2
        assert response[0]["type"] == "distance"
        assert response[0]["data"]
        assert response[0]["series_type"] == "distance"
        assert response[0]["original_size"]
        assert response[0]["resolution"]
        assert response[0]["data"]
        assert response[1]["type"] == "heartrate"
        assert response[1]["data"]
        assert response[1]["series_type"] == "distance"
        assert response[1]["original_size"]
        assert response[1]["resolution"]
        assert response[1]["data"]
