import functools
from datetime import datetime

from strava_client import (
    ActivityNotFound,
    AfterTsInTheFuture,
    InvalidDatetime,
    NaiveDatetime,
    PossibleDuplicatedActivity,
    RequestedResultsPageDoesNotExist,
    StravaApiRateLimitExceeded,
    StravaClient,
)
from strava_client.token_managers import (
    AwsParameterStoreTokenManager,
    AwsParameterStoreTokenManagerException,
    BaseTokenManagerException,
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


def handle_strava_api_rate_limit_error(fn):
    @functools.wraps(fn)
    def closure(*args, **kwargs):
        # `self` in the original method.
        # zelf = args[0]
        try:
            return fn(*args, **kwargs)
        except StravaApiRateLimitExceeded as exc:
            raise exceptions.StravaApiRateLimitExceededError from exc

    return closure


@handle_strava_api_rate_limit_error
def list_activities(
    after_ts: int | None = None,
    before_ts: int | None = None,
    activity_type: str | None = None,
    n_results_per_page: int | None = None,
    page_n: int = 1,
) -> list[dict]:
    """
    List activities in Strava.
    The activity is found filtering by after and before timestamps and activity
     type (eg. "WeightTraining").

    Args:
        after_ts: timestamp used to filter and find the activity (eg. 1691704800).
        before_ts: timestamp used to filter and find the activity (eg. 1691791199).
        activity_type: used to filter and find the activity (eg. "WeightTraining").
        n_results_per_page: number of results in each results page (eg. 100).
        page_n: result page number (eg. 2).
    """
    token_mgr = AwsParameterStoreTokenManager(
        "/strava-facade-api/production/strava-api-token-json",
        "/strava-facade-api/production/strava-api-client-id",
        "/strava-facade-api/production/strava-api-client-secret",
    )
    try:
        access_token = token_mgr.get_access_token()
    except (AwsParameterStoreTokenManagerException, BaseTokenManagerException) as exc:
        raise exceptions.StravaAuthenticationError(str(exc)) from exc

    strava = StravaClient(access_token)

    # Get all activities of the given type for the given day.
    try:
        activities: list[dict] = strava.list_activities(
            after_ts,
            before_ts,
            activity_type,
            n_results_per_page,
            page_n,
        )
    # except NaiveDatetime as exc:  # Cannot happen as here the timestamps are ints.
    except RequestedResultsPageDoesNotExist as exc:
        raise exceptions.RequestedResultsPageDoesNotExistInStravaApi(exc.page_n)
    except AfterTsInTheFuture as exc:
        raise exceptions.AfterTsInTheFutureInStravaApi(exc.after_ts)
    return activities


@handle_strava_api_rate_limit_error
def update_activity_description(
    activity_id: int,
    description: str,
    name: str | None = None,
    do_stop_if_description_not_null=True,
):
    """
    Update the description of an existing Strava activity by its id.

    Args:
        activity_id: id of the Strava activity (eg. XXX).
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
    except (AwsParameterStoreTokenManagerException, BaseTokenManagerException) as exc:
        raise exceptions.StravaAuthenticationError(str(exc)) from exc

    strava = StravaClient(access_token)

    # Get the details and ensure it has no description.
    if do_stop_if_description_not_null:
        try:
            activity_details = strava.get_activity_details(activity_id)
        except ActivityNotFound as exc:
            raise exceptions.ActivityNotFoundInStravaApi(activity_id) from exc
        if existing_descr := activity_details.get("description"):
            raise exceptions.ActivityAlreadyHasDescription(
                activity_id=activity_id,
                description=existing_descr,
            )

    # Finally update the description.
    data = {"description": description}
    # And the name if given.
    if name:
        data["name"] = name
    updated_activity = strava.update_activity(activity_id, data)
    return updated_activity


@handle_strava_api_rate_limit_error
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
    except (AwsParameterStoreTokenManagerException, BaseTokenManagerException) as exc:
        raise exceptions.StravaAuthenticationError(str(exc)) from exc

    strava = StravaClient(access_token)

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
