from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)
from strava_client.strava_token_managers import (
    AwsParameterStoreStravaTokenManager,
    FakeTestStravaTokenManager,
)

from sport_analysis.conf import settings
from sport_analysis.conf.settings_module import ROOT_DIR
from sport_analysis.search.search_strava_api.search_strava_api_cmd import (
    SearchStravaApiCmd,
)
from tests.conftest import is_vcr_enabled, is_vcr_record_mode


class ConsoleAdapterMock:
    # Mock the original rich console with this class that collects the output so we
    #  can make assertions.
    def __init__(self):
        self.print_list = list()
        self.print_error_list = list()

    def print(self, *args, **kwargs):
        self.print_list.append(dict(args=args, kwargs=kwargs))

    def print_error(self, *args, **kwargs):
        self.print_error_list.append(dict(args=args, kwargs=kwargs))


class TestSearchStravaApiCmd:
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

    def test_start_date(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before=datetime(
                2025, 9, 2, 23, 59, 59, tzinfo=ZoneInfo("Europe/Rome")
            ),
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 3
        assert (
            "https://www.strava.com/activities/15675847441"
            in mock_console.print_list[0]["args"][0]
        )
        assert (
            "https://www.strava.com/activities/15658059835"
            in mock_console.print_list[1]["args"][0]
        )
        assert (
            "https://www.strava.com/activities/15647482107"
            in mock_console.print_list[2]["args"][0]
        )

    def test_title_contains(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            title_contains="caterina DI VALfur",
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 1
        assert (
            "https://www.strava.com/activities/15647482107"
            in mock_console.print_list[0]["args"][0]
        )

    def test_activity_type(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            activity_type="run",
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 1
        assert (
            "https://www.strava.com/activities/15658059835"
            in mock_console.print_list[0]["args"][0]
        )

    def test_start_latlng(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            start_latlng=(46.411549, 10.499020, 100),
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 1
        assert (
            "https://www.strava.com/activities/15647482107"
            in mock_console.print_list[0]["args"][0]
        )

    def test_end_latlng(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            end_latlng=(45.609540, 9.616726, 100),
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 1
        assert (
            "https://www.strava.com/activities/15658059835"
            in mock_console.print_list[0]["args"][0]
        )

    def test_location_visited_latlng(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            location_visited_latlng=(46.390345, 10.500900, 100),
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 1
        assert (
            "https://www.strava.com/activities/15647482107"
            in mock_console.print_list[0]["args"][0]
        )

    def test_segment_id(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            segment_id=37699613,
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 1
        assert (
            "https://www.strava.com/activities/15647482107"
            in mock_console.print_list[0]["args"][0]
        )
        assert (
            "Segment GAVIA UFFICIALE da S.Caterina"
            in mock_console.print_list[0]["args"][0]
        )

    def test_distance_range(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            distance_range=(20000, 50000),
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 1
        assert (
            "https://www.strava.com/activities/15647482107"
            in mock_console.print_list[0]["args"][0]
        )

    def test_moving_time_range(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            moving_time_range=(60, 120),
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 2
        assert (
            "https://www.strava.com/activities/15675847441"
            in mock_console.print_list[0]["args"][0]
        )
        assert (
            "https://www.strava.com/activities/15647482107"
            in mock_console.print_list[1]["args"][0]
        )

    def test_elapsed_time_range(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            elapsed_time_range=(120, 180),
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 1
        assert (
            "https://www.strava.com/activities/15647482107"
            in mock_console.print_list[0]["args"][0]
        )

    def test_elevation_gain_range(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            elevation_gain_range=(800, 9000),
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 1
        assert (
            "https://www.strava.com/activities/15647482107"
            in mock_console.print_list[0]["args"][0]
        )

    def test_elevation_highest_range(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            elevation_highest_range=(2600, 3000),
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 1
        assert (
            "https://www.strava.com/activities/15647482107"
            in mock_console.print_list[0]["args"][0]
        )

    def test_elevation_lowest_range(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            elevation_lowest_range=(1500, 2000),
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 1
        assert (
            "https://www.strava.com/activities/15647482107"
            in mock_console.print_list[0]["args"][0]
        )

    def test_speed_avg_range(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            speed_avg_range=(14.5, 20.0),
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 1
        assert (
            "https://www.strava.com/activities/15647482107"
            in mock_console.print_list[0]["args"][0]
        )

    def test_speed_max_range(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            speed_max_range=(58.0, 60.0),
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 1
        assert (
            "https://www.strava.com/activities/15647482107"
            in mock_console.print_list[0]["args"][0]
        )

    def test_pace_avg_range(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            pace_avg_range=("5:15", "5:20"),
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 1
        assert (
            "https://www.strava.com/activities/15658059835"
            in mock_console.print_list[0]["args"][0]
        )

    def test_pace_max_range(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            pace_max_range=("3:30", "3:40"),
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 1
        assert (
            "https://www.strava.com/activities/15658059835"
            in mock_console.print_list[0]["args"][0]
        )

    def test_hr_avg_range(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            hr_avg_range=(120, 130),
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 1
        assert (
            "https://www.strava.com/activities/15658059835"
            in mock_console.print_list[0]["args"][0]
        )

    def test_hr_max_range(self):
        s = SearchStravaApiCmd(
            start_date_after="2025-08-31T00:00:00+01:00",
            start_date_before="2025-09-02T23:59:59+01:00",
            hr_max_range=(140, 220),
            strava_token_manager=self.strava_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 1
        assert (
            "https://www.strava.com/activities/15647482107"
            in mock_console.print_list[0]["args"][0]
        )

    def test_do_select_only_if_with_hr_band(self):
        garmin_token_mgr = (
            # Use the regular file token manager when recording vcr episodes.
            FileGarminConnectTokenManager(
                token_file_path=ROOT_DIR / "garmin-connect-token.json"
            )
            if is_vcr_record_mode() or not is_vcr_enabled()
            # And using a fake test token (expiration in 3999) when replaying episodes.
            else FakeTestGarminConnectTokenManager()
        )

        s = SearchStravaApiCmd(
            start_date_after="2025-12-25T00:00:00+01:00",
            do_select_only_if_with_hr_band=True,
            strava_token_manager=self.strava_token_mgr,
            garmin_connect_token_manager=garmin_token_mgr,
        )
        with mock.patch(
            "sport_analysis.search.search_strava_api.search_strava_api_cmd.console",
            ConsoleAdapterMock(),
        ) as mock_console:
            s.search()

        assert len(mock_console.print_list) == 2
        assert (
            "https://www.strava.com/activities/16844998965"
            in mock_console.print_list[0]["args"][0]
        )
        assert (
            "https://www.strava.com/activities/16854219271"
            in mock_console.print_list[1]["args"][0]
        )
