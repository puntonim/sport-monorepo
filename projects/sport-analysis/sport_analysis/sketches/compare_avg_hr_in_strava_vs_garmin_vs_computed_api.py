from statistics import mean

from garmin_connect_client import GarminConnectClient
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)
from strava_client import StravaClient
from strava_client.strava_token_managers import (
    AwsParameterStoreStravaTokenManager,
    FakeTestStravaTokenManager,
    FileStravaTokenManager,
)

from ..conf import settings
from ..conf.settings_module import ROOT_DIR


def compare_avg_hr_in_strava_vs_garmin_vs_computed_api(
    strava_activity_id: int,
    garmin_activity_id: int,
    strava_token_manager: (
        AwsParameterStoreStravaTokenManager
        | FileStravaTokenManager
        | FakeTestStravaTokenManager
        | None
    ) = None,
    garmin_connect_token_manager: (
        FileGarminConnectTokenManager | FakeTestGarminConnectTokenManager | None
    ) = None,
):
    """
    The goal of this function is to run some tests to ensure that the avg and max HR
     values reported by Strava (get_activity_details()) and Garmin (get_activity_summary())
     are the same or very close. I also compared them to the values computed from
     the original HR stream.

    Results are great, see tests in tests/sketches/test_compare_avg_hr_in_strava_vs_garmin_vs_computed.py.
     The only big difference is with a special activity (Strava id 13983015686):
     Snowboarding - never paused the watch, but many not moving times.
     Those not moving times are due to the time spent on the ski lift.
    """
    ## Strava.
    strava_token_manager = strava_token_manager or AwsParameterStoreStravaTokenManager(
        settings.TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
        settings.CLIENT_ID_PARAMETER_STORE_KEY_PATH,
        settings.CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
    )
    strava = StravaClient(strava_token_manager.get_access_token())
    response = strava.get_activity_details(strava_activity_id)
    strava_hr_avg = response.data["average_heartrate"]
    strava_hr_max = response.data["max_heartrate"]

    ## Garmin.
    garmin_token_manager = (
        garmin_connect_token_manager
        or FileGarminConnectTokenManager(
            token_file_path=ROOT_DIR / "garmin-connect-token.json"
        )
    )
    garmin = GarminConnectClient(token_manager=garmin_token_manager)
    response = garmin.get_activity_summary(garmin_activity_id)
    garmin_hr_avg = response.summary["averageHR"]
    garmin_hr_max = response.summary["maxHR"]
    garmin_hr_min = response.summary["minHR"]

    ## Computed
    # Compute those values from the streams.
    r2 = garmin.get_activity_details(
        garmin_activity_id,
        max_metrics_data_count=100 * 1000,
        do_include_polyline=False,
        # max_polyline_count: int = 4000,
        do_keep_raw_data=False,
    )
    hr_stream = r2.get_heartrate_stream(do_remove_none_values=True)
    computed_hr_avg = mean(hr_stream)
    computed_hr_max = max(hr_stream)
    computed_hr_min = min(hr_stream)

    diff = abs(strava_hr_avg * 2 - garmin_hr_avg - computed_hr_avg)
    if diff > 6:
        print(
            f"Avg HR mismatch: {strava_hr_avg} vs {garmin_hr_avg} vs {computed_hr_avg} | {round(diff,2)}"
        )
    diff = abs(strava_hr_max * 2 - garmin_hr_max - computed_hr_max)
    if diff > 4:
        print(
            f"Max HR mismatch: {strava_hr_max} vs {garmin_hr_max} vs {computed_hr_max} | {round(diff, 2)}"
        )
    diff = abs(garmin_hr_min - computed_hr_min)
    if diff > 4:
        print(
            f"Min HR mismatch: {garmin_hr_max} vs {computed_hr_max} | {round(diff, 2)}"
        )
