import warnings
from collections.abc import Generator
from functools import cached_property, lru_cache
from typing import Any, Sequence

import requests

from . import list_activities_response_filters

__all__ = [
    "ActivityDetailsResponse",
    "SegmentEffortNotFound",
    "StreamsResponse",
    "ListActivitiesResponse",
    "UpdatedActivity",
    "CreatedActivity",
    "StreamNotFound",
    "SegmentResponse",
]


class BaseJsonResponse:
    def __init__(self, raw_response: requests.Response):
        # `raw_response` is the raw HTTP response received by `requests` lib.
        self.raw_response = raw_response

    @cached_property
    def data(self):
        # `data` is the JSON content included in the raw HTTP response.
        return self.raw_response.json()


class ListActivitiesResponse(BaseJsonResponse):
    """
    Raw response data format: see "docs/activity summary.md"
     or https://github.com/puntonim/sport-monorepo/blob/main/libs/strava-client/docs/activity%20summary.md
    """

    # IMP: do NOT assign values to INSTANCE attrs here at class-level, but only type
    #  annotations. If you assign values they become CLASS attrs.

    data: list[dict[str, Any]]

    def filter_by_activity_type(
        self,
        # All types described in https://github.com/puntonim/sport-monorepo/blob/main/libs/strava-db-models/strava_db_models/strava_db_models.py#L106.
        activity_type: str,
    ) -> Generator[dict]:
        """
        Filter the collected activities summaries by activity_type.
        Note: it's obsolete, instead use .filter(activity_type=...).
        Note: all types described in https://github.com/puntonim/sport-monorepo/blob/main/libs/strava-db-models/strava_db_models/strava_db_models.py#L106.

        Note: this is just a Python filtering (NOT supported by Strava API).
        """
        warnings.warn("use filter(activity_type=...)", DeprecationWarning)
        return self.filter(activity_type=activity_type)

    def filter(
        self,
        title_contains: str | None = None,
        # All types described in StravaClient.STRAVA_ACTIVITY_TYPES.
        activity_type: str | None = None,
        start_latlng: tuple[float, float, int] | tuple[float, float] | None = None,
        end_latlng: tuple[float, float, int] | tuple[float, float] | None = None,
        location_visited_latlng: (
            tuple[float, float, int] | tuple[float, float] | None
        ) = None,
        # Meters (int). The original metric is float.
        distance_range: tuple[int, int] | None = None,
        # Seconds (int). The original metric is float.
        moving_time_range: tuple[int, int] | None = None,
        # Seconds (int). The original metric is float.
        elapsed_time_range: tuple[int, int] | None = None,
        # Meters (int). The original metric is float.
        elevation_gain_range: tuple[int, int] | None = None,
        # Meters (int). The original metric is float.
        elevation_highest_range: tuple[int, int] | None = None,
        # Meters (int). The original metric is float.
        elevation_lowest_range: tuple[int, int] | None = None,
        # km/h (float). The original metric is m/s, float.
        speed_avg_range: tuple[float, float] | None = None,
        # km/h (float). The original metric is m/s, float.
        speed_max_range: tuple[float, float] | None = None,
        # min/km (string like "4:45"). The original metric is speed avg in m/s, float.
        pace_avg_range: tuple[str, str] | None = None,
        # min/km (string like "4:45"). The original metric is speed max in m/s, float.
        pace_max_range: tuple[str, str] | None = None,
        # bpm (int). The original metric is float.
        hr_avg_range: tuple[int, int] | None = None,
        # bpm (int). The original metric is float.
        hr_max_range: tuple[int, int] | None = None,
    ) -> Generator[dict]:
        """
        Filter the collected activities summaries.

        Args:
            title_contains: filter by text included in the activity summary `name`
             (title), case insensitive.
             Eg. a string like "back, calisthenics".
            activity_type: filter by activity type included in the activity summary
             `type` or `sport_type`, case insensitive.
             All types described in StravaClient.STRAVA_ACTIVITY_TYPES.
             Eg. a string like "ride" | "MountainBikeRide" | "WeightTraining".
            start_latlng: filter by activity starting location, within a certain
             distance, as tuple in the form (lat, lon, distance*).
             Distance is optional and its default value is 250 meters.
             Eg. a tuple like (38.898, -77.037, 100)
             Examples of lat and long:
               white_house = (38.898, -77.037)
               eiffel_tower = (48.858, 2.294)
               bsas = (-34.83333, -58.5166646)  # Ezeiza Airport (Buenos Aires, Argentina).
               paris = (49.0083899664, 2.53844117956)  # C. de Gaulle Airport (Paris, France).
               newport_ri = (41.49008, -71.312796)
               cleveland_oh = (41.499498, -81.695391)
            end_latlng: same as start_latlng but for activity ending location.
            location_visited_latlng: same as start_latlng but for any location visited
             during the activity.
            distance_range: filter by distance range as tuple of 2 ints to define the
             distance range inclusive, in meters.
             Eg. (9800, 10500) for a 10km run.
            moving_time_range: filter by moving time range as tuple of 2 ints to define
             the moving time range inclusive, in minutes.
             Eg. (60, 120) for a run.
            elapsed_time_range: same as moving_time_range but for elapsed time.
            elevation_gain_range: filter by elevation gain range as tuple of 2 ints to
             define the elevation gain range inclusive, in meters.
             Eg. (600, 1000) for a ride.
            elevation_highest_range: same as elevation_gain_range but for the highest
             elevation visited during the activity.
            elevation_lowest_range: same as elevation_gain_range but for the lowest
             elevation visited during the activity.
            speed_avg_range: filter by average speed range as tuple of 2 floats to
             define the average speed range inclusive, in km/h.
             Eg. (14.2, 20.0) for a ride.
            speed_max_range: same as speed_avg_range but for max speed.
            pace_avg_range: same as speed_avg_range but for average pace in min/km.
             Eg. ("5:30", "5:45") for a run.
            pace_max_range: same as speed_avg_range but for max pace in min/km.
             Eg. ("5:30", "5:45") for a run.
            hr_avg_range: filter by average heart rate range as tuple of 2 ints to
             define the average heart rate range inclusive, in bpm.
             Eg. (112, 180)
            hr_max_range: same as hr_avg_range but for max heaty rate.
        """
        _ = list_activities_response_filters
        for summary in self.data:
            summary: dict

            if not _.does_title_contains_filter_match(title_contains, summary):
                continue
            if not _.does_activity_type_filter_match(activity_type, summary):
                continue
            if not _.does_start_latlng_filter_match(start_latlng, summary):
                continue
            if not _.does_end_latlng_filter_match(end_latlng, summary):
                continue
            if not _.does_location_visited_latlng_filter_match(
                location_visited_latlng, summary
            ):
                continue
            if not _.does_distance_range_filter_match(distance_range, summary):
                continue
            if not _.does_moving_time_range_filter_match(moving_time_range, summary):
                continue
            if not _.does_elapsed_time_range_filter_match(elapsed_time_range, summary):
                continue
            if not _.does_elevation_gain_range_filter_match(
                elevation_gain_range, summary
            ):
                continue
            if not _.does_elevation_highest_range_filter_match(
                elevation_highest_range, summary
            ):
                continue
            if not _.does_elevation_lowest_range_filter_match(
                elevation_lowest_range, summary
            ):
                continue
            if not _.does_speed_avg_range_filter_match(speed_avg_range, summary):
                continue
            if not _.does_speed_max_range_filter_match(speed_max_range, summary):
                continue
            if not _.does_pace_avg_range_filter_match(pace_avg_range, summary):
                continue
            if not _.does_pace_max_range_filter_match(pace_max_range, summary):
                continue
            if not _.does_hr_avg_range_filter_match(hr_avg_range, summary):
                continue
            if not _.does_hr_max_range_filter_match(hr_max_range, summary):
                continue

            yield summary


