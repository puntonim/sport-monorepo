import pytest
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)
from strava_client.strava_token_managers import (
    AwsParameterStoreStravaTokenManager,
    FakeTestStravaTokenManager,
)

from sport_analysis.base_cli_view import ActivityId, ValidationError
from sport_analysis.conf import settings
from sport_analysis.conf.settings_module import ROOT_DIR
from sport_analysis.get.get_activity_urls.get_activity_urls_api_cmd import (
    GarminActivityTypeUnknown,
    GetActivityUrlsApiCmd,
    StravaActivityTypeUnknown,
    get_latest_garmin_activity,
    get_latest_strava_activity,
    search_garmin_activity_matching_strava_activity,
    search_strava_activity_matching_garmin_activity,
)
from tests.conftest import is_vcr_enabled, is_vcr_record_mode

TEST_ACTIVITIES = [
    # 0.
    dict(
        title="Bike, Selvino and Salmezza",
        strava_activity_id=14038286532,
        garmin_activity_id=18689027868,
        start_date="2025-03-31",
    ),
    # 1.
    dict(
        title="Bike, Selvino and Salmezza - Selvino record with road bike",
        strava_activity_id=11681601053,
        garmin_activity_id=15974223178,
        start_date="2024-06-18",
    ),
    # 2.
    dict(
        title="Run, Milano21",
        strava_activity_id=10283002244,
        garmin_activity_id=12877651519,
        start_date="2023-11-26",
    ),
    # 3.
    dict(
        title="Bike, 1st Sellaronda - long activity with many pauses",
        strava_activity_id=9240064780,
        garmin_activity_id=11313479371,
        start_date="2023-06-10",
    ),
    # 4.
    dict(
        title="Snowboarding - never paused the watch, but many not moving times",
        strava_activity_id=13983015686,
        garmin_activity_id=18633237715,
        start_date="2025-03-25",
    ),
    # 5.
    # It was a 5x40s but I messed up with the first interval, pressing the
    #  lap button by mistake, so I pressed it again.
    dict(
        title="Bike - Selvino 5x40s",
        strava_activity_id=14211292173,
        garmin_activity_id=18861865288,
        start_date="2025-04-18",
    ),
    # 6.
    dict(
        title="Run - Limone Sunset Running Race",
        strava_activity_id=13956710205,
        garmin_activity_id=18606916834,
        start_date="2025-03-22",
    ),
    # 7.
    dict(
        title="Run - 6x300m",
        strava_activity_id=14273546414,
        garmin_activity_id=18923007987,
        start_date="2025-04-24",
    ),
]


class TestGetActivityUrlsApiCmd:
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

    def test_strava_happy_flow(self):
        for i, activity in enumerate(TEST_ACTIVITIES[:3]):
            s = "strava" if i % 2 == 0 else "s"
            g = GetActivityUrlsApiCmd(
                ActivityId.make_from_string(f"{s}-{activity['strava_activity_id']}")
            )
            matching_activities = g.get(do_suppress_logs=True)
            assert (
                matching_activities.garmin_activity_dict["activityId"]
                == activity["garmin_activity_id"]
            )
            assert (
                matching_activities.strava_activity_dict["id"]
                == activity["strava_activity_id"]
            )

    def test_garmin_happy_flow(self):
        for i, activity in enumerate(TEST_ACTIVITIES[:3]):
            s = "garmin" if i % 2 == 0 else "g"
            g = GetActivityUrlsApiCmd(
                ActivityId.make_from_string(f"{s}-{activity['garmin_activity_id']}")
            )
            matching_activities = g.get(do_suppress_logs=True)
            assert (
                matching_activities.garmin_activity_dict["activityId"]
                == activity["garmin_activity_id"]
            )
            assert (
                matching_activities.strava_activity_dict["id"]
                == activity["strava_activity_id"]
            )

    def test_latest(self):
        g = GetActivityUrlsApiCmd(ActivityId.make_from_string("LATEST"))
        matching_activities = g.get(do_suppress_logs=True)
        assert matching_activities.garmin_activity_dict["activityId"] == 24214377309
        assert matching_activities.strava_activity_dict["id"] == 20009822955

    def test_latest_105(self):
        g = GetActivityUrlsApiCmd(ActivityId.make_from_string("LATEST-105"))
        matching_activities = g.get(do_suppress_logs=True)
        assert matching_activities.garmin_activity_dict["activityId"] == 22796304255
        assert matching_activities.strava_activity_dict["id"] == 18411723846

    def test_latest_run(self):
        g = GetActivityUrlsApiCmd(ActivityId.make_from_string("LATEST-RUN"))
        matching_activities = g.get(do_suppress_logs=True)
        assert matching_activities.garmin_activity_dict["activityId"] == 24222094070
        assert matching_activities.strava_activity_dict["id"] == 20018887172

    def test_latest_ride_5(self):
        g = GetActivityUrlsApiCmd(ActivityId.make_from_string("LATEST-RIDE-5"))
        matching_activities = g.get(do_suppress_logs=True)
        assert matching_activities.garmin_activity_dict["activityId"] == 23421227784
        assert matching_activities.strava_activity_dict["id"] == 19113767592

    def test_activity_type_unknown(self):
        with pytest.raises(ValidationError):
            GetActivityUrlsApiCmd(ActivityId.make_from_string("LATEST-XXX"))


