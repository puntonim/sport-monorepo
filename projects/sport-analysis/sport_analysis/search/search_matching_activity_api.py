from datetime import datetime, timedelta

import click
import log_utils as logger
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

from ..base_cli_view import BaseClickCommand
from ..conf import settings
from ..conf.settings_module import ROOT_DIR


@click.command(cls=BaseClickCommand, name="search-matching-garmin-activity")
@click.argument("strava-activity-id", nargs=1, type=int)
def search_garmin_activity_matching_strava_activity_api_cli_view(
    strava_activity_id: int,
) -> dict:
    """
    Search the matching Garmin activity for the given Strava activity id.
    """
    return search_garmin_activity_matching_strava_activity_api(strava_activity_id)


def search_garmin_activity_matching_strava_activity_api(
    strava_activity_id: int,
    strava_token_manager: (
        AwsParameterStoreStravaTokenManager
        | FileStravaTokenManager
        | FakeTestStravaTokenManager
        | None
    ) = None,
    garmin_connect_token_manager: (
        FileGarminConnectTokenManager | FakeTestGarminConnectTokenManager | None
    ) = None,
    do_suppress_logs_for_happy_case: bool = False,
) -> dict:
    """
    Search the matching Garmin activity for the given Strava activity id.

    Args:
        strava_activity_id: eg. 14038286532.
        strava_token_manager: use FakeTestStravaTokenManager when
         replaying VCR episodes.
        garmin_connect_token_manager: use FakeTestGarminConnectTokenManager when
         replaying VCR episodes.
        do_suppress_logs_for_happy_case: if True, it does not print any log statement
         in the happy case, so when the activity is found.
    """
    strava_token_manager = strava_token_manager or AwsParameterStoreStravaTokenManager(
        settings.TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
        settings.CLIENT_ID_PARAMETER_STORE_KEY_PATH,
        settings.CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
    )
    strava = StravaClient(strava_token_manager.get_access_token())
    response = strava.get_activity_details(strava_activity_id)
    start_date_strava = datetime.fromisoformat(response.data["start_date"])  # GMT.

    garmin_token_manager = (
        garmin_connect_token_manager
        or FileGarminConnectTokenManager(
            token_file_path=ROOT_DIR / "garmin-connect-token.json"
        )
    )
    garmin = GarminConnectClient(token_manager=garmin_token_manager)
    response = garmin.list_activities(start_date_strava)
    for activity in response.get_activities():
        start_date_garmin = datetime.fromisoformat(activity["startTimeGMT"] + "+00:00")
        # If the start ts are very close (less than 1 min), match found.
        if abs((start_date_strava - start_date_garmin).total_seconds()) < 60:
            if not do_suppress_logs_for_happy_case:
                logger.info(f"Matching Garmin activity id: {activity['activityId']}")
                logger.info(
                    f"https://connect.garmin.com/modern/activity/{activity['activityId']}"
                )
            return activity
    logger.info("Matching Garmin activity not found")
    raise ActivityNotFound("Matching Garmin activity not found")


@click.command(cls=BaseClickCommand, name="search-matching-strava-activity")
@click.argument("garmin-activity-id", nargs=1, type=int)
def search_strava_activity_matching_garmin_activity_api_cli_view(
    garmin_activity_id: int,
) -> dict:
    """
    Search the matching Strava activity for the given Garmin activity id.
    """
    return search_strava_activity_matching_garmin_activity_api(garmin_activity_id)


def search_strava_activity_matching_garmin_activity_api(
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
    do_suppress_logs_for_happy_case: bool = False,
) -> dict:
    """
    Search the matching Strava activity for the given Garmin activity id.

    Args:
        garmin_activity_id: eg. 18689027868.
        strava_token_manager: use FakeTestStravaTokenManager when
         replaying VCR episodes.
        garmin_connect_token_manager: use FakeTestGarminConnectTokenManager when
         replaying VCR episodes.
        do_suppress_logs_for_happy_case: if True, it does not print any log statement
         in the happy case, so when the activity is found.
    """
    garmin_token_manager = (
        garmin_connect_token_manager
        or FileGarminConnectTokenManager(
            token_file_path=ROOT_DIR / "garmin-connect-token.json"
        )
    )
    garmin = GarminConnectClient(token_manager=garmin_token_manager)
    response = garmin.get_activity_summary(garmin_activity_id)
    start_date_garmin = datetime.fromisoformat(
        response.data["summaryDTO"]["startTimeGMT"] + "+00:00"
    )

    strava_token_manager = strava_token_manager or AwsParameterStoreStravaTokenManager(
        settings.TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
        settings.CLIENT_ID_PARAMETER_STORE_KEY_PATH,
        settings.CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
    )
    strava = StravaClient(strava_token_manager.get_access_token())
    response = strava.list_activities(
        after_ts=start_date_garmin - timedelta(seconds=5 * 60),
        before_ts=start_date_garmin + timedelta(seconds=5 * 60),
        n_results_per_page=1,
    )

    if len(response.data) == 1:
        activity = response.data[0]
        start_date_strava = datetime.fromisoformat(activity["start_date"])
        # If the start ts are very close (less than 1 min), match found.
        if abs((start_date_strava - start_date_garmin).total_seconds()) < 60:
            if not do_suppress_logs_for_happy_case:
                logger.info(f"Matching Strava activity id: {activity['id']}")
                logger.info(f"https://www.strava.com/activities/{activity['id']}")
            return activity
    elif len(response.data) > 1:
        logger.info(
            "Multiple Strava activities matched the same start timestamp, weird!"
        )
        raise MultipleActivitiesFound(
            "Multiple Strava activities matched the same start timestamp, weird!"
        )
    logger.info("Matching Strava activity not found")
    raise ActivityNotFound("Matching Strava activity not found")


class BaseApiFunctionsException(Exception):
    pass


class ActivityNotFound(BaseApiFunctionsException):
    pass


class MultipleActivitiesFound(BaseApiFunctionsException):
    pass
