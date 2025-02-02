"""
** STRAVA MONOREPO: STRAVA CLIENT **
====================================

With Strava token stored to a **local file**:
```py
from pathlib import Path

from strava_client.token_managers import FileTokenManager
from strava_client import StravaClient

# Create the file strava-api-token.json with content similar to:
# {
#     "token_type": "Bearer",
#     "access_token": "XXX",
#     "expires_at": 1737927237,
#     "expires_in": 21600,
#     "refresh_token": "XXX"
# }

token_mgr = FileTokenManager(
    client_id="myclientid",
    client_secret="myclientsecret",
    token_json_file_path=Path() / "strava-api-token.json",
)
client = StravaClient(token_mgr.get_access_token())
response = client.list_activities(
    n_results_per_page=3,
)
assert len(response) == 3
assert response[0]["name"] == "Weight training: biceps 🦠"
assert response[0]["id"] == 13451142175
```

With Strava token, client id and client secret stored in **AWS Parameter Store**:
```py
from datetime import datetime
from zoneinfo import ZoneInfo

from strava_client.token_managers import AwsParameterStoreTokenManager
from strava_client import StravaClient

token_mgr = AwsParameterStoreTokenManager(
    "/strava-facade-api/production/strava-api-token-json",
    "/strava-facade-api/production/strava-api-client-id",
    "/strava-facade-api/production/strava-api-client-secret",
)
client = StravaClient(token_mgr.get_access_token())
response = client.list_activities(
    after_ts=datetime(2025, 1, 18, 6, 0, tzinfo=ZoneInfo("Europe/Rome")),
    n_results_per_page=2,
)
assert len(response) == 2
assert response[0]["name"] == "Dobbiaco Winter Night Run 🦠"
assert response[0]["id"] == 13389554554
```
"""

from datetime import datetime, timedelta

import log_utils as logger
import requests
from datetime_utils import datetime_utils

__all__ = [
    "ActivityNotFound",
    "NaiveDatetime",
    "InvalidDatetime",
    "PossibleDuplicatedActivity",
    "RequestedResultsPageDoesNotExist",
    "SportTypeInvalid",
    "StravaClient",
]