class TestSearchGarminActivityMatchingStravaActivity:
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

    def test_happy_flow(self):
        for activity in TEST_ACTIVITIES[:3]:
            matching_activities = search_garmin_activity_matching_strava_activity(
                activity["strava_activity_id"],
                do_suppress_logs=True,
                strava_token_manager=self.strava_token_mgr,
                garmin_connect_token_manager=self.garmin_token_mgr,
            )
            assert (
                matching_activities.garmin_activity_dict["activityId"]
                == activity["garmin_activity_id"]
            )
            assert (
                matching_activities.strava_activity_dict["id"]
                == activity["strava_activity_id"]
            )


class TestSearchStravaActivityMatchingGarminActivity:
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

    def test_happy_flow(self):
        for activity in TEST_ACTIVITIES[:3]:
            matching_activities = search_strava_activity_matching_garmin_activity(
                activity["garmin_activity_id"],
                do_suppress_logs=True,
                strava_token_manager=self.strava_token_mgr,
                garmin_connect_token_manager=self.garmin_token_mgr,
            )
            assert (
                matching_activities.strava_activity_dict["id"]
                == activity["strava_activity_id"]
            )
            assert (
                matching_activities.garmin_activity_dict["activityId"]
                == activity["garmin_activity_id"]
            )


class TestGetLatestGarminActivity:
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

    def test_latest(self):
        l = get_latest_garmin_activity(
            0, do_suppress_logs=True, garmin_connect_token_manager=self.garmin_token_mgr
        )
        assert l["activityId"] == 24214377309
        assert l["activityName"] == "Strength"

    def test_latest_5(self):
        l = get_latest_garmin_activity(
            5, do_suppress_logs=True, garmin_connect_token_manager=self.garmin_token_mgr
        )
        assert l["activityId"] == 24135607183
        assert l["activityName"] == "Verdellino Running"

    def test_latest_running(self):
        l = get_latest_garmin_activity(
            0,
            activity_type="running",
            do_suppress_logs=True,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        assert l["activityId"] == 24200451254
        assert l["activityName"] == "Verdellino Running"

    def test_latest_cycling_2(self):
        l = get_latest_garmin_activity(
            2,
            activity_type="cycling",
            do_suppress_logs=True,
            garmin_connect_token_manager=self.garmin_token_mgr,
        )
        assert l["activityId"] == 23512339583
        assert l["activityName"] == "Verdellino Mountain Biking"

    def test_activity_type_unknown(self):
        with pytest.raises(GarminActivityTypeUnknown):
            get_latest_garmin_activity(
                2,
                activity_type="XXX",
                do_suppress_logs=True,
                garmin_connect_token_manager=self.garmin_token_mgr,
            )


class TestGetLatestStravaActivity:
    def setup_method(self):
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

    def test_latest(self):
        l = get_latest_strava_activity(
            0, do_suppress_logs=True, strava_token_manager=self.strava_token_mgr
        )
        assert l["id"] == 20009822955
        assert l["name"] == "Legs, calisthenics"

    def test_latest_6(self):
        l = get_latest_strava_activity(
            6, do_suppress_logs=True, strava_token_manager=self.strava_token_mgr
        )
        assert l["id"] == 19921755836
        assert l["name"] == "Slow run: 94% ≤Z2"

    def test_latest_running(self):
        l = get_latest_strava_activity(
            0,
            activity_type="Run",
            do_suppress_logs=True,
            strava_token_manager=self.strava_token_mgr,
        )
        assert l["id"] == 19994208345
        assert l["name"] == "Slow run: 97% ≤Z2"

    def test_latest_cycling_25(self):
        l = get_latest_strava_activity(
            25,
            activity_type="Ride",
            do_suppress_logs=True,
            strava_token_manager=self.strava_token_mgr,
        )
        assert l["id"] == 15502275420
        assert (
            l["name"]
            == "Passo della Presolana - Salto degli Sposi - Vareno - Cima Pora - Rifugio Magnolini - Monte Alto"
        )

    def test_activity_type_unknown(self):
        with pytest.raises(StravaActivityTypeUnknown):
            get_latest_strava_activity(
                2,
                activity_type="XXX",
                do_suppress_logs=True,
                strava_token_manager=self.strava_token_mgr,
            )
