from collections import defaultdict
from functools import cached_property, lru_cache
from typing import Any

import requests

__all__ = [
    "ActivityDetailsResponse",
    "SegmentEffortNotFound",
    "StreamsResponse",
    "SegmentNameMismatch",
    "ListActivitiesResponse",
    "UpdatedActivity",
    "CreatedActivity",
    "StreamNotFound",
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
    # IMP: do NOT assign values to INSTANCE attrs here at class-level, but only type
    #  annotations. If you assign values they become CLASS attrs.

    data: list[dict[str, Any]]

    def filter_by_activity_type(self, activity_type: str):
        """
        Filter by activity_type.

        Note: this is just a Python filtering (NOT supported by Strava API).
        """
        for activity in self.data:
            activity: dict
            if (
                activity.get("type") == activity_type
                or activity.get("sport_type") == activity_type
            ):
                yield activity


class UpdatedActivity(BaseJsonResponse):
    # IMP: do NOT assign values to INSTANCE attrs here at class-level, but only type
    #  annotations. If you assign values they become CLASS attrs.
    data: dict[str, Any]


class CreatedActivity(BaseJsonResponse):
    # IMP: do NOT assign values to INSTANCE attrs here at class-level, but only type
    #  annotations. If you assign values they become CLASS attrs.
    data: dict[str, Any]


class ActivityDetailsResponse(BaseJsonResponse):
    # IMP: do NOT assign values to INSTANCE attrs here at class-level, but only type
    #  annotations. If you assign values they become CLASS attrs.
    data: dict[str, Any]

    def get_segment_efforts(
        self, segments_filter: list[tuple[int, str]] | None = None
    ) -> list[dict]:
        """
        Get segment efforts.
        Optionally use the arg segments_filter to get only certain segments identified
         by ids [int] and their name [str].
        Mind that there can be multiple efforts for the same segment, for example
         when I run 6x300m.

        Args:
            segments_filter list[tuple] | None: a list of tuples of 2 items:
             segment_id [int], segment_name [str].
             Eg.: list((30559592, "Pista Blu Dobbiaco"), (14418673, "Selvino Fontanella"))
        """
        if not segments_filter:
            return self.data.get("segment_efforts", [])

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

        # First collect all indices and segment ids, so it's easier to manipulate.
        _id_and_indices: dict[int, list[int]] = defaultdict(list)
        for i in range(len(self.data.get("segment_efforts", []))):
            _segment_effort: dict = self.data["segment_efforts"][i]
            _segment: dict = _segment_effort["segment"]
            _id_and_indices[_segment["id"]].append(i)

        # Get all target segments given in segments_filter.
        for _segment_filter in segments_filter:
            _segments_filter_id, _segments_filter_name = _segment_filter
            if not _id_and_indices.get(_segments_filter_id):
                raise SegmentEffortNotFound(_segments_filter_id, _segments_filter_name)

            found = False
            for ix in _id_and_indices.get(_segments_filter_id):
                _data = self.data["segment_efforts"][ix]
                if _data["name"].lower() != _segments_filter_name.lower():
                    raise SegmentNameMismatch(
                        _segments_filter_id, _segments_filter_name, _data["name"]
                    )
                return_data.append(_data)
                found = True
            if not found:
                raise SegmentEffortNotFound(_segments_filter_id, _segments_filter_name)

        return return_data


class StreamsResponse(BaseJsonResponse):
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

    def get_moving_time_stream(self) -> list:
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


class BaseJsonResponseException(Exception):
    pass


class SegmentEffortNotFound(BaseJsonResponseException):
    def __init__(self, segment_id: int, segment_name: str):
        self.segment_id = segment_id
        self.segment_name = segment_name


class SegmentNameMismatch(BaseJsonResponseException):
    def __init__(self, segment_id: int, segment_name: str, actual_name: str):
        self.segment_id = segment_id
        self.segment_name = segment_name
        self.actual_name = actual_name


class StreamNotFound(BaseJsonResponseException):
    def __init__(self, stream_name: str):
        self.stream_name = stream_name


class StreamSizeError(BaseJsonResponseException):
    def __init__(self, stream_name, stream_size, original_dataset_size):
        self.stream_name = stream_name
        self.stream_size = stream_size
        self.original_dataset_size = original_dataset_size