class UpdatedActivity(BaseJsonResponse):
    # IMP: do NOT assign values to INSTANCE attrs here at class-level, but only type
    #  annotations. If you assign values they become CLASS attrs.
    data: dict[str, Any]


class CreatedActivity(BaseJsonResponse):
    # IMP: do NOT assign values to INSTANCE attrs here at class-level, but only type
    #  annotations. If you assign values they become CLASS attrs.
    data: dict[str, Any]


class ActivityDetailsResponse(BaseJsonResponse):
    """
    Raw response data format: see "docs/activity details.md"
     or https://github.com/puntonim/sport-monorepo/blob/main/libs/strava-client/docs/activity%20details.md
    """

    # IMP: do NOT assign values to INSTANCE attrs here at class-level, but only type
    #  annotations. If you assign values they become CLASS attrs.
    data: dict[str, Any]

    def get_segment_efforts(
        self, segments_filter: Sequence[int | str] | None = None
    ) -> list[dict]:
        """
        Get segment efforts.
        Optionally use the arg segments_filter to get only certain segments identified
         by either ids [int] or names [str].
        Mind that there can be multiple efforts for the same segment, for example
         when I run 6x300m.

        Args:
            segments_filter list[int | str] | None: a list of ints or strings.
             Eg.: [30559592, 14418673]
             Eg.: ["Pista Blu Dobbiaco"]
             Eg.: ["Pista Blu Dobbiaco", 14418673, 123345]
        """
        if not segments_filter:
            return self.data.get("segment_efforts", [])

        # Make all segments_filter lower case.
        filters = tuple(x.lower() if isinstance(x, str) else x for x in segments_filter)

        return_data: list[dict] = list()
        # Each item in the list `return_data` is a dict that contains segment efforts
        #  data with these interesting attrs (and many others):
        #     "id": 3238160405689973068
        #     "resource_state": 2
        #     "name": "ritorno - MONTEred new ciclabile"
        #     "elapsed_time": 2748
        #     "moving_time": 2714
        #     "start_date": "2024-06-18T09:21:40Z"
        #     "start_date_local": "2024-06-18T11:21:40Z"
        #     "distance": 10160.9
        #     "start_index": 751
        #     "end_index": 1641
        #     "average_heartrate": 133.7
        #     "max_heartrate": 146.0
        #     "segment": {
        #         "id": 22549796,
        #         "resource_state": 2,
        #         "name": "ritorno - MONTEred new ciclabile",
        #         "activity_type": "Ride",
        #         "distance": 378.1,
        #         "average_grade": 0.9,
        #         "maximum_grade": 3.6,
        #         "elevation_high": 284.5,
        #         "elevation_low": 280.1,
        #         "start_latlng": [45.714189, 9.685557],
        #         "end_latlng": [45.714255, 9.69003],
        #         "elevation_profile": None,
        #         "elevation_profiles": None,
        #         "climb_category": 0,
        #         "city": "Bergamo",
        #         "state": "Lombardia",
        #         "country": "Italy",
        #         "private": False,
        #         "hazardous": False,
        #         "starred": False,
        #     }

        _found = list()
        for segment_effort in self.data.get("segment_efforts", []):
            _segment: dict = segment_effort["segment"]
            if (_segment["id"] in filters) or (_segment["name"].lower() in filters):
                _found.append(_segment["id"])
                _found.append(_segment["name"].lower())
                return_data.append(segment_effort)

        # Make sure that all requested segments were found.
        for filter in filters:
            if filter not in _found:
                raise SegmentEffortNotFound(filter)

        return return_data