class StravaClient:
    def __init__(self, access_token: str):
        self._access_token = access_token

    def list_activities(
        self,
        after_ts: datetime | int | float | None = None,
        before_ts: datetime | int | float | None = None,
        activity_type: str | None = None,
        n_results_per_page: int | None = None,
        page_n: int = 1,
    ) -> list[dict]:
        """
        List all my activities and filter by date, as supported by Strava API.
        Also, filter by activity_type, but this is just a Python filtering (NOT supported by Strava API).

        Docs:
            - Authentication: https://developers.strava.com/docs/authentication/
            - List Athlete Activities API: https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities

        Example:
            $ curl "https://www.strava.com/api/v3/athlete/activities?after=1718834400&before=1718920799" \
             -H "Authorization: Bearer XXX"

            [
              {
                "resource_state": 2,
                "athlete": {
                  "id": 115890775,
                  "resource_state": 1
                },
                "name": "Weight training: chest, triceps, shoulders",
                "distance": 0.0,
                "moving_time": 2902,
                "elapsed_time": 2902,
                "total_elevation_gain": 0,
                "type": "WeightTraining",
                "sport_type": "WeightTraining",
                "id": 11699080053,
                "start_date": "2024-06-20T16:53:19Z",
                "start_date_local": "2024-06-20T18:53:19Z",
                "timezone": "(GMT+02:00) Africa/Blantyre",
                "utc_offset": 7200.0,
                "location_city": null,
                "location_state": null,
                "location_country": "Italy",
                "achievement_count": 0,
                "kudos_count": 1,
                "comment_count": 0,
                "athlete_count": 1,
                "photo_count": 0,
                "map": {
                  "id": "a11699080053",
                  "summary_polyline": "",
                  "resource_state": 2
                },
                "trainer": true,
                "commute": false,
                "manual": false,
                "private": false,
                "visibility": "followers_only",
                "flagged": false,
                "gear_id": null,
                "start_latlng": [],
                "end_latlng": [],
                "average_speed": 0.0,
                "max_speed": 0.0,
                "average_temp": 32,
                "has_heartrate": true,
                "average_heartrate": 70.7,
                "max_heartrate": 121.0,
                "heartrate_opt_out": false,
                "display_hide_heartrate_option": true,
                "elev_high": 0.0,
                "elev_low": 0.0,
                "upload_id": 12481876918,
                "upload_id_str": "12481876918",
                "external_id": "garmin_ping_349214871994",
                "from_accepted_tag": false,
                "pr_count": 0,
                "total_photo_count": 0,
                "has_kudoed": false
              }
            ]

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
        response.raise_for_status()

        data = response.json()

        # If the results page requested does not exist:
        if page_n != 1 and data == []:
            raise RequestedResultsPageDoesNotExist(page_n)

        # Filter y activity_type.
        if activity_type:
            data = []
            for activity in response.json():
                if (
                    activity.get("type") == activity_type
                    or activity.get("sport_type") == activity_type
                ):
                    data.append(activity)

        # A single `activity` is a dict like:
        # {
        #     "resource_state": 2,
        #     "athlete": {
        #         "id": 115890775,
        #         "resource_state": 1
        #     },
        #     "name": "Weight training: broken finger, abs, triceps, legs",
        #     "distance": 0.0,
        #     "moving_time": 7157,
        #     "elapsed_time": 7157,
        #     "total_elevation_gain": 0,
        #     "type": "WeightTraining",
        #     "sport_type": "WeightTraining",
        #     "id": 10709853894,
        #     "start_date": "2024-02-06T17:20:32Z",
        #     "start_date_local": "2024-02-06T18:20:32Z",
        #     "timezone": "(GMT+01:00) Africa/Algiers",
        #     "utc_offset": 3600.0,
        #     "location_city": null,
        #     "location_state": null,
        #     "location_country": "Italy",
        #     "achievement_count": 0,
        #     "kudos_count": 0,
        #     "comment_count": 0,
        #     "athlete_count": 1,
        #     "photo_count": 0,
        #     "map": {
        #         "id": "a10709853894",
        #         "summary_polyline": "",
        #         "resource_state": 2
        #     },
        #     "trainer": true,
        #     "commute": false,
        #     "manual": false,
        #     "private": false,
        #     "visibility": "followers_only",
        #     "flagged": false,
        #     "gear_id": null,
        #     "start_latlng": [],
        #     "end_latlng": [],
        #     "average_speed": 0.0,
        #     "max_speed": 0.0,
        #     "average_temp": 24,
        #     "has_heartrate": true,
        #     "average_heartrate": 77.0,
        #     "max_heartrate": 148.0,
        #     "heartrate_opt_out": false,
        #     "display_hide_heartrate_option": true,
        #     "elev_high": 0.0,
        #     "elev_low": 0.0,
        #     "upload_id": 11453524654,
        #     "upload_id_str": "11453524654",
        #     "external_id": "garmin_ping_319619866387",
        #     "from_accepted_tag": false,
        #     "pr_count": 0,
        #     "total_photo_count": 0,
        #     "has_kudoed": false
        # }
        return data

    def get_activity_details(self, activity_id: int) -> dict:
        """
        Get details for the given activity id.

        Docs:
            - Authentication: https://developers.strava.com/docs/authentication/
            - Get Activity API: https://developers.strava.com/docs/reference/#api-Activities-getActivityById
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
        details = response.json()
        # `details` is a dict like:
        # {
        #     "resource_state": 3,
        #     "athlete": {
        #         "id": 115890775,
        #         "resource_state": 1
        #     },
        #     "name": "Weight training: broken finger, abs, triceps, legs",
        #     "distance": 0.0,
        #     "moving_time": 7157,
        #     "elapsed_time": 7157,
        #     "total_elevation_gain": 0,
        #     "type": "WeightTraining",
        #     "sport_type": "WeightTraining",
        #     "id": 10709853894,
        #     "start_date": "2024-02-06T17:20:32Z",
        #     "start_date_local": "2024-02-06T18:20:32Z",
        #     "timezone": "(GMT+01:00) Africa/Algiers",
        #     "utc_offset": 3600.0,
        #     "location_city": null,
        #     "location_state": null,
        #     "location_country": "Italy",
        #     "achievement_count": 0,
        #     "kudos_count": 0,
        #     "comment_count": 0,
        #     "athlete_count": 1,
        #     "photo_count": 0,
        #     "map": {
        #         "id": "a10709853894",
        #         "polyline": "",
        #         "resource_state": 3,
        #         "summary_polyline": ""
        #     },
        #     "trainer": true,
        #     "commute": false,
        #     "manual": false,
        #     "private": false,
        #     "visibility": "followers_only",
        #     "flagged": false,
        #     "gear_id": null,
        #     "start_latlng": [],
        #     "end_latlng": [],
        #     "average_speed": 0.0,
        #     "max_speed": 0.0,
        #     "average_temp": 24,
        #     "has_heartrate": true,
        #     "average_heartrate": 77.0,
        #     "max_heartrate": 148.0,
        #     "heartrate_opt_out": false,
        #     "display_hide_heartrate_option": true,
        #     "elev_high": 0.0,
        #     "elev_low": 0.0,
        #     "upload_id": 11453524654,
        #     "upload_id_str": "11453524654",
        #     "external_id": "garmin_ping_319619866387",
        #     "from_accepted_tag": false,
        #     "pr_count": 0,
        #     "total_photo_count": 0,
        #     "has_kudoed": false,
        #     "description": "Finger rehab: 15 reps x 20 sets\nDecline crunch: bodyweight x 15 reps x 5 sets\nRussian twist: 40 reps x 5 sets\nV-hold: 30s reps x 5 sets\nResistance band tricep pull-down: red band (25kg) x 15 reps x 5 sets\nBulgarian split squat: bodyweight+16kg x 10 reps x 5 sets\nSplit soleus raise: bodyweight x 20 reps x 4 sets\n",
        #     "calories": 404.0,
        #     "perceived_exertion": null,
        #     "prefer_perceived_exertion": null,
        #     "segment_efforts": [],
        #     "laps": [
        #         {
        #             "id": 37068060147,
        #             "resource_state": 2,
        #             "name": "Lap 1",
        #             "activity": {
        #                 "id": 10709853894,
        #                 "visibility": "followers_only",
        #                 "resource_state": 1
        #             },
        #             "athlete": {
        #                 "id": 115890775,
        #                 "resource_state": 1
        #             },
        #             "elapsed_time": 7157,
        #             "moving_time": 7157,
        #             "start_date": "2024-02-06T17:20:32Z",
        #             "start_date_local": "2024-02-06T18:20:32Z",
        #             "distance": 0.0,
        #             "average_speed": 0.0,
        #             "max_speed": 0.0,
        #             "lap_index": 1,
        #             "split": 1,
        #             "start_index": 0,
        #             "end_index": 4321,
        #             "total_elevation_gain": 0,
        #             "device_watts": false,
        #             "average_heartrate": 77.0,
        #             "max_heartrate": 148.0
        #         }
        #     ],
        #     "photos": {
        #         "primary": null,
        #         "count": 0
        #     },
        #     "stats_visibility": [
        #         {
        #             "type": "heart_rate",
        #             "visibility": "everyone"
        #         },
        #         {
        #             "type": "pace",
        #             "visibility": "everyone"
        #         },
        #         {
        #             "type": "power",
        #             "visibility": "everyone"
        #         },
        #         {
        #             "type": "speed",
        #             "visibility": "everyone"
        #         },
        #         {
        #             "type": "calories",
        #             "visibility": "everyone"
        #         }
        #     ],
        #     "hide_from_home": false,
        #     "device_name": "Garmin Forerunner 965",
        #     "embed_token": "33f24624d0d69cfd987523970ae102065eb6b101",
        #     "private_note": "",
        #     "available_zones": []
        # }
        return details

    def update_activity(self, activity_id: int, data: dict) -> dict:
        """
        Update an activity by its id.

        Docs:
            - Authentication: https://developers.strava.com/docs/authentication/
            - Update Activity API: https://developers.strava.com/docs/reference/#api-Activities-updateActivityById
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
        return response.json()

    def create_activity(
        self,
        name: str,
        sport_type: str,
        start_date: datetime | str,
        duration_seconds: int,  # Seconds.
        description: str | None,
        do_detect_duplicates=False,
    ):
        """
        Create a new activity.
        It also tries to make sure that this new activity is not a duplicate.

        Docs:
            - Authentication: https://developers.strava.com/docs/authentication/
            - Create Activity API: https://developers.strava.com/docs/reference/#api-Activities-createActivity
        """
        logger.info(f"Creating new activity...")

        # Parse start_date.
        if isinstance(start_date, str):
            try:
                start_date = datetime.fromisoformat(start_date)
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
            activities = self.list_activities(after_ts, before_ts, sport_type)
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

        details = response.json()
        # `details` is a dict like:
        # {
        #     "resource_state": 3,
        #     "athlete": {"id": 115890775, "resource_state": 1},
        #     "name": "Test1 Paolo",
        #     "distance": 0.0,
        #     "moving_time": 3605,
        #     "elapsed_time": 3605,
        #     "total_elevation_gain": 0,
        #     "type": "WeightTraining",
        #     "sport_type": "WeightTraining",
        #     "id": 11977678435,
        #     "start_date": "2024-07-25T13:39:55Z",
        #     "start_date_local": "2024-07-25T15:39:55Z",
        #     "timezone": "(GMT+01:00) Europe/Rome",
        #     "utc_offset": 7200.0,
        #     "location_city": None,
        #     "location_state": None,
        #     "location_country": "Italy",
        #     "achievement_count": 0,
        #     "kudos_count": 0,
        #     "comment_count": 0,
        #     "athlete_count": 1,
        #     "photo_count": 0,
        #     "map": {
        #         "id": "a11977678435",
        #         "polyline": "",
        #         "resource_state": 3,
        #         "summary_polyline": "",
        #     },
        #     "trainer": False,
        #     "commute": False,
        #     "manual": True,
        #     "private": False,
        #     "visibility": "followers_only",
        #     "flagged": False,
        #     "gear_id": None,
        #     "start_latlng": [],
        #     "end_latlng": [],
        #     "average_speed": 0.0,
        #     "max_speed": 0,
        #     "has_heartrate": False,
        #     "heartrate_opt_out": False,
        #     "display_hide_heartrate_option": False,
        #     "upload_id": None,
        #     "external_id": None,
        #     "from_accepted_tag": False,
        #     "pr_count": 0,
        #     "total_photo_count": 0,
        #     "has_kudoed": False,
        #     "description": "test from Python",
        #     "calories": 0,
        #     "perceived_exertion": None,
        #     "prefer_perceived_exertion": None,
        #     "segment_efforts": [],
        #     "photos": {"primary": None, "count": 0},
        #     "stats_visibility": [
        #         {"type": "heart_rate", "visibility": "everyone"},
        #         {"type": "pace", "visibility": "everyone"},
        #         {"type": "power", "visibility": "everyone"},
        #         {"type": "speed", "visibility": "everyone"},
        #         {"type": "calories", "visibility": "everyone"},
        #     ],
        #     "hide_from_home": False,
        #     "embed_token": "175fc05106f4e824cdc261524af5a9320fe7b0de",
        #     "available_zones": [],
        # }
        return details


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
    def __init__(self, page_n):
        self.page_n = page_n
