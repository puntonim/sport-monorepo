"""
** SPORT MONOREPO: STRAVA CLIENT **
===================================

With Strava token stored to a **local file**:
```py
from pathlib import Path

from strava_client.strava_token_managers import FileStravaTokenManager
from strava_client import StravaClient

# Create the file strava-api-token.json with content similar to:
# {
#     "token_type": "Bearer",
#     "access_token": "XXX",
#     "expires_at": 1737927237,
#     "expires_in": 21600,
#     "refresh_token": "XXX"
# }

token_mgr = FileStravaTokenManager(
    client_id="myclientid",
    client_secret="myclientsecret",
    token_json_file_path=Path() / "strava-api-token.json",
)
client = StravaClient(token_mgr.get_access_token())
response = client.list_activities(
    n_results_per_page=3,
)
assert len(response.data) == 3
assert response.data[0]["name"] == "Weight training: biceps 🦠"
assert response.data[0]["id"] == 13451142175
```

With Strava token, client id and client secret stored in **AWS Parameter Store**:
```py
from datetime import datetime
from zoneinfo import ZoneInfo

from strava_client.strava_token_managers import AwsParameterStoreStravaTokenManager
from strava_client import StravaClient

token_mgr = AwsParameterStoreStravaTokenManager(
    "/strava-facade-api/production/strava-api-token-json",
    "/strava-facade-api/production/strava-api-client-id",
    "/strava-facade-api/production/strava-api-client-secret",
)
client = StravaClient(token_mgr.get_access_token())
response = client.list_activities(
    after_ts=datetime(2025, 1, 18, 6, 0, tzinfo=ZoneInfo("Europe/Rome")),
    n_results_per_page=2,
)
assert len(response.data) == 3
assert response.data[0]["name"] == "Weight training: biceps 🦠"
assert response.data[0]["id"] == 13451142175
```
"""

import functools
from datetime import datetime, timedelta

import log_utils as logger
import requests
from datetime_utils import datetime_utils

from .responses import (
    ActivityDetailsResponse,
    CreatedActivity,
    ListActivitiesResponse,
    StreamsResponse,
    UpdatedActivity,
)

__all__ = [
    "ActivityNotFound",
    "NaiveDatetime",
    "InvalidDatetime",
    "PossibleDuplicatedActivity",
    "RequestedResultsPageDoesNotExist",
    "SportTypeInvalid",
    "StravaClient",
    "StravaApiRateLimitExceeded",
    "AfterTsInTheFuture",
]


def handle_api_rate_limit_error(fn):
    @functools.wraps(fn)
    def closure(*args, **kwargs):
        # `self` in the original method.
        zelf = args[0]  # noqa
        try:
            return fn(*args, **kwargs)
        except requests.exceptions.HTTPError as exc:
            if exc.response.status_code == 429:
                # Handling the Strava API rate limits:
                #  100 requests every 15 minutes: reset at natural 15-minute intervals
                #   corresponding to 0, 15, 30 and 45 minutes after the hour.
                #  1000 per day: resets at midnight UTC.
                #  https://developers.strava.com/docs/rate-limits/
                raise StravaApiRateLimitExceeded from exc
            raise

    return closure


