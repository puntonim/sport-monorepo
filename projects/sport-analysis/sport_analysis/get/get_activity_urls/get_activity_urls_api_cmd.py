from datetime import datetime, timedelta

import log_utils as logger
from garmin_connect_client import (
    GARMIN_ACTIVITY_FOR_SEARCH_FILTER,
    ActivityTypeUnknown,
    GarminConnectClient,
    SearchActivitiesResponse,
)
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)
from strava_client import ListActivitiesResponse, StravaClient
from strava_client.strava_token_managers import (
    AwsParameterStoreStravaTokenManager,
    FakeTestStravaTokenManager,
    FileStravaTokenManager,
)

from ...base_cli_view import ActivityId, ConsoleAdapter
from ...conf import settings
from ...conf.settings_module import ROOT_DIR

console = ConsoleAdapter()


class GetActivityUrlsApiCmd:
    def __init__(
        self,
        activity_id: ActivityId,
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
        Get both Garmin and Strava activity urls, given any id: either Garmin activity
         id or Strava activity id or LATEST or LATEST-3.
        Args:
            activity_id: an ActivityId instance, examples:
             ActivityId.make_from_string("garmin-11313479371")
             ActivityId.make_from_string("g-11313479371")
             ActivityId.make_from_string("strava-9240064780")
             ActivityId.make_from_string("s-9240064780")
             ActivityId.make_from_string("LATEST")
             ActivityId.make_from_string("LATEST-3")
            strava_token_manager: use FakeTestStravaTokenManager when
             replaying VCR episodes.
            garmin_connect_token_manager: use FakeTestGarminConnectTokenManager when
             replaying VCR episodes.
        """
        self.activity_id = activity_id
        self.strava_token_manager = strava_token_manager
        self.garmin_connect_token_manager = garmin_connect_token_manager

    def get(self, do_suppress_logs: bool = False):
        if self.activity_id.garmin_id:
            garmin_id = self.activity_id.garmin_id
            strava_id = search_strava_activity_matching_garmin_activity(
                garmin_id,
                do_suppress_logs=do_suppress_logs,
                strava_token_manager=self.strava_token_manager,
                garmin_connect_token_manager=self.garmin_connect_token_manager,
            )["id"]

        elif self.activity_id.strava_id:
            strava_id = self.activity_id.strava_id
            garmin_id = search_garmin_activity_matching_strava_activity(
                strava_id,
                do_suppress_logs=do_suppress_logs,
                strava_token_manager=self.strava_token_manager,
                garmin_connect_token_manager=self.garmin_connect_token_manager,
            )["activityId"]

        else:  # LATEST or LATEST-3.
            garmin_id = get_latest_garmin_activity(abs(self.activity_id.latest_id))[
                "activityId"
            ]
            strava_id = search_strava_activity_matching_garmin_activity(
                garmin_id,
                do_suppress_logs=do_suppress_logs,
                strava_token_manager=self.strava_token_manager,
                garmin_connect_token_manager=self.garmin_connect_token_manager,
            )["id"]

        console.print(f"🔗 Garmin: https://connect.garmin.com/app/activity/{garmin_id}")
        console.print(f"🔗 Strava: https://www.strava.com/activities/{strava_id}")
        return garmin_id, strava_id


def search_garmin_activity_matching_strava_activity(
    strava_activity_id: int,
    do_suppress_logs: bool = False,
    strava_token_manager: (
        AwsParameterStoreStravaTokenManager
        | FileStravaTokenManager
        | FakeTestStravaTokenManager
        | None
    ) = None,
    garmin_connect_token_manager: (
        FileGarminConnectTokenManager | FakeTestGarminConnectTokenManager | None
    ) = None,
) -> dict:
    """
    Search the matching Garmin activity for the given Strava activity id.

    Args:
        strava_activity_id: eg. 14038286532.
        do_suppress_logs: if True, it does not print any log statement.
        strava_token_manager: use FakeTestStravaTokenManager when
         replaying VCR episodes.
        garmin_connect_token_manager: use FakeTestGarminConnectTokenManager when
         replaying VCR episodes.
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
            if not do_suppress_logs:
                logger.info(f"Matching Garmin activity id: {activity['activityId']}")
                logger.info(
                    f"https://connect.garmin.com/modern/activity/{activity['activityId']}"
                )
            return activity
    if not do_suppress_logs:
        logger.info("Matching Garmin activity not found")
    raise ActivityNotFound("Matching Garmin activity not found")


def search_strava_activity_matching_garmin_activity(
    garmin_activity_id: int,
    do_suppress_logs: bool = False,
    strava_token_manager: (
        AwsParameterStoreStravaTokenManager
        | FileStravaTokenManager
        | FakeTestStravaTokenManager
        | None
    ) = None,
    garmin_connect_token_manager: (
        FileGarminConnectTokenManager | FakeTestGarminConnectTokenManager | None
    ) = None,
) -> dict:
    """
    Search the matching Strava activity for the given Garmin activity id.

    Args:
        garmin_activity_id: eg. 18689027868.
        do_suppress_logs: if True, it does not print any log statement.
        strava_token_manager: use FakeTestStravaTokenManager when
         replaying VCR episodes.
        garmin_connect_token_manager: use FakeTestGarminConnectTokenManager when
         replaying VCR episodes.
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
            if not do_suppress_logs:
                logger.info(f"Matching Strava activity id: {activity['id']}")
                logger.info(f"https://www.strava.com/activities/{activity['id']}")
            return activity
    elif len(response.data) > 1:
        if not do_suppress_logs:
            logger.info(
                "Multiple Strava activities matched the same start timestamp, weird!"
            )
        raise MultipleActivitiesFound(
            "Multiple Strava activities matched the same start timestamp, weird!"
        )
    if not do_suppress_logs:
        logger.info("Matching Strava activity not found")
    raise ActivityNotFound("Matching Strava activity not found")


def get_latest_garmin_activity(
    nth: int = 0,  # The Nth latest, eg. 0 for LATEST, 3 for LATEST-3.
    # One of GARMIN_ACTIVITY_FOR_SEARCH_FILTER in garmin-connect-client.
    activity_type: str | None = None,
    garmin_connect_token_manager: (
        FileGarminConnectTokenManager | FakeTestGarminConnectTokenManager | None
    ) = None,
    do_suppress_logs: bool = False,
) -> dict:
    """
    Get the Nth latest activity, of the given type (eg. "cycling") if given, in Garmin.

    Args:
        nth: the Nth latest, eg. 0 for LATEST, 3 for LATEST-3.
        activity_type: one of GARMIN_ACTIVITY_FOR_SEARCH_FILTER in
         garmin-connect-client. Eg. running, cycling.
        do_suppress_logs: if True, it does not print any log statement.
        garmin_connect_token_manager: use FakeTestGarminConnectTokenManager when
         replaying VCR episodes.
    """
    garmin_token_manager = (
        garmin_connect_token_manager
        or FileGarminConnectTokenManager(
            token_file_path=ROOT_DIR / "garmin-connect-token.json"
        )
    )
    garmin = GarminConnectClient(token_manager=garmin_token_manager)
    kwargs = dict(n_results=abs(nth) + 1)
    if activity_type:
        kwargs["activity_type"] = activity_type
    try:
        response: SearchActivitiesResponse = garmin.search_activities(**kwargs)
    except ActivityTypeUnknown as exc:
        raise GarminActivityTypeUnknown(
            f"Not a valid value for the Garmin activity type filter: {activity_type}\n"
            f"Valid values: {' | '.join(GARMIN_ACTIVITY_FOR_SEARCH_FILTER)}"
        ) from exc
    latest_activity = response.data[-1]
    if not do_suppress_logs:
        logger.info(
            f"LATEST{'-' + str(nth) if nth else ''}"
            f" {activity_type + ' ' if activity_type else ''}Garmin activity:"
            f" https://connect.garmin.com/app/activity/{latest_activity['activityId']}"
        )
    return latest_activity


def get_latest_strava_activity(
    nth: int = 0,  # The Nth latest, eg. 0 for LATEST, 3 for LATEST-3.
    activity_type: str | None = None,  # One of STRAVA_ACTIVITY_TYPES in strava-client.
    do_suppress_logs: bool = False,
    strava_token_manager: (
        AwsParameterStoreStravaTokenManager
        | FileStravaTokenManager
        | FakeTestStravaTokenManager
        | None
    ) = None,
) -> dict:
    """
    Get the Nth latest activity, of the given type (eg. "Ride") if given, in Strava.

    Args:
        nth: the Nth latest, eg. 0 for LATEST, 3 for LATEST-3.
        activity_type: one of STRAVA_ACTIVITY_TYPES in strava-client. Eg. Ride | Run.
        do_suppress_logs: if True, it does not print any log statement.
        strava_token_manager: use FakeTestStravaTokenManager when
         replaying VCR episodes.
    """
    strava = StravaClient(strava_token_manager.get_access_token())
    latest_activity = None

    if not activity_type:
        response: ListActivitiesResponse = strava.list_activities(
            n_results_per_page=abs(nth) + 1,
        )
        latest_activity = response.data[-1]
    else:
        page_n = 1
        i = 0
        while True:
            response: ListActivitiesResponse = strava.list_activities(
                n_results_per_page=100, page_n=page_n
            )
            n = len(response.data)

            for activity in response.filter(activity_type=activity_type):
                if i == nth:
                    latest_activity = activity
                    break
                i += 1

            if latest_activity or n < 100:
                break
            page_n += 1

    if not latest_activity:
        raise ActivityNotFound

    if not do_suppress_logs:
        logger.info(
            f"LATEST{'-' + str(nth) if nth else ''}"
            f" {activity_type + ' ' if activity_type else ''}Strava activity:"
            f" https://www.strava.com/activities/{latest_activity['id']}"
        )
    return latest_activity


class BaseGetActivityUrlsApiCmdException(Exception): ...


class ActivityNotFound(BaseGetActivityUrlsApiCmdException): ...


class MultipleActivitiesFound(BaseGetActivityUrlsApiCmdException): ...


class GarminActivityTypeUnknown(BaseGetActivityUrlsApiCmdException): ...
