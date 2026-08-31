from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from strava_client import (
    ActivityNotFound,
    AfterTsInTheFuture,
    FilterTypeError,
    NaiveDatetime,
    PossibleDuplicatedActivity,
    RequestedResultsPageDoesNotExist,
    SegmentEffortNotFound,
    SegmentNotFound,
    SportTypeInvalid,
    StravaApiRateLimitExceeded,
    StravaClient,
    StreamNotFound,
)
from strava_client.conf.settings_module import ROOT_DIR
from strava_client.strava_token_managers import (
    AwsParameterStoreStravaTokenManager,
    FakeTestStravaTokenManager,
    FileStravaTokenManager,
)

from .conftest import is_vcr_record_mode

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
        self.token_mgr = (
            # Use AWS Param Store token manager when recording vcr episodes.
            AwsParameterStoreStravaTokenManager(
                TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
                CLIENT_ID_PARAMETER_STORE_KEY_PATH,
                CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            )
            if is_vcr_record_mode()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestStravaTokenManager()
        )

    def test_happy_flow(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            n_results_per_page=3,
        )
        assert len(response.data) == 3
        assert response.data[0]["name"] == "Lunch Run"
        assert response.data[0]["id"] == 14241623406


class TestFileToken:
    def setup_method(self):
        self.token_mgr = (
            # Use AWS Param Store token manager when recording vcr episodes.
            FileStravaTokenManager(
                client_id="XXX",
                client_secret="XXX",
                token_json_file_path=ROOT_DIR / "strava-api-token.json",
            )
            if is_vcr_record_mode()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestStravaTokenManager()
        )

    def test_happy_flow(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            n_results_per_page=3,
        )
        assert len(response.data) == 3
        assert response.data[0]["name"] == "Lunch Run"
        assert response.data[0]["id"] == 14241623406


