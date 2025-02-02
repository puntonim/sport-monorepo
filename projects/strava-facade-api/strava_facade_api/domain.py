from datetime import datetime
from typing import Optional, Union

import requests
from strava_client.strava_client import (
    InvalidDatetime,
    NaiveDatetime,
    PossibleDuplicatedActivity,
    StravaClient,
)
from strava_client.token_managers.aws_parameter_store_token_manager import (
    AwsParameterStoreTokenManager,
    AwsParameterStoreTokenManagerException,
)

from . import domain_exceptions as exceptions

TOKEN_JSON_PARAMETER_STORE_KEY_PATH = (
    "/strava-facade-api/production/strava-api-token-json"
)
CLIENT_ID_PARAMETER_STORE_KEY_PATH = (
    "/strava-facade-api/production/strava-api-client-id"
)
CLIENT_SECRET_PARAMETER_STORE_KEY_PATH = (
    "/strava-facade-api/production/strava-api-client-secret"
)


def update_activity_description(
    after_ts: Union[int, float],
    before_ts: Union[int, float],
    activity_type: str,
    description: str,
    name: Optional[str] = None,
    do_stop_if_description_not_null=True,
):
    """
    Update the description of an existing Strava activity.
    The activity is found filtering by after and before timestamps and activity
     type (eg. "WeightTraining").

    Args:
        after_ts: timestamp used to filter and find the activity (eg. 1691704800).
        before_ts: timestamp used to filter and find the activity (eg. 1691791199).
        activity_type: used to filter and find the activity (eg. "WeightTraining").
        description: the updated description of the activity.
        name: the updated name (or title) of the activity, optional.
        do_stop_if_description_not_null: if True the update is not performed when
         the existing description is not null, defaults to True.
    """
    token_mgr = AwsParameterStoreTokenManager(
        "/strava-facade-api/production/strava-api-token-json",
        "/strava-facade-api/production/strava-api-client-id",
        "/strava-facade-api/production/strava-api-client-secret",
    )
    try:
        access_token = token_mgr.get_access_token()
    except AwsParameterStoreTokenManagerException as exc:
        raise exceptions.StravaAuthenticationError(str(exc)) from exc

    try:
        strava = StravaClient(access_token)
    except requests.HTTPError as exc:
        raise exceptions.StravaApiError(str(exc)) from exc

    # Get all activities of the given type for the given day.
    activities = strava.list_activities(after_ts, before_ts, activity_type)
    if not activities:
        raise exceptions.NoActivityFound

    # Get the latest of these activities and ensure it has no description.
    latest_activity = activities[0]
    if do_stop_if_description_not_null:
        latest_activity_details = strava.get_activity_details(latest_activity["id"])
        if latest_activity_details["description"]:
            raise exceptions.ActivityAlreadyHasDescription(
                activity_id=latest_activity["id"],
                description=latest_activity_details["description"],
            )

    # Finally update the description.
    data = {"description": description}
    # And the name if given.
    if name:
        data["name"] = name
    updated_activity = strava.update_activity(latest_activity["id"], data)
    return updated_activity


def create_activity(
    name: str,
    activity_type: str,
    start_date: datetime | str,
    duration_seconds: int,
    description: str | None,
):
    """
    Create a new activity.
    It also tries to make sure that this new activity is not a duplicate.

    Args:
        name: the name (or title) of the new activity.
        activity_type: eg. "WeightTraining".
        start_date: non-naive.
        duration_seconds: in seconds.
        description: optional.
    """
    token_mgr = AwsParameterStoreTokenManager(
        "/strava-facade-api/production/strava-api-token-json",
        "/strava-facade-api/production/strava-api-client-id",
        "/strava-facade-api/production/strava-api-client-secret",
    )
    try:
        access_token = token_mgr.get_access_token()
    except AwsParameterStoreTokenManagerException as exc:
        raise exceptions.StravaAuthenticationError(str(exc)) from exc

    try:
        strava = StravaClient(access_token)
    except requests.HTTPError as exc:
        raise exceptions.StravaApiError(str(exc)) from exc

    try:
        activity = strava.create_activity(
            name,
            activity_type,
            start_date,
            duration_seconds,
            description,
            do_detect_duplicates=True,
        )
    except InvalidDatetime as exc:
        raise exceptions.InvalidDatetimeInput(exc.value) from exc
    except NaiveDatetime as exc:
        raise exceptions.NaiveDatetimeInput(exc.value) from exc
    except PossibleDuplicatedActivity as exc:
        raise exceptions.PossibleDuplicatedActivityFound(exc.activity_id) from exc

    return activity
