"""
** SPORT MONOREPO: GARMIN CONNECT CLIENT **
===========================================

This client does NOT use any official Garmin API client because Garmin API are open
 to business client only, not for private clients.
Instead, this client wraps an unofficial library (garminconnect) that  leverages
 the backend-for-frontend used by Garmin Connect official website.

The authentication is interactive and it asks for the username and password used
 in Garmin Connect official website. It gets a token from their backend and
  stores it in a local file, with a long expiration time.
Use the same email and password that you use in Garmin Connect website.

NOTABLE DATA
------------
- HR avg, min and max
    are in the response to: client.get_activity_summary(<activity id>)
    I tested that those value are very close to the one I computed from the HR stream.

- The data streams (hr, distance, altitude, etc)
    are in both responses to:
        client.get_activity_details(<activity id>)
        client.download_activity(<activity id>)
    They contain the same datasets, and I recommend to use `client.get_activity_details`
     because it includes some extra info, like:
        response.original_dataset_size
        response.streams_size
     and it also you to request a subset of the original dataset.
    I verified that they both return the same dataset.

- The splits executed during a workout, when pressing the lap button, can be retrieved
   with client.get_activity_splits(<activity id>)
   and they include: distance, elapsedDuration, averageHR, maxHR

- Name, start date, type, distance, duration, average HR, max speed
    are in both responses to:
        client.list_activities(<date>)
        client.get_activity_summary(<activity id>)
    I tested that the average HR returned in both methods are the same.

EXAMPLE
-------
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
    ActivitySplitsResponse,
    ActivitySummaryResponse,
    DownloadFitContentResponse,
    ListActivitiesResponse,
)

__all__ = [
    "GarminConnectClient",
    "InvalidDate",
    "BaseGarminConnectClientException",
]


class GarminConnectClient:
    """
    See docstring at the top of this file.
    """

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

        Iterate the activities with `response.get_activities()`.
        Each activity is a dict with these notable attrs, and others:
            {
                "activityId": 18603794245,
                "activityName": "Strength",
                "startTimeLocal": "2025-03-22T12:06:14.0",
                "startTimeGMT": "2025-03-22T11:06:14.0",
                "activityType": {
                    "typeId": 13,
                    "typeKey": "strength_training",
                    ...
                },
                "eventType": {"typeId": 9, "typeKey": "uncategorized", "sortOrder": 10},
                "distance": 0.0,
                "duration": 5267.6572265625,
                "calories": 410.0,
                "bmrCalories": 126.81397026909723,
                "activeCalories": 283.18602973090276,
                "steps": 428,
                "privacy": {"typeId": 2, "typeKey": "private"},
                "elapsedDuration": 5267.6572265625,
                "minTemperature": 31.0,
                "lapCount": 1,
                "averageHR": 72.0,
                "activeSets": 21,
                "moderateIntensityMinutes": 38,
                "vigorousIntensityMinutes": 3,
                "pr": False,
                "favorite": False,
                ...
            }
        I tested that `averageHR` returned here is the same as the one
         return in client.get_activity_summary(<activity id>).
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
            assert response.summary["averageHR"] == 121.0

        Each summary is a dict with these notable attrs, and others:
            {
                "activityId": 18606916834,
                "activityUUID": {"uuid": "56e0a3b9-1e01-41fd-9706-969ddc783154"},
                "activityName": "Limone Piemonte Trail Running",
                "userProfileId": 113739130,
                "activityTypeDTO": {
                    "typeId": 6,
                    "typeKey": "trail_running",
                    "parentTypeId": 1,
                    "isHidden": False,
                    ...
                },
                "eventTypeDTO": {"typeId": 9, "typeKey": "uncategorized", "sortOrder": 10},
                "timeZoneUnitDTO": {
                    "unitId": 124,
                    "unitKey": "Europe/Paris",
                    "factor": 0.0,
                    "timeZone": "Europe/Paris",
                },
                "metadataDTO": {
                    "lastUpdateDate": "2025-03-22T17:29:36.0",
                    "uploadedDate": "2025-03-22T17:29:35.0",
                    "videoUrl": None,
                    "hasPolyline": True,
                    "hasChartData": True,
                    "hasHrTimeInZones": True,
                    "hasPowerTimeInZones": True,
                    "userInfoDto": {
                        "userProfilePk": 113739130,
                        "displayname": "3c9af3f5-eec2-4047-b9d8-bc98d3bb88c3",
                        "fullname": "Paolo",
                        "profileImageUrlLarge": "https://s3.amazonaws.com/garmin-connect-prod/profile_images/54ac91f0-443c-4611-a585-eb18d69ae44e-prof.png",
                        ...
                    },
                    "lapCount": 11,
                    "hasSplits": True,
                    "hasRunPowerWindData": True,
                    "favorite": False,
                    "personalRecord": False,
                    ...
                },
                "summaryDTO": {
                    "startTimeLocal": "2025-03-22T17:04:36.0",
                    "startTimeGMT": "2025-03-22T16:04:36.0",
                    "startLatitude": 44.16586736217141,
                    "startLongitude": 7.569181434810162,
                    "distance": 10803.7,
                    "duration": 4177.955,
                    "movingDuration": 4173.44,
                    "elapsedDuration": 4177.955,
                    "elevationGain": 514.0,
                    "elevationLoss": 508.0,
                    "maxElevation": 1803.6,
                    "minElevation": 1396.8,
                    "averageSpeed": 2.5859999656677246,
                    "averageMovingSpeed": 2.5886798967979896,
                    "maxSpeed": 4.4039998054504395,
                    "calories": 951.0,
                    "bmrCalories": 101.0,
                    "averageHR": 121.0,
                    "maxHR": 146.0,
                    "minHR": 98.0,
                    "averageRunCadence": 159.359375,
                    "maxRunCadence": 236.0,
                    "averageTemperature": 15.536073508039488,
                    "maxTemperature": 19.0,
                    "minTemperature": 12.0,
                    "averagePower": 333.0,
                    "maxPower": 473.0,
                    "minPower": 0.0,
                    "normalizedPower": 353.0,
                    "totalWork": 331.74065994911723,
                    "groundContactTime": 277.20001220703125,
                    "strideLength": 97.27000122070314,
                    "verticalOscillation": 8.34000015258789,
                    "trainingEffect": 3.700000047683716,
                    "anaerobicTrainingEffect": 2.0,
                    "aerobicTrainingEffectMessage": "IMPROVING_AEROBIC_ENDURANCE_9",
                    "anaerobicTrainingEffectMessage": "MAINTAINING_ANAEROBIC_BASE_1",
                    "verticalRatio": 8.930000305175781,
                    "endLatitude": 44.1658887360245,
                    "endLongitude": 7.569096609950066,
                    "maxVerticalSpeed": 0.8000488281250001,
                    "waterEstimated": 1025.0,
                    "trainingEffectLabel": "AEROBIC_BASE",
                    "activityTrainingLoad": 189.7177276611328,
                    "minActivityLapDuration": 205.186,
                    "directWorkoutFeel": 75,
                    "directWorkoutRpe": 80,
                    "moderateIntensityMinutes": 1,
                    "vigorousIntensityMinutes": 44,
                    "steps": 11150,
                    "beginPotentialStamina": 81.0,
                    "endPotentialStamina": 56.0,
                    "minAvailableStamina": 50.0,
                    "avgGradeAdjustedSpeed": 2.947999954223633,
                    "differenceBodyBattery": -10,
                },
                "locationName": "Limone Piemonte",
                "splitSummaries": [
                    {
                        "distance": 10803.7,
                        "duration": 4177.955,
                        "movingDuration": 4174.0,
                        "elevationGain": 514.0,
                        "elevationLoss": 508.0,
                        "averageSpeed": 2.5859999656677246,
                        "averageMovingSpeed": 2.588332581531504,
                        "maxSpeed": 4.4039998054504395,
                        "calories": 951.0,
                        "bmrCalories": 101.0,
                        "averageHR": 121.0,
                        "maxHR": 146.0,
                        "averageRunCadence": 159.34375,
                        "maxRunCadence": 236.0,
                        "averageTemperature": 16.0,
                        "maxTemperature": 19.0,
                        "minTemperature": 12.0,
                        "averagePower": 333.0,
                        "maxPower": 473.0,
                        "normalizedPower": 353.0,
                        "groundContactTime": 277.20001220703125,
                        "strideLength": 97.27000122070314,
                        "verticalOscillation": 8.34000015258789,
                        "verticalRatio": 8.930000305175781,
                        "totalExerciseReps": 0,
                        "avgVerticalSpeed": 0.0020000000949949026,
                        "avgGradeAdjustedSpeed": 2.947999954223633,
                        "splitType": "INTERVAL_ACTIVE",
                        "noOfSplits": 1,
                        "maxElevationGain": 514.0,
                        "averageElevationGain": 171.0,
                        "maxDistance": 10803,
                        "maxDistanceWithPrecision": 10803.7,
                    },
                    ...
                ],
            }
        I tested that the HR avg|min|max return here are very close to the ones
         computed directly from the HR stream.
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

        The detail is a dict with these notable attrs, and others:
            {
                "activityId": 18606916834,
                "measurementCount": 26,
                "metricsCount": 125,
                "totalMetricsCount": 4179,
                "metricDescriptors": [
                    {
                        "metricsIndex": 0,
                        "key": "directTimestamp",
                        "unit": {"id": 120, "key": "gmt", "factor": 0.0},
                    },
                    {
                        "metricsIndex": 1,
                        "key": "directLongitude",
                        "unit": {"id": 60, "key": "dd", "factor": 1.0},
                    },
                    ... <MANY> ...
                ],
                "activityDetailMetrics": [
                    {
                        "metrics": [
                            56.0,  # directAvailableStamina
                            1476.4000244140625,  # directElevation meter
                            12.0,  # directAirTemperature
                            44.16305732913315,  # directLatitude
                            3996.0,  # sumElapsedDuration sec
                            7.572167655453086,  # directLongitude
                            3993.0,  # sumMovingDuration sec
                            22.0,  # directBodyBattery
                            10100.8203125,  # sumDistance meter
                            3.803999900817871,  # directGradeAdjustedSpeed mps
                            176.0,  # directDoubleCadence stepsPerMinute
                            3996.0,  # sumDuration sec
                            1742663472000.0,  # directTimestamp gmt
                            59.0,  # directPotentialStamina
                            4.198999881744385,  # directSpeed mps
                            138.0,  # directHeartRate bpm
                            355.0,  # directPower watt
                            88.0,  # directRunCadence stepsPerMinute
                            0.0,  # directFractionalCadence stepsPerMinute
                            -0.6000000238418579,  # directVerticalSpeed mps
                            6.769999980926514,  # directVerticalRatio
                            9.700000000000001,  # directVerticalOscillation cm
                            226.0,  # directGroundContactTime ms
                            1337258.0,  # sumAccumulatedPower watt
                            143.1,  # directStrideLength cm
                            2.0,  # directPerformanceCondition
                        ]
                    },
                    ... <MANY> ...
                ],
                "geoPolylineDTO": {
                    "startPoint": {
                        "lat": 44.16586736217141,
                        "lon": 7.569181434810162,
                        "altitude": None,
                        "time": 1742659476000,
                        "timerStart": False,
                        "timerStop": False,
                        "distanceFromPreviousPoint": None,
                        "distanceInMeters": None,
                        "speed": 0.0,
                        "cumulativeAscent": None,
                        "cumulativeDescent": None,
                        "extendedCoordinate": False,
                        "valid": True,
                    },
                    "endPoint": {
                        "lat": 44.16588747873902,
                        "lon": 7.56909342482686,
                        "altitude": None,
                        "time": 1742663654000,
                        "timerStart": False,
                        "timerStop": False,
                        "distanceFromPreviousPoint": None,
                        "distanceInMeters": None,
                        "speed": 0.0,
                        "cumulativeAscent": None,
                        "cumulativeDescent": None,
                        "extendedCoordinate": False,
                        "valid": True,
                    },
                    "minLat": 44.1529578063637,
                    "maxLat": 44.16588747873902,
                    "minLon": 7.5516420509666204,
                    "maxLon": 7.5731823686510324,
                    "polyline": [
                        {
                            "lat": 44.16586736217141,
                            "lon": 7.569181434810162,
                            "altitude": None,
                            "time": 1742659476000,
                            "timerStart": False,
                            "timerStop": False,
                            "distanceFromPreviousPoint": None,
                            "distanceInMeters": None,
                            "speed": 0.0,
                            "cumulativeAscent": None,
                            "cumulativeDescent": None,
                            "extendedCoordinate": False,
                            "valid": True,
                        },
                        ... <MANY> ...
                    ],
                },
                "heartRateDTOs": None,
                "pendingData": None,
                "detailsAvailable": True,
            }
        I tested that all the streams sizes match the original dataset size.
        Note that some streams can contain None values, see details in ActivityDetailsResponse.
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

    def get_activity_splits(self, activity_id: int) -> ActivitySplitsResponse:
        """
        Get the splits for the given activity.
        Splits can be automatic or started when the lap button is pressed (like during
         a 6x300m workout). The splits started with a lap button press have:
         "type": "INTERVAL_ACTIVE".
        You can get them with: response.get_interval_active_splits()
        However, some activities, when I never pressed the lap button, still have
         1 single INTERVAL_ACTIVE split which is the whole activity.

        Args:
            activity_id: eg. 18923007987  # 6x300m..

        Raw response data format: see `docs/splits.md`.

        Example:
            client = GarminConnectClient()
            response = client.get_activity_splits(18923007987)
            for active_split in response.get_interval_active_splits():
                print(active_split["elapsedDuration"])

        The split is a dict with these attrs:
            {
                "startTimeLocal": "2025-04-24T16:59:55.0",
                "startTimeGMT": "2025-04-24T14:59:55.0",
                "startLatitude": 45.62512510456145,
                "startLongitude": 9.63120530359447,
                "distance": 300.0,
                "duration": 49.99,
                "movingDuration": 46.0,
                "elapsedDuration": 49.99,
                "elevationGain": 0.0,
                "elevationLoss": 1.0,
                "averageSpeed": 6.000999927520752,
                "averageMovingSpeed": 6.521739130434782,
                "maxSpeed": 6.625000000000001,
                "calories": 12.0,
                "bmrCalories": 1.0,
                "averageHR": 134.0,
                "maxHR": 160.0,
                "averageRunCadence": 182.046875,
                "maxRunCadence": 220.0,
                "averageTemperature": 25.0,
                "maxTemperature": 26.0,
                "minTemperature": 25.0,
                "averagePower": 556.0,
                "maxPower": 727.0,
                "normalizedPower": 524.0,
                "groundContactTime": 168.3000030517578,
                "strideLength": 178.8,
                "verticalOscillation": 7.540000152587891,
                "verticalRatio": 4.21999979019165,
                "totalExerciseReps": 0,
                "endLatitude": 45.623174300417304,
                "endLongitude": 9.62955859489739,
                "avgVerticalSpeed": -0.019999999552965164,
                "avgGradeAdjustedSpeed": 5.619999885559082,
                "avgElapsedDurationVerticalSpeed": -0.02399993896484375,
                "type": "INTERVAL_ACTIVE",
                "messageIndex": 8,
                "lapIndexes": [4],
                "endTimeGMT": "2025-04-24T15:00:45.0",
                "startElevation": 187.4,
            }
        """
        data: dict = self.garmin.get_activity_typed_splits(activity_id)
        return ActivitySplitsResponse(data)

    def download_fit_content(self, activity_id: int) -> DownloadFitContentResponse:
        """
        Download the original .fit file content.

        IMP: do not use this method, but use client.get_activity_details(<activity id>)
         instead, because its response includes some extra info, like:
            response.original_dataset_size
            response.streams_size
        And also it allows you to download a subset of the original dataset.
        I made several tests to ensure that the data returned by the 2 methods
         are the same.
        """
        # Lib example: https://github.com/cyberjunky/python-garminconnect/blob/master/example.py#L501
        zip_data: bytes = self.garmin.download_activity(
            activity_id, dl_fmt=self.garmin.ActivityDownloadFormat.ORIGINAL
        )
        return DownloadFitContentResponse(zip_data)


class BaseGarminConnectClientException(Exception):
    pass


class InvalidDate(BaseGarminConnectClientException):
    def __init__(self, value):
        self.value = value
