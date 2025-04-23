"""
** SPORT MONOREPO: GARMIN CONNECT CLIENT **
===========================================

The authentication is interactive and it asks for the username and password used
 in Garmin Connect official website. It gets a token and stores it in a local file
 for months.

```py
from garmin_connect_client import GarminConnectClient
from garmin_connect_client.garmin_connect_token_managers import (
    FileGarminConnectTokenManager,
)

client = GarminConnectClient()
# It will ask interactively for username and password the first time.

# You can also leverage the file token manager:
# garmin_tk_mgr = FileGarminConnectTokenManager(email="my@email.com", password="sss")
# garmin_tk_mgr = FileGarminConnectTokenManager(token_file_path=Path() / "token.txt")
# garmin_tk_mgr = FileGarminConnectTokenManager(do_use_fake_test_token=True)
# client = GarminConnectClient(garmin_tk_mgr)

response = client.list_activities("2025-03-22")
activities = list(response.get_activities())
assert len(activities) == 2
assert activities[0]["activityId"] == 18603794245
assert activities[0]["activityName"] == "Strength"
assert activities[1]["activityId"] == 18606916834
assert activities[1]["activityName"] == "Limone Piemonte Trail Running"

response = client.get_activity_summary(18606916834)
assert response.data["activityId"] == 18606916834
assert response.data["activityName"] == "Limone Piemonte Trail Running"
```
"""

from datetime import date, datetime
from typing import Any

import garth
from garminconnect import Garmin, GarminConnectAuthenticationError

from .garmin_connect_token_managers import (
    FileGarminConnectTokenManager,
    FileGarminConnectTokenManagerException,
)
from .responses import (
    ActivityDetailsResponse,
    ActivitySummaryResponse,
    ListActivitiesResponse,
)

__all__ = [
    "GarminConnectClient",
    "InvalidDate",
    "BaseGarminConnectClientException",
]


class GarminConnectClient:
    def __init__(self, token_manager: FileGarminConnectTokenManager | None = None):
        self._garmin: Garmin | None = None
        self._token_manager = token_manager or FileGarminConnectTokenManager()

    @property
    def garmin(self) -> Garmin:
        if not self._garmin:
            self._garmin = Garmin()

            try:
                token_base64 = self._token_manager.get_access_token()
                self._garmin.login(token_base64)
            except (
                FileGarminConnectTokenManagerException,
                FileNotFoundError,
                garth.exc.GarthHTTPError,
                GarminConnectAuthenticationError,
            ) as exc:
                # Session expired, interactive login with username and password.
                email = self._token_manager.get_email()
                password = self._token_manager.get_password()
                self._garmin = Garmin(email=email, password=password)
                self._garmin.login()
                token_base64 = self._garmin.garth.dumps()
                self._token_manager.store_access_token(token_base64)
        return self._garmin

    def list_activities(self, day: date | datetime | str) -> ListActivitiesResponse:
        """
        List all activities for the given day.

        Args:
            day: eg. datetime.date(2023, 5, 1) or datetime.datetime(2023, 5, 1, 0, 0)
             or "2023-05-01".

        Raw response data format: see `docs/list activities for date.md`.

        Example:
            client = GarminConnectClient()
            response = client.list_activities("2025-03-22")
            activities = list(response.get_activities())
            assert len(activities) == 2
            assert activities[0]["activityId"] == 18603794245
            assert activities[0]["activityName"] == "Strength"
        """
        if isinstance(day, date) or isinstance(day, datetime):
            date_str = day.isoformat()
        elif isinstance(day, str):
            try:
                datetime.fromisoformat(day)
            except ValueError as exc:
                raise InvalidDate(day) from exc
            date_str = day
        else:
            raise InvalidDate(day)
        data: dict[str, dict] = self.garmin.get_activities_fordate(date_str)
        return ListActivitiesResponse(data)

    def get_activity_summary(self, activity_id: int) -> ActivitySummaryResponse:
        """
        Get summary for the given activity_id.

        Args:
            activity_id: eg. 18606916834.

        Raw response data format: see `docs/activity summary.md`.

        Example:
            client = GarminConnectClient()
            response = client.get_activity_summary(18606916834)
            assert response.data["activityId"] == 18606916834
            assert response.data["activityName"] == "Limone Piemonte Trail Running"
        """
        data: dict[str, Any] = self.garmin.get_activity(activity_id)
        return ActivitySummaryResponse(data)

    def get_activity_details(
        self,
        activity_id: int,
        max_metrics_data_count: int = 2000,
        do_include_polyline: bool = False,
        max_polyline_count: int = 4000,
        do_keep_raw_data: bool = False,
    ) -> ActivityDetailsResponse:
        """
        Get details for the given activity_id.

        Note: if you want to plot over time (eg. HR over time), like Garmin Connect
         website does, then use `response.non_paused_time_stream` for the x-axis.
         Strava website instead only plots over distance.

        Note: this response can be large, some Mb, so we do not collect polylines
         by default and also discard not relevant metrics to reduce the size.

        Args:
            activity_id: eg. 18606916834.
            max_metrics_data_count: max number of metrics datapoints to include in
             the response. It is <= the number of the original netrics collected.
            do_include_polyline: the polyline.
            max_polyline_count: max number of metrics datapoints to include in
             the response.
            do_keep_raw_data: keep the raw response data, duplicating some data.

        Raw response data format: see `docs/activity details.md`.

        Example:
            client = GarminConnectClient()
            response = client.get_activity_details(
                18606916834,
                max_metrics_data_count=999 * 1000,
                do_include_polyline=False,
                # max_polyline_count: int = 4000,
                do_keep_raw_data=False,
            )
            assert response.activity_id == 18606916834
            assert response.original_dataset_size == 4179
            assert response.streams_size == 4179
            assert response.elapsed_time_stream[3] == 17.0
        """
        maxpoly = 0
        if do_include_polyline:
            maxpoly = max_polyline_count
        response: dict[str, Any] = self.garmin.get_activity_details(
            activity_id,
            maxchart=max_metrics_data_count,
            maxpoly=maxpoly,
        )
        return ActivityDetailsResponse(response, do_keep_raw_data)


class BaseGarminConnectClientException(Exception):
    pass


class InvalidDate(BaseGarminConnectClientException):
    def __init__(self, value):
        self.value = value