class StravaClient:
    def __init__(self, access_token: str):
        self._access_token = access_token

    @handle_api_rate_limit_error
    def list_activities(
        self,
        after_ts: datetime | int | float | None = None,
        before_ts: datetime | int | float | None = None,
        n_results_per_page: int | None = None,
        page_n: int = 1,
    ) -> ListActivitiesResponse:
        """
        List all my activities and filter by date, as supported by Strava API.

        Raw response data format: see "docs/activity summary.md"

        Docs:
            - Authentication: https://developers.strava.com/docs/authentication/
            - List Athlete Activities API: https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities

        Curl example:
            $ curl "https://www.strava.com/api/v3/athlete/activities?after=1718834400&before=1718920799" \
             -H "Authorization: Bearer XXX"

        Example:
            token_mgr = FileStravaTokenManager(
                client_id="myclientid",
                client_secret="myclientsecret",
                token_json_file_path=Path() / "strava-api-token.json",
            )
            client = StravaClient(self.token_mgr.get_access_token())
            response = client.list_activities(n_results_per_page=10)

            assert len(response.data) == 10
            assert response.data[0]["name"] == "Weight training: biceps 🦠"
            assert response.data[0]["id"] == 13451142175

            activities = list(response.filter_by_activity_type("Run"))
            assert len(activities) == 2
            assert activities[0]["name"] == "Dobbiaco Winter Night Run 🦠"
            assert activities[0]["id"] == 13389554554
            assert activities[1]["name"] == "6x300m"
            assert activities[1]["id"] == 13361068984
        """
        if isinstance(after_ts, datetime):
            if datetime_utils.is_naive(after_ts):
                raise NaiveDatetime(after_ts)
            after_ts = datetime_utils.utc_date_to_timestamp(after_ts)

        if isinstance(before_ts, datetime):
            if datetime_utils.is_naive(before_ts):
                raise NaiveDatetime(before_ts)
            before_ts = datetime_utils.utc_date_to_timestamp(before_ts)

        logger.info("Listing my activities...")
        url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        payload = {}
        if before_ts:
            payload["before"] = int(before_ts)
        if after_ts:
            payload["after"] = int(after_ts)
        if n_results_per_page:
            payload["per_page"] = n_results_per_page
        if page_n != 1:
            payload["page"] = page_n
        response = requests.get(url, headers=headers, params=payload)

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            for err in exc.response.json().get("errors", []):
                if err.get("field", "") == "after" and err.get("code", "") == "future":
                    raise AfterTsInTheFuture(after_ts) from exc
            raise

        return_data = ListActivitiesResponse(response)

        # If the results page requested does not exist:
        if page_n != 1 and return_data.data == []:
            raise RequestedResultsPageDoesNotExist(page_n)

        return return_data

    @handle_api_rate_limit_error
    def get_activity_details(self, activity_id: int) -> ActivityDetailsResponse:
        """
        Get details for the given activity id.
        The response is a class that offers the method `get_segment_effort`
         to get a segment effort data.

        Raw response data format: see "docs/activity details.md"

        Returns:
            responses.ActivityDetails instance with the attribute `data` [dict]
             like described in "docs/activity details.md".
             The response offers the method `get_segment_effort` to get a segment
             effort data.

        Docs:
            - Authentication: https://developers.strava.com/docs/authentication/
            - Get Activity API: https://developers.strava.com/docs/reference/#api-Activities-getActivityById

        Curl example:
            $ curl "https://www.strava.com/api/v3/activities/13389554554" \
             -H "Authorization: Bearer XXX"

        Example:
            token_mgr = FileStravaTokenManager(
                client_id="myclientid",
                client_secret="myclientsecret",
                token_json_file_path=Path() / "strava-api-token.json",
            )
            client = StravaClient(self.token_mgr.get_access_token())
            response = client.get_activity_details(13389554554)
            assert response.data["name"] == "Dobbiaco Winter Night Run 🦠"
            assert response.data["id"] == 13389554554
            assert "description" in response.data
        """
        logger.info(f"Getting activity details for id={activity_id}...")
        url = f"https://www.strava.com/api/v3/activities/{activity_id}"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        response = requests.get(url, headers=headers)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            if exc.response.status_code == 404:
                raise ActivityNotFound(activity_id) from exc
            raise
        return ActivityDetailsResponse(response)

    @handle_api_rate_limit_error
    def update_activity(self, activity_id: int, data: dict) -> UpdatedActivity:
        """
        Update an activity by its id.

        Docs:
            - Authentication: https://developers.strava.com/docs/authentication/
            - Update Activity API: https://developers.strava.com/docs/reference/#api-Activities-updateActivityById

        Example:
            token_mgr = FileStravaTokenManager(
                client_id="myclientid",
                client_secret="myclientsecret",
                token_json_file_path=Path() / "strava-api-token.json",
            )
            client = StravaClient(self.token_mgr.get_access_token())
            data = {
                "name": "test Weight training",
                "description": "bla bla",
            }
            response = client.update_activity(13381920990, data)
            assert response.data["id"] == 13381920990
            assert response.data["name"] == "test Weight training"
            assert response.data["description"] == "bla bla"
        """
        logger.info(f"Updating activity id={activity_id}...")
        url = f"https://www.strava.com/api/v3/activities/{activity_id}"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        response = requests.put(url, headers=headers, data=data)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            if exc.response.status_code == 404:
                raise ActivityNotFound(activity_id) from exc
            raise
        return UpdatedActivity(response)

    @handle_api_rate_limit_error
    def create_activity(
        self,
        name: str,
        sport_type: str,
        start_date: datetime | str,
        duration_seconds: int,  # Seconds.
        description: str | None,
        do_detect_duplicates=False,
    ) -> CreatedActivity:
        """
        Create a new activity.
        It also tries to make sure that this new activity is not a duplicate.

        Docs:
            - Authentication: https://developers.strava.com/docs/authentication/
            - Create Activity API: https://developers.strava.com/docs/reference/#api-Activities-createActivity

        Example:
            token_mgr = FileStravaTokenManager(
                client_id="myclientid",
                client_secret="myclientsecret",
                token_json_file_path=Path() / "strava-api-token.json",
            )
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
        """
        logger.info(f"Creating new activity...")

        # Parse start_date.
        if isinstance(start_date, str):
            try:
                start_date = datetime_utils.iso_string_to_date(start_date)
            except ValueError as exc:
                raise InvalidDatetime(start_date) from exc

        if isinstance(start_date, datetime):
            if datetime_utils.is_naive(start_date):
                raise NaiveDatetime(start_date)
        else:
            raise InvalidDatetime(start_date)
        start_date_local = start_date.isoformat()

        # Try to detect if there is already a duplicate, so an existing activity
        #  of the same type within 1 hour and 15 mins.
        if do_detect_duplicates:
            after_ts = (start_date - timedelta(hours=1, minutes=15)).timestamp()
            before_ts = (start_date + timedelta(hours=1, minutes=15)).timestamp()
            response = self.list_activities(after_ts, before_ts)
            activities = list(response.filter_by_activity_type(sport_type))
            if activities:
                logger.info(f"Found possible duplicate: {activities[0]['id']}")
                raise PossibleDuplicatedActivity(activities[0]["id"])

        url = f"https://www.strava.com/api/v3/activities"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        data = dict(
            name=name,
            sport_type=sport_type,
            start_date_local=start_date_local,
            elapsed_time=duration_seconds,
        )
        if description:
            data["description"] = description
        response = requests.post(url, headers=headers, data=data)

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            if (
                response.status_code == 409
                and "conflict for url" in exc.args[0].lower()
            ):
                raise PossibleDuplicatedActivity from exc
            else:
                for err in exc.response.json().get("errors", []):
                    if (
                        err.get("field", "") == "sport_type"
                        and err.get("code", "") == "invalid"
                    ):
                        raise SportTypeInvalid(sport_type) from exc
            raise

        return CreatedActivity(response)

    @handle_api_rate_limit_error
    def get_streams(self, activity_id: int, stream_types: list[str]) -> StreamsResponse:
        """
        Get streams for the given activity id.
        Supported stream types: time, distance, latlng, altitude, heartrate.
        Full list of stream types: https://developers.strava.com/docs/reference/#api-models-StreamSet

        Raw response data format: see "docs/streams.md"

        Docs:
            - Authentication: https://developers.strava.com/docs/authentication/
            - Get Activity Streams API: https://developers.strava.com/docs/reference/#api-Streams-getActivityStreams

        Curl example:
            $ curl "https://www.strava.com/api/v3/activities/13389554554/streams?keys=time,heartrate" \
             -H "Authorization: Bearer XXX"

        Example:
            token_mgr = FileStravaTokenManager(
                client_id="myclientid",
                client_secret="myclientsecret",
                token_json_file_path=Path() / "strava-api-token.json",
            )
            client = StravaClient(self.token_mgr.get_access_token())
            response = client.get_streams(13389554554, stream_types=stream_types)
            assert len(response.data) == 6
            assert response.get_elapsed_time_stream()[6] == 134.6
        """
        # Full list of stream types:
        #  https://developers.strava.com/docs/reference/#api-models-StreamSet
        for stream_type in stream_types:
            if stream_type not in (
                "time",
                "distance",
                "latlng",
                "altitude",
                "heartrate",
                "moving",  # True if the athlete was moving.
            ):
                raise InvalidStreamType(stream_type)

        logger.info(f"Getting streams for activity id={activity_id}...")
        url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams?keys={','.join(stream_types)}"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        response = requests.get(url, headers=headers)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            if exc.response.status_code == 404:
                raise ActivityNotFound(activity_id) from exc
            raise
        return StreamsResponse(response)