class StreamsResponse(BaseJsonResponse):
    """
    Raw response data format: see "docs/streams.md"
     or https://github.com/puntonim/sport-monorepo/blob/main/libs/strava-client/docs/streams.md
    """

    # IMP: do NOT assign values to INSTANCE attrs here at class-level, but only type
    #  annotations. If you assign values they become CLASS attrs.
    data: list[dict]

    @lru_cache
    def _validate_data_size(self):
        # This is the original size of the data collected by the Garmin watch.
        original_dataset_size = self.get_original_dataset_size()

        for d in self.data:
            # This is the size of this dataset.
            stream_size = len(d["data"])
            if stream_size != original_dataset_size:
                stream_name = d["type"]
                raise StreamSizeError(stream_name, stream_size, original_dataset_size)

    def _get_stream_by_name(self, name: str) -> list:
        self._validate_data_size()

        stream_data = list()
        for d in self.data:
            if d["type"] == name:
                stream_data = d["data"]
        if not stream_data:
            raise StreamNotFound(name)
        return stream_data

    @lru_cache
    def get_original_dataset_size(self) -> int:
        return self.data[0]["original_size"]

    def get_elapsed_time_stream(self) -> list:
        return self._get_stream_by_name("time")

    def get_distance_stream(self) -> list:
        return self._get_stream_by_name("distance")

    def get_latlng_stream(self) -> list:
        return self._get_stream_by_name("latlng")

    def get_altitude_stream(self) -> list:
        return self._get_stream_by_name("altitude")

    def get_heartrate_stream(self) -> list:
        return self._get_stream_by_name("heartrate")

    def get_moving_stream(self) -> list:
        return self._get_stream_by_name("moving")

    def compute_moving_time_stream(self) -> list:
        """
        To compute moving times:
         - we traverse all the `elapsed time` datapoints
         - and if the `moving` datapoint at that same index is not moving
         - then we compute the time diff with the prev `elapsed time` datapoint
         - and subtract that time diff to all next `elapsed time` datapoints
         - but only if that time diff is <13 secs (so the athlete was still
            for >13 secs; that's what Garmin seems to do)

        Note that when plotting a datapoint over distance (eg. HR over distance), so
         when the x-axis is distance, then `moving time` datapoints are useless. All
         Strava charts are over distance.
        But Garmin Connect lets you choose to plot data over distance or time. And
         when choosing time, it uses moving times on the x-axis (rather than
         elapsed times).
        """
        # Copy the dataset so we can modify it.
        moving_time_stream = self.get_elapsed_time_stream()[:]
        moving_stream = self.get_moving_stream()
        for i in range(2, len(moving_time_stream)):
            # If the datapoint was not moving.
            if moving_stream[i] is False:
                # Get how long (seconds) the athlete was not moving (so the time diff
                #  the prev datapoint).
                diff = moving_time_stream[i] - moving_time_stream[i - 1]
                # If the diff is <= 13 secs, just ignore it .
                # That's what Garmin seems to, even though the resulting graphs are not
                #  100% matching but they are very close.
                if diff < 13.0:
                    continue
                # Subtract the time diff to all next datapoints.
                for j in range(i, len(moving_time_stream)):
                    # print(f"subtracting {diff} for index {j}")
                    moving_time_stream[j] -= diff
        return moving_time_stream


class SegmentResponse(BaseJsonResponse):
    """
    Raw response data format: see "docs/segment.md"
     or https://github.com/puntonim/sport-monorepo/blob/main/libs/strava-client/docs/segment.md
    """

    # IMP: do NOT assign values to INSTANCE attrs here at class-level, but only type
    #  annotations. If you assign values they become CLASS attrs.
    data: dict[str, Any]


class BaseJsonResponseException(Exception):
    pass


class SegmentEffortNotFound(BaseJsonResponseException):
    def __init__(self, segment_id_or_name: int | str):
        self.segment_id_or_name = segment_id_or_name


class StreamNotFound(BaseJsonResponseException):
    def __init__(self, stream_name: str):
        self.stream_name = stream_name


class StreamSizeError(BaseJsonResponseException):
    def __init__(self, stream_name, stream_size, original_dataset_size):
        self.stream_name = stream_name
        self.stream_size = stream_size
        self.original_dataset_size = original_dataset_size