class TestListActivities:
    def setup_method(self):
        self.token_mgr = (
            # Use AWS Param Store token manager when recording vcr episodes.
            AwsParameterStoreStravaTokenManager(
                TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
                CLIENT_ID_PARAMETER_STORE_KEY_PATH,
                CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            )
            if is_vcr_record_mode()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestStravaTokenManager()
        )

    def test_happy_flow(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            n_results_per_page=3,
        )
        assert len(response.data) == 3
        assert response.data[0]["name"] == "Lunch Run"
        assert response.data[0]["id"] == 14241623406

    def test_after_ts_datetime(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=datetime(2025, 1, 18, 6, 0, 1, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=2,
        )
        assert len(response.data) == 2
        assert response.data[0]["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response.data[0]["id"] == 13389554554

    def test_after_ts_str(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts="2025-01-18T06:00:00+01:00",
            n_results_per_page=2,
        )
        assert len(response.data) == 2
        assert response.data[0]["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response.data[0]["id"] == 13389554554

    def test_after_ts_float(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=datetime(
                2025, 1, 18, 6, 0, 1, tzinfo=ZoneInfo("Europe/Rome")
            ).timestamp(),
            n_results_per_page=2,
        )
        assert len(response.data) == 2
        assert response.data[0]["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response.data[0]["id"] == 13389554554

    def test_after_ts_int(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=int(
                datetime(
                    2025, 1, 18, 6, 0, 1, tzinfo=ZoneInfo("Europe/Rome")
                ).timestamp()
            ),
            n_results_per_page=2,
        )
        assert len(response.data) == 2
        assert response.data[0]["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response.data[0]["id"] == 13389554554

    def test_after_ts_inclusive_timestamp(self):
        after_ts = 1759424400
        activity_id = 16013371380
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=after_ts,
            n_results_per_page=1,
        )
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Weight training: powerlifting"
        assert response.data[0]["id"] == activity_id

    def test_after_ts_inclusive_datetime(self):
        after_ts = datetime(2025, 10, 2, 19, 0, tzinfo=ZoneInfo("Europe/Rome"))
        activity_id = 16013371380
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=after_ts,
            n_results_per_page=1,
        )
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Weight training: powerlifting"
        assert response.data[0]["id"] == activity_id

    def test_after_ts_in_the_future(self):
        client = StravaClient(self.token_mgr.get_access_token())
        with pytest.raises(AfterTsInTheFuture):
            client.list_activities(
                after_ts=datetime(2099, 1, 18, 6, 0, 1, tzinfo=ZoneInfo("Europe/Rome")),
                n_results_per_page=2,
            )

    def test_before_ts_datetime(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 1, 18, 5, 59, 59, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=2,
        )
        assert len(response.data) == 2
        assert response.data[0]["name"] == "Weight training: chest, biceps"
        assert response.data[0]["id"] == 13371865434

    def test_before_ts_str(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts="2025-01-18T05:59:59+01:00",
            n_results_per_page=2,
        )
        assert len(response.data) == 2
        assert response.data[0]["name"] == "Weight training: chest, biceps"
        assert response.data[0]["id"] == 13371865434

    def test_before_ts_float(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(
                2025, 1, 18, 5, 59, 59, tzinfo=ZoneInfo("Europe/Rome")
            ).timestamp(),
            n_results_per_page=2,
        )
        assert len(response.data) == 2
        assert response.data[0]["name"] == "Weight training: chest, biceps"
        assert response.data[0]["id"] == 13371865434

    def test_before_ts_int(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=int(
                datetime(
                    2025, 1, 18, 5, 59, 59, tzinfo=ZoneInfo("Europe/Rome")
                ).timestamp()
            ),
            n_results_per_page=2,
        )
        assert len(response.data) == 2
        assert response.data[0]["name"] == "Weight training: chest, biceps"
        assert response.data[0]["id"] == 13371865434

    def test_before_ts_inclusive_timestamp(self):
        before_ts = 1759424400
        activity_id = 16013371380
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=before_ts,
            n_results_per_page=1,
        )
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Weight training: powerlifting"
        assert response.data[0]["id"] == activity_id

    def test_before_ts_inclusive_datetime(self):
        before_ts = datetime(2025, 10, 2, 19, 0, tzinfo=ZoneInfo("Europe/Rome"))
        activity_id = 16013371380
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=before_ts,
            n_results_per_page=1,
        )
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Weight training: powerlifting"
        assert response.data[0]["id"] == activity_id

    def test_before_ts_in_the_future(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2099, 1, 18, 5, 59, 59, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=2,
        )
        assert len(response.data) == 2

    def test_page_n(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 1, 18, 5, 59, 59, tzinfo=ZoneInfo("Europe/Rome")),
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
                after_ts=datetime(2025, 1, 18, 6, 0, 1, tzinfo=ZoneInfo("Europe/Rome")),
                n_results_per_page=2,
                page_n=99,
            )