class BaseStravaClientException(Exception):
    pass


class InvalidDatetime(BaseStravaClientException):
    def __init__(self, value):
        self.value = value


class NaiveDatetime(BaseStravaClientException):
    def __init__(self, value):
        self.value = value


class ActivityNotFound(BaseStravaClientException):
    def __init__(self, activity_id):
        self.activity_id = activity_id


class PossibleDuplicatedActivity(BaseStravaClientException):
    def __init__(self, activity_id: str | None = None):
        self.activity_id = activity_id


class SportTypeInvalid(BaseStravaClientException):
    def __init__(self, sport_type: str):
        self.sport_type = sport_type


class RequestedResultsPageDoesNotExist(BaseStravaClientException):
    def __init__(self, page_n: int):
        self.page_n = page_n


class InvalidStreamType(BaseStravaClientException):
    def __init__(self, stream_type: str):
        self.stream_type = stream_type


class AfterTsInTheFuture(BaseStravaClientException):
    def __init__(self, after_ts):
        self.after_ts = after_ts


class StravaApiRateLimitExceeded(BaseStravaClientException):
    def __init__(self):
        self.ts = datetime.now().astimezone()
        # Strava API rate limits:
        #  100 requests every 15 minutes: reset at natural 15-minute intervals
        #   corresponding to 0, 15, 30 and 45 minutes after the hour.
        #  1000 per day: resets at midnight UTC.
        #  https://developers.strava.com/docs/rate-limits/

        # Find the next minute divisible by 15 (so 0, 15, 30 and 45 min after the hour).
        for i in range(1, 16):
            self.reset_ts = self.ts + timedelta(minutes=i)
            if self.reset_ts.minute % 15 == 0:
                self.reset_ts = self.reset_ts.replace(second=0, microsecond=0)
                break

        self.msg = (
            f"You *probably* exceeded Strava API rate limit of 100 requests per 15 mins.\n"
            f" You must wait until the natural 15-min interval corresponding to 0, 15,"
            f" 30 and 45 minutes after the hour.\n"
            f" You hit the limit at: {self.ts.isoformat()}\n"
            f" And must wait until: {self.reset_ts.isoformat()}\n"
            f" You also *might* have exceeded the daily limit of 1000 requests that"
            f" resets at midnight UTC.\n"
            f" Docs: https://developers.strava.com/docs/rate-limits/"
        )
        super().__init__(self.msg)
