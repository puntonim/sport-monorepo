"""
** SPORT MONOREPO: GARMIN CONNECT CLIENT **
===========================================

The authentication is interactive and it asks for the username and password used
 in Garmin Connect official website. It gets a token and stores it in a local file
 for months.

```py
from garmin_connect_client import GarminConnectClient

client = GarminConnectClient()
# It will ask interactively for username and password the first time.

activities = client.list_activities("2025-03-22")
assert len(activities["ActivitiesForDay"]["payload"]) == 2
assert activities["ActivitiesForDay"]["payload"][0]["activityId"] == 18603794245
```
"""

from datetime import date, datetime
from getpass import getpass
from pathlib import Path
from typing import Any

import garth
from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

from .activity_details_response import ActivityDetailsResponse

__all__ = [
    "GarminConnectClient",
    "InvalidDate",
    "BaseGarminConnectClientException",
    "ActivityDetailsResponse",
]

ROOT_DIR = Path(__file__).parent.parent
TOKEN_FILE = ROOT_DIR / "garmin-connect-token"


class GarminConnectClient:
    def __init__(self):
        self._garmin: Garmin | None = None

    @property
    def garmin(self) -> Garmin:
        if not self._garmin:
            self._garmin = Garmin()
            try:
                with open(TOKEN_FILE, "r") as fin:
                    token_base64 = fin.read()
                self._garmin.login(token_base64)
            except (
                FileNotFoundError,
                garth.exc.GarthHTTPError,
                GarminConnectAuthenticationError,
            ) as exc:
                # Session expired, interactive login with username and password.
                email = input("Garmin Connect login email: ")
                password = getpass("Garmin Connect login password: ")
                self._garmin = Garmin(email=email, password=password)
                self._garmin.login()
                token_base64 = self._garmin.garth.dumps()
                with open(TOKEN_FILE, "w") as fout:
                    fout.write(token_base64)
        return self._garmin

    def list_activities(self, day: date | datetime | str) -> dict[str, dict]:
        """
        List all activities for the given day.

        Args:
            day: eg. datetime.date(2023, 5, 1) or datetime.datetime(2023, 5, 1, 0, 0)
             or "2023-05-01".

        Example: see `docs/list activities for date.md`.
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
        return data

    def get_activity_summary(self, activity_id: int) -> dict[str, Any]:
        """
        Get summary for the given activity_id.

        Args:
            activity_id: eg. 18606916834.

        Example: see `docs/activity summary.md`.
        """
        data: dict[str, Any] = self.garmin.get_activity(activity_id)
        return data

    def get_activity_details(
        self,
        activity_id: int,
        max_metrics_data_count: int = 2000,
        do_include_polyline: bool = False,
        max_polyline_count: int = 4000,
        do_keep_raw_response: bool = False,
    ) -> ActivityDetailsResponse:
        """
        Get details for the given activity_id.

        Note that this response can be big, some Mb, so we do not collect polylines
         by default and also discard not relevant metrics to reduce the size.

        Args:
            activity_id: eg. 18606916834.
            max_metrics_data_count: max number of metrics datapoints to include in
             the response. It is <= the number of the original netrics collected.
            do_include_polyline: the polyline.
            max_polyline_count: max number of metrics datapoints to include in
             the response.
            do_keep_raw_response: keep the raw response, duplicating some data.

        Example: see `docs/activity details.md`.
        """
        maxpoly = 0
        if do_include_polyline:
            maxpoly = max_polyline_count
        data: dict[str, Any] = self.garmin.get_activity_details(
            activity_id,
            maxchart=max_metrics_data_count,
            maxpoly=maxpoly,
        )
        activity_details = ActivityDetailsResponse(data, do_keep_raw_response)
        return activity_details


class BaseGarminConnectClientException(Exception):
    pass


class InvalidDate(BaseGarminConnectClientException):
    def __init__(self, value):
        self.value = value