class TestListActivitiesResponseFilter:
    def setup_method(self):
        self.token_mgr = (
            # Use AWS Param Store token manager when recording vcr episodes.
            AwsParameterStoreStravaTokenManager(
                TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
                CLIENT_ID_PARAMETER_STORE_KEY_PATH,
                CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            )
            if is_vcr_record_mode()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestStravaTokenManager()
        )

    def test_deprecated_filter_by_activity_type(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            n_results_per_page=10,
            before_ts=datetime(2025, 12, 18, 7, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
        )
        assert len(response.data) == 10

        activities = list(response.filter_by_activity_type("WeightTraining"))
        assert len(activities) == 9
        assert activities[0]["name"] == "Legs plyometrics"
        assert activities[0]["id"] == 16770546210
        assert activities[8]["name"] == "Back, calisthenics"
        assert activities[8]["id"] == 16695233895

    def test_filter_by_title_contains_happy_flow(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            n_results_per_page=10,
            before_ts=datetime(2025, 12, 18, 7, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
        )
        assert len(response.data) == 10

        activities = list(
            response.filter(
                title_contains="back, triceps",
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "Back, triceps, calisthenics"
        assert activities[0]["id"] == 16707730538

    def test_filter_by_title_contains_no_results(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            n_results_per_page=10,
            before_ts=datetime(2025, 12, 18, 7, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
        )
        assert len(response.data) == 10

        activities = list(
            response.filter(
                title_contains="XXX",
            )
        )
        assert len(activities) == 0

    def test_filter_by_activity_type_happy_flow(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            n_results_per_page=10,
            before_ts=datetime(2025, 12, 18, 7, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
        )
        assert len(response.data) == 10

        activities = list(
            response.filter(
                activity_type="WeiGHttraINIng",
            )
        )
        assert len(activities) == 9
        assert activities[0]["name"] == "Legs plyometrics"
        assert activities[0]["id"] == 16770546210
        assert activities[8]["name"] == "Back, calisthenics"
        assert activities[8]["id"] == 16695233895

    def test_filter_by_activity_type_no_results(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            n_results_per_page=10,
            before_ts=datetime(2025, 12, 18, 7, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
        )
        assert len(response.data) == 10

        activities = list(
            response.filter(
                activity_type="XXX",
            )
        )
        assert len(activities) == 0

    def test_filter_by_start_latlng_exact_coords(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=datetime(2025, 11, 23, 7, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=5,
        )
        assert len(response.data) == 5

        activities = list(
            response.filter(
                start_latlng=(45.609162, 9.616743, 0),
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "3x1000m"

    def test_filter_by_start_latlng_no_distance(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=datetime(2025, 11, 23, 7, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=5,
        )
        assert len(response.data) == 5

        activities = list(
            response.filter(
                start_latlng=(45.609162, 9.616743),
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "3x1000m"

    def test_filter_by_start_latlng_no_results_within_that_distance(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=datetime(2025, 11, 23, 7, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=5,
        )
        assert len(response.data) == 5

        activities = list(
            response.filter(
                start_latlng=(45.61, 9.60, 200),
            )
        )
        assert len(activities) == 0

    def test_filter_by_start_latlng_2_results_within_that_distance(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=datetime(2025, 11, 23, 7, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=5,
        )
        assert len(response.data) == 5

        activities = list(
            response.filter(
                start_latlng=(45.61, 9.60, 1500),
            )
        )
        assert len(activities) == 2
        assert activities[0]["name"] == "Tapasciata Osio Sotto"
        assert activities[1]["name"] == "3x1000m"

    def test_filter_by_start_latlng_non_tuple(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=datetime(2025, 11, 23, 7, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=5,
        )
        assert len(response.data) == 5

        with pytest.raises(FilterTypeError):
            list(
                response.filter(
                    start_latlng="XXX",
                )
            )

    def test_filter_by_end_latlng_exact_coords(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=datetime(2025, 11, 23, 7, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=5,
        )
        assert len(response.data) == 5

        activities = list(
            response.filter(
                end_latlng=(45.622294, 9.593923, 0),
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "Tapasciata Osio Sotto"

    def test_filter_by_end_latlng_no_distance(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=datetime(2025, 11, 23, 7, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=5,
        )
        assert len(response.data) == 5

        activities = list(
            response.filter(
                end_latlng=(45.622294, 9.593923),
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "Tapasciata Osio Sotto"

    def test_filter_by_end_latlng_no_results_within_that_distance(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=datetime(2025, 11, 23, 7, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=5,
        )
        assert len(response.data) == 5

        activities = list(
            response.filter(
                end_latlng=(45.61, 9.60, 200),
            )
        )
        assert len(activities) == 0

    def test_filter_by_end_latlng_2_results_within_that_distance(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=datetime(2025, 11, 23, 7, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=5,
        )
        assert len(response.data) == 5

        activities = list(
            response.filter(
                end_latlng=(45.61, 9.60, 1500),
            )
        )
        assert len(activities) == 2
        assert activities[0]["name"] == "Tapasciata Osio Sotto"
        assert activities[1]["name"] == "3x1000m"

    def test_filter_by_end_latlng_non_tuple(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            after_ts=datetime(2025, 11, 23, 7, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=5,
        )
        assert len(response.data) == 5

        with pytest.raises(FilterTypeError):
            list(
                response.filter(
                    end_latlng="XXX",
                )
            )

    def test_filter_by_location_visited_latlng_happy_flow(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 11, 5, 13, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=1,
        )
        assert len(response.data) == 1

        activities = list(
            response.filter(
                location_visited_latlng=(45.616171, 9.616094, 10),
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "Slow run"

    def test_filter_by_location_visited_latlng_no_distance(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 11, 5, 13, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=1,
        )
        assert len(response.data) == 1

        activities = list(
            response.filter(
                location_visited_latlng=(45.616171, 9.616094),
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "Slow run"

    def test_filter_by_location_visited_latlng_2_results_within_that_distance(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 11, 5, 13, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                location_visited_latlng=(45.616171, 9.616094, 10),
            )
        )
        assert len(activities) == 2
        assert activities[0]["name"] == "Slow run"
        assert activities[1]["name"] == "5x1000m 😮‍💨"

    def test_filter_by_location_visited_latlng_non_tuple(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 11, 5, 13, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        with pytest.raises(FilterTypeError):
            list(
                response.filter(
                    location_visited_latlng="XXX",
                )
            )

    def test_filter_by_distance_range_1_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 11, 5, 13, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                distance_range=(9_900, 10_200),
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "Slow run"

    def test_filter_by_distance_range_2_results(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 11, 5, 13, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                distance_range=(9_900, 10_900),
            )
        )
        assert len(activities) == 2
        assert activities[0]["name"] == "Slow run"
        assert activities[1]["name"] == "5x1000m 😮‍💨"

    def test_filter_by_distance_range_no_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 11, 5, 13, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                distance_range=(15_000, 99_000),
            )
        )
        assert len(activities) == 0

    def test_filter_by_distance_range_non_tuple(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 11, 5, 13, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        with pytest.raises(FilterTypeError):
            list(
                response.filter(
                    distance_range="XXX",
                )
            )

    def test_filter_by_elevation_gain_range_1_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                elevation_gain_range=(1_000, 2_000),
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "Cepina - Passo dello Stelvio"

    def test_filter_by_elevation_gain_range_2_results(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                elevation_gain_range=(600, 2_000),
            )
        )
        assert len(activities) == 2
        assert activities[0]["name"] == "Santa Caterina di Valfurva - Passo Gavia"
        assert activities[1]["name"] == "Cepina - Passo dello Stelvio"

    def test_filter_by_elevation_gain_range_no_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                elevation_gain_range=(5_000, 12_000),
            )
        )
        assert len(activities) == 0

    def test_filter_by_elevation_gain_range_non_tuple(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        with pytest.raises(FilterTypeError):
            list(
                response.filter(
                    elevation_gain_range="XXX",
                )
            )

    def test_filter_by_moving_time_range_1_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                moving_time_range=(120, 240),
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "Cepina - Passo dello Stelvio"

    def test_filter_by_moving_time_range_2_results(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                moving_time_range=(90, 240),
            )
        )
        assert len(activities) == 2
        assert activities[0]["name"] == "Santa Caterina di Valfurva - Passo Gavia"
        assert activities[1]["name"] == "Cepina - Passo dello Stelvio"

    def test_filter_by_moving_time_range_no_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                moving_time_range=(240, 360),
            )
        )
        assert len(activities) == 0

    def test_filter_by_moving_time_range_non_tuple(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        with pytest.raises(FilterTypeError):
            list(
                response.filter(
                    moving_time_range="XXX",
                )
            )

    def test_filter_by_elapsed_time_range_1_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                elapsed_time_range=(240, 600),
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "Cepina - Passo dello Stelvio"

    def test_filter_by_elapsed_time_range_2_results(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                elapsed_time_range=(120, 600),
            )
        )
        assert len(activities) == 2
        assert activities[0]["name"] == "Santa Caterina di Valfurva - Passo Gavia"
        assert activities[1]["name"] == "Cepina - Passo dello Stelvio"

    def test_filter_by_elapsed_time_range_no_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                elapsed_time_range=(600, 900),
            )
        )
        assert len(activities) == 0

    def test_filter_by_elapsed_time_range_non_tuple(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        with pytest.raises(FilterTypeError):
            list(
                response.filter(
                    elapsed_time_range="XXX",
                )
            )

    def test_filter_by_elevation_highest_range_1_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                elevation_highest_range=(2700, 7000),
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "Cepina - Passo dello Stelvio"

    def test_filter_by_elevation_highest_range_2_results(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                elevation_highest_range=(2000, 7000),
            )
        )
        assert len(activities) == 2
        assert activities[0]["name"] == "Santa Caterina di Valfurva - Passo Gavia"
        assert activities[1]["name"] == "Cepina - Passo dello Stelvio"

    def test_filter_by_elevation_highest_range_no_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                elevation_highest_range=(7000, 9000),
            )
        )
        assert len(activities) == 0

    def test_filter_by_elevation_highest_range_non_tuple(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        with pytest.raises(FilterTypeError):
            list(
                response.filter(
                    elevation_highest_range="XXX",
                )
            )

    def test_filter_by_elevation_lowest_range_1_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                elevation_lowest_range=(1700, 7000),
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "Santa Caterina di Valfurva - Passo Gavia"

    def test_filter_by_elevation_lowest_range_2_results(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                elevation_lowest_range=(1000, 7000),
            )
        )
        assert len(activities) == 2
        assert activities[0]["name"] == "Santa Caterina di Valfurva - Passo Gavia"
        assert activities[1]["name"] == "Cepina - Passo dello Stelvio"

    def test_filter_by_elevation_lowest_range_no_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                elevation_lowest_range=(7000, 9000),
            )
        )
        assert len(activities) == 0

    def test_filter_by_elevation_lowest_range_non_tuple(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        with pytest.raises(FilterTypeError):
            list(
                response.filter(
                    elevation_lowest_range="XXX",
                )
            )

    def test_filter_by_hr_avg_range_1_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                hr_avg_range=(110, 180),
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "Cepina - Passo dello Stelvio"

    def test_filter_by_hr_avg_range_2_results(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                hr_avg_range=(100, 180),
            )
        )
        assert len(activities) == 2
        assert activities[0]["name"] == "Santa Caterina di Valfurva - Passo Gavia"
        assert activities[1]["name"] == "Cepina - Passo dello Stelvio"

    def test_filter_by_hr_avg_range_no_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                hr_avg_range=(180, 200),
            )
        )
        assert len(activities) == 0

    def test_filter_by_hr_avg_range_non_tuple(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        with pytest.raises(FilterTypeError):
            list(
                response.filter(
                    hr_avg_range="XXX",
                )
            )

    def test_filter_by_speed_avg_range_1_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                speed_avg_range=(14.7, 25.0),
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "Cepina - Passo dello Stelvio"

    def test_filter_by_speed_avg_range_2_results(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                speed_avg_range=(14.5, 25.0),
            )
        )
        assert len(activities) == 2
        assert activities[0]["name"] == "Santa Caterina di Valfurva - Passo Gavia"
        assert activities[1]["name"] == "Cepina - Passo dello Stelvio"

    def test_filter_by_speed_avg_range_no_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                speed_avg_range=(16.0, 25.0),
            )
        )
        assert len(activities) == 0

    def test_filter_by_speed_avg_range_non_tuple(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        with pytest.raises(FilterTypeError):
            list(
                response.filter(
                    speed_avg_range="XXX",
                )
            )

    def test_filter_by_speed_max_range_1_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                speed_max_range=(60.0, 100.0),
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "Cepina - Passo dello Stelvio"

    def test_filter_by_speed_max_range_2_results(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                speed_max_range=(55.5, 100.0),
            )
        )
        assert len(activities) == 2
        assert activities[0]["name"] == "Santa Caterina di Valfurva - Passo Gavia"
        assert activities[1]["name"] == "Cepina - Passo dello Stelvio"

    def test_filter_by_speed_max_range_no_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        activities = list(
            response.filter(
                speed_max_range=(100.0, 200.0),
            )
        )
        assert len(activities) == 0

    def test_filter_by_speed_max_range_non_tuple(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 8, 31, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=4,
        )
        assert len(response.data) == 4

        with pytest.raises(FilterTypeError):
            list(
                response.filter(
                    speed_max_range="XXX",
                )
            )

    def test_filter_by_pace_avg_range_1_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 10, 18, 22, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=3,
        )
        assert len(response.data) == 3

        activities = list(
            response.filter(
                pace_avg_range=("5:30", "5:45"),
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "4x1000m"

    def test_filter_by_pace_avg_range_2_results(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 10, 18, 22, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=3,
        )
        assert len(response.data) == 3

        activities = list(
            response.filter(
                pace_avg_range=("5:30", "6:45"),
            )
        )
        assert len(activities) == 2
        assert activities[0]["name"] == "4x1000m"
        assert activities[1]["name"] == "5x300m"

    def test_filter_by_pace_avg_range_no_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 10, 18, 22, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=3,
        )
        assert len(response.data) == 3

        activities = list(
            response.filter(
                pace_avg_range=("4:10", "4:15"),
            )
        )
        assert len(activities) == 0

    def test_filter_by_pace_avg_range_non_tuple(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 10, 18, 22, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=3,
        )
        assert len(response.data) == 3

        with pytest.raises(FilterTypeError):
            list(
                response.filter(
                    pace_avg_range="XXX",
                )
            )

    def test_filter_by_pace_max_range_1_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 10, 18, 22, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=3,
        )
        assert len(response.data) == 3

        activities = list(
            response.filter(
                pace_max_range=("2:10", "2:20"),
            )
        )
        assert len(activities) == 1
        assert activities[0]["name"] == "5x300m"

    def test_filter_by_pace_max_range_2_results(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 10, 18, 22, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=3,
        )
        assert len(response.data) == 3

        activities = list(
            response.filter(
                pace_max_range=("2:10", "3:20"),
            )
        )
        assert len(activities) == 2
        assert activities[0]["name"] == "4x1000m"
        assert activities[1]["name"] == "5x300m"

    def test_filter_by_pace_max_range_no_result(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 10, 18, 22, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=3,
        )
        assert len(response.data) == 3

        activities = list(
            response.filter(
                pace_max_range=("2:05", "2:07"),
            )
        )
        assert len(activities) == 0

    def test_filter_by_pace_max_range_non_tuple(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            before_ts=datetime(2025, 10, 18, 22, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
            n_results_per_page=3,
        )
        assert len(response.data) == 3

        with pytest.raises(FilterTypeError):
            list(
                response.filter(
                    pace_max_range="XXX",
                )
            )

    def test_2_filters(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            n_results_per_page=10,
            before_ts=datetime(2025, 12, 18, 7, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
        )
        assert len(response.data) == 10

        activities = list(
            response.filter(
                title_contains="back",
                activity_type="WeightTraining",
            )
        )
        assert len(activities) == 4
        assert activities[0]["name"] == "Back, shoulders, calisthenics"
        assert activities[0]["id"] == 16734012247
        assert activities[1]["name"] == "Back, shoulders, calisthenics"
        assert activities[1]["id"] == 16724137676
        assert activities[2]["name"] == "Back, triceps, calisthenics"
        assert activities[2]["id"] == 16707730538
        assert activities[3]["name"] == "Back, calisthenics"
        assert activities[3]["id"] == 16695233895

    def test_no_filter(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.list_activities(
            n_results_per_page=9,
            before_ts=datetime(2025, 12, 18, 7, 0, 0, tzinfo=ZoneInfo("Europe/Rome")),
        )
        assert len(response.data) == 9

        activities = list(response.filter())
        assert len(activities) == 9
        assert activities[0]["name"] == "Legs plyometrics"
        assert activities[0]["id"] == 16770546210
        assert activities[8]["name"] == "Powerlifting class"
        assert activities[8]["id"] == 16697710509


class TestGetActivityDetails:
    def setup_method(self):
        self.token_mgr = (
            # Use AWS Param Store token manager when recording vcr episodes.
            AwsParameterStoreStravaTokenManager(
                TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
                CLIENT_ID_PARAMETER_STORE_KEY_PATH,
                CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            )
            if is_vcr_record_mode()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestStravaTokenManager()
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


class TestGetActivityDetailsSegment:
    def setup_method(self):
        self.token_mgr = (
            # Use AWS Param Store token manager when recording vcr episodes.
            AwsParameterStoreStravaTokenManager(
                TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
                CLIENT_ID_PARAMETER_STORE_KEY_PATH,
                CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            )
            if is_vcr_record_mode()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestStravaTokenManager()
        )

    def test_happy_flow(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_activity_details(13389554554)
        assert response.data["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response.data["id"] == 13389554554
        assert "description" in response.data

        segment_efforts = response.get_segment_efforts(
            [30559592]  # "Pista Blu Dobbiaco"
        )
        assert len(segment_efforts) == 1
        assert segment_efforts[0]["start_index"] == 1130
        assert segment_efforts[0]["end_index"] == 1349
        assert segment_efforts[0]["average_heartrate"] == 129.8

        # Case insensitive.
        response.get_segment_efforts(["pistA BLU dobbiaco"])  # 30559592
        assert len(segment_efforts) == 1

    def test_filter_int(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_activity_details(13389554554)
        assert response.data["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response.data["id"] == 13389554554
        assert "description" in response.data

        segment_efforts = response.get_segment_efforts(
            [30559592]  # "Pista Blu Dobbiaco"
        )
        assert len(segment_efforts) == 1
        assert segment_efforts[0]["start_index"] == 1130
        assert segment_efforts[0]["end_index"] == 1349
        assert segment_efforts[0]["average_heartrate"] == 129.8

    def test_filter_string(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_activity_details(13389554554)
        assert response.data["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response.data["id"] == 13389554554
        assert "description" in response.data

        segment_efforts = response.get_segment_efforts(
            ["Pista Blu Dobbiaco"]  # 30559592
        )
        assert len(segment_efforts) == 1
        assert segment_efforts[0]["start_index"] == 1130
        assert segment_efforts[0]["end_index"] == 1349
        assert segment_efforts[0]["average_heartrate"] == 129.8

    def test_segment_not_found(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_activity_details(13389554554)
        assert response.data["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response.data["id"] == 13389554554
        assert "description" in response.data

        with pytest.raises(SegmentEffortNotFound):
            response.get_segment_efforts([999])
        with pytest.raises(SegmentEffortNotFound):
            response.get_segment_efforts(["XXX"])
        with pytest.raises(SegmentEffortNotFound):
            response.get_segment_efforts(
                [
                    "Pista Blu Dobbiaco",
                    999,
                ]
            )
        with pytest.raises(SegmentEffortNotFound):
            response.get_segment_efforts(
                [
                    "Pista Blu DobbiacoXXX",
                    30559592,
                ]
            )

    def test_no_filter(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_activity_details(13389554554)
        assert response.data["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response.data["id"] == 13389554554
        assert "description" in response.data

        segment_efforts = response.get_segment_efforts()
        assert len(segment_efforts) == 7

    def test_many_segments(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_activity_details(13389554554)
        assert response.data["name"] == "Dobbiaco Winter Night Run 🦠"
        assert response.data["id"] == 13389554554
        assert "description" in response.data

        segment_efforts = response.get_segment_efforts(
            [
                "Pista Blu Dobbiaco",  # 30559592.
                38460423,  # "Winter Night Run 2024".
            ]
        )
        assert len(segment_efforts) == 2

    def test_n_times_same_segment(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_activity_details(13679778676)
        assert response.data["name"] == "6x300m"
        assert response.data["id"] == 13679778676
        assert "description" in response.data

        segment_efforts = response.get_segment_efforts(
            [
                8167025,  # "Via Solferino".
                "300m stazione Levate",  # 38355448.
            ]
        )
        assert len(segment_efforts) == 7
        segment_efforts.sort(key=lambda x: x["id"])
        assert segment_efforts[0]["name"] == "Via Solferino"
        for i in range(1, 6):
            assert segment_efforts[i]["name"] == "300m stazione Levate"


class TestUpdateActivity:
    def setup_method(self):
        self.token_mgr = (
            # Use AWS Param Store token manager when recording vcr episodes.
            AwsParameterStoreStravaTokenManager(
                TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
                CLIENT_ID_PARAMETER_STORE_KEY_PATH,
                CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            )
            if is_vcr_record_mode()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestStravaTokenManager()
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
        self.token_mgr = (
            # Use AWS Param Store token manager when recording vcr episodes.
            AwsParameterStoreStravaTokenManager(
                TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
                CLIENT_ID_PARAMETER_STORE_KEY_PATH,
                CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            )
            if is_vcr_record_mode()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestStravaTokenManager()
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
        assert response.data["id"] == 14261347515
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
        assert response.data["id"] == 14261372946
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
        self.token_mgr = (
            # Use AWS Param Store token manager when recording vcr episodes.
            AwsParameterStoreStravaTokenManager(
                TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
                CLIENT_ID_PARAMETER_STORE_KEY_PATH,
                CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            )
            if is_vcr_record_mode()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestStravaTokenManager()
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
        assert response.compute_moving_time_stream()

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


class TestGetSegment:
    def setup_method(self):
        self.token_mgr = (
            # Use AWS Param Store token manager when recording vcr episodes.
            AwsParameterStoreStravaTokenManager(
                TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
                CLIENT_ID_PARAMETER_STORE_KEY_PATH,
                CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            )
            if is_vcr_record_mode()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestStravaTokenManager()
        )
        self.segment_stelvio = 15756100  # Passo Stelvio (via Bormio).
        self.segment_selvino = 14418673  # Selvino Fontanella.

    def test_stelvio(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_segment(self.segment_stelvio)
        assert response.data["name"] == "Passo Stelvio (via Bormio)"
        assert response.data["id"] == self.segment_stelvio
        assert response.data["start_latlng"] == [46.47783, 10.367602]
        assert response.data["end_latlng"] == [46.52874, 10.452808]
        assert response.data["distance"] == 19481.1
        assert response.data["total_elevation_gain"] == 1467.7
        assert response.data["activity_type"] == "Ride"
        assert "polyline" in response.data["map"]

    def test_selvino(self):
        client = StravaClient(self.token_mgr.get_access_token())
        response = client.get_segment(self.segment_selvino)
        assert response.data["name"] == "Selvino Fontanella"
        assert response.data["id"] == self.segment_selvino
        assert response.data["start_latlng"] == [45.745995, 9.762249]
        assert response.data["end_latlng"] == [45.778911, 9.743986]
        assert response.data["distance"] == 10160.9
        assert response.data["total_elevation_gain"] == 587.9
        assert response.data["activity_type"] == "Ride"
        assert "polyline" in response.data["map"]

    def test_not_found(self):
        client = StravaClient(self.token_mgr.get_access_token())
        with pytest.raises(SegmentNotFound):
            client.get_segment(99999999999956100)


class TestRateLimit:
    def setup_method(self):
        self.token_mgr = (
            # Use AWS Param Store token manager when recording vcr episodes.
            AwsParameterStoreStravaTokenManager(
                TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
                CLIENT_ID_PARAMETER_STORE_KEY_PATH,
                CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            )
            if is_vcr_record_mode()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestStravaTokenManager()
        )

    def test_happy_flow(self):
        client = StravaClient(self.token_mgr.get_access_token())
        with pytest.raises(StravaApiRateLimitExceeded):
            # Any requests will fail after exceeding the API rate limit.
            client.list_activities(
                after_ts=datetime(2025, 1, 18, 6, 0, 1, tzinfo=ZoneInfo("Europe/Rome")),
                n_results_per_page=2,
            )
