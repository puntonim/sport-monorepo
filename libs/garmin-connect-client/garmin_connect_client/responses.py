import io
import zipfile
from collections.abc import Generator
from functools import lru_cache
from pathlib import Path
from typing import Any

from garmin_fit_sdk import Decoder, Profile, Stream

__all__ = [
    "ActivityDetailsResponse",
    "ListActivitiesResponse",
    "ActivitySummaryResponse",
    "DownloadFitContentResponse",
    "ActivityTypedSplitsResponse",
    "SearchActivitiesResponse",
]


class BaseGarminResponse:
    def __init__(self, data: Any):
        # `data` is the raw response data received by `garminconnect` lib.
        self.data = data


class ListActivitiesResponse(BaseGarminResponse):
    """
    See docstring in GarminConnectClient.list_activities().
    """

    # IMP: do NOT assign values to INSTANCE attrs here at class-level, but only type
    #  annotations. If you assign values they become CLASS attrs.
    data: dict[str, dict]

    @lru_cache
    def get_activities(self) -> Generator[dict]:
        for x in self.data["ActivitiesForDay"]["payload"]:
            x: dict[str, Any]
            yield x


class ActivitySummaryResponse(BaseGarminResponse):
    """
    See docstring in GarminConnectClient.get_activity_summary().
    """

    # IMP: do NOT assign values to INSTANCE attrs here at class-level, but only type
    #  annotations. If you assign values they become CLASS attrs.
    data: dict[str, Any]

    @property
    def summary(self) -> dict:
        return self.data["summaryDTO"]

    def has_heart_rate_monitor(self):
        for sensor in self.data["metadataDTO"].get("sensors") or []:
            # Sensor is a dict like:
            # {
            #     "manufacturer": "GARMIN",
            #     "serialNumber": 3511385941,
            #     "sku": "006-B4606-00",
            #     "fitProductNumber": 4606,
            #     "sourceType": "ANTPLUS",
            #     "antplusDeviceType": "HEART_RATE",
            #     "softwareVersion": 3.9,
            #     "batteryStatus": "OK",
            # }
            for val in sensor.values():
                if isinstance(val, str) and "HEART_RATE".lower() in val.lower():
                    return True
        return False


class ActivityDetailsResponse(BaseGarminResponse):
    """
    See docstring in GarminConnectClient.get_activity_details().
    """

    # IMP: do NOT assign values to INSTANCE attrs here at class-level, but only type
    #  annotations. If you assign values they become CLASS attrs.

    data: dict[str, Any] | None
    _relevant_metric_descriptors: dict[str, int]

    ## Public attrs annotations.
    activity_id: int
    # The tot number datapoints in the original dataset collected by the device.
    original_dataset_size: int
    # The number of datapoints in this response: it is <= `original_dataset_size`
    #  as it can be a subset of the original dataset collected by the device.
    streams_size: int

    ## Interesting metrics.
    # There are more like directGradeAdjustedSpeed, directVerticalSpeed,
    #  directGroundContactTime, ...
    # Timestamp GMT when the datapoint was collected.
    _ts_stream: list[float]  # directTimestamp in gmt [s], eg. 1742663472000.0.
    # Seconds elapsed since the start. It's the diff between timestamps.
    _elapsed_time_stream: list[float]  # sumElapsedDuration [s], eg. 3996.0.
    # Seconds since the start, excluding the time when the device was paused.
    # Note that the device might not have been paused, but the athlete be still (because
    #  the athlete forgot to pause).
    # Note: it's the x-axis used in Garmin Connect website for charts over time,
    #  for example for the chart HR over time.
    _non_paused_time_stream: list[float]  # sumDuration [s], eg. 3996.0.
    # Seconds since start, when the athlete was actually moving.
    # It's computed checking the coords and it is the most reliable stream for the
    #  moving time, as the device might not have been properly paused when the athlete
    #  was still.
    _moving_time_stream: list[float]  # sumMovingDuration [s], eg. 3993.0.
    _distance_stream: list[float]  # sumDistance [m], eg. 10100.8203125.
    _speed_stream: list[float]  # directSpeed [mps], eg. 4.198999881744385.
    _lat_stream: list[float]  # directLatitude, eg. 44.16305732913315.
    _lng_stream: list[float]  # directLongitude, eg. 7.572167655453086.
    _altitude_stream: list[float]  # directElevation [m], eg. 1476.4000244140625.
    _heartrate_stream: list[float]  # directHeartRate [bpm], eg. 138.0.

    _all_stream_names: list[str] = (
        "_ts_stream",
        "_elapsed_time_stream",
        "_non_paused_time_stream",
        "_moving_time_stream",
        "_distance_stream",
        "_speed_stream",
        "_lat_stream",
        "_lng_stream",
        "_altitude_stream",
        "_heartrate_stream",
    )

    def __init__(self, data: dict, do_keep_raw_data: bool = False):
        """

        Args:
            data [dict]: the raw response data received by `garminconnect` lib.
            do_keep_raw_data: True to keep the raw response data. It can be large.
        """
        self.data = None

        self._parse_raw_data(data)

        # Store data only if requested. It duplicates data and it can be large.
        if not do_keep_raw_data:
            del data
        else:
            super().__init__(data)

    def get_ts_stream(self) -> list:
        # I've never found None values in this stream.
        return self._ts_stream

    def get_elapsed_time_stream(self) -> list:
        # I've never found None values in this stream.
        return self._elapsed_time_stream

    def get_non_paused_time_stream(self) -> list:
        # I've never found None values in this stream.
        return self._non_paused_time_stream

    def get_moving_time_stream(self) -> list:
        # I've never found None values in this stream.
        return self._moving_time_stream

    def get_distance_stream(self) -> list:
        # I've never found None values in this stream.
        return self._distance_stream

    def get_speed_stream(self, do_remove_none_values: bool = False) -> list:
        # I found None values in this stream.
        if do_remove_none_values:
            return [x for x in self._speed_stream if x is not None]
        return self._speed_stream

    def get_lat_stream(self, do_remove_none_values: bool = False) -> list:
        # I found None values in this stream.
        if do_remove_none_values:
            return [x for x in self._lat_stream if x is not None]
        return self._lat_stream

    def get_lng_stream(self, do_remove_none_values: bool = False) -> list:
        # I found None values in this stream.
        if do_remove_none_values:
            return [x for x in self._lng_stream if x is not None]
        return self._lng_stream

    def get_altitude_stream(self) -> list:
        # I've never found None values in this stream.
        return self._altitude_stream

    def get_heartrate_stream(self, do_remove_none_values: bool = False) -> list:
        # I found None values in this stream.
        if do_remove_none_values:
            return [x for x in self._heartrate_stream if x is not None]
        return self._heartrate_stream

    def _parse_raw_data(self, data: dict[str, Any]):
        ## Parse basic attrs.
        self.activity_id = data["activityId"]
        # The tot number datapoints in the original dataset collected by the device.
        self.original_dataset_size = data["totalMetricsCount"]
        # The number of datapoints in this response: it is <= `original_dataset_size`
        #  as it can be a subset of the original dataset collected by the device.
        self.streams_size = data["metricsCount"]

        ## Parse the metrics descriptors, which have different order in every response.
        self._parse_relevant_metric_descriptors(data["metricDescriptors"])

        ## Parse the relevant metrics (and ignore the rest).
        self._parse_relevant_metrics(data["activityDetailMetrics"])

    def _parse_relevant_metric_descriptors(self, metric_descriptors_attr: list[dict]):
        self._relevant_metric_descriptors = dict()
        for m in metric_descriptors_attr:
            if m["key"] == "sumElapsedDuration":
                self._relevant_metric_descriptors["elapsed_time_stream"] = m[
                    "metricsIndex"
                ]
            elif m["key"] == "sumMovingDuration":
                self._relevant_metric_descriptors["moving_time_stream"] = m[
                    "metricsIndex"
                ]
            elif m["key"] == "sumDuration":
                self._relevant_metric_descriptors["non_paused_time_stream"] = m[
                    "metricsIndex"
                ]
            elif m["key"] == "directTimestamp":
                self._relevant_metric_descriptors["ts_stream"] = m["metricsIndex"]
            elif m["key"] == "sumDistance":
                self._relevant_metric_descriptors["distance_stream"] = m["metricsIndex"]
            elif m["key"] == "directSpeed":
                self._relevant_metric_descriptors["speed_stream"] = m["metricsIndex"]
            elif m["key"] == "directLatitude":
                self._relevant_metric_descriptors["lat_stream"] = m["metricsIndex"]
            elif m["key"] == "directLongitude":
                self._relevant_metric_descriptors["lng_stream"] = m["metricsIndex"]
            elif m["key"] == "directElevation":
                self._relevant_metric_descriptors["altitude_stream"] = m["metricsIndex"]
            elif m["key"] == "directHeartRate":
                self._relevant_metric_descriptors["heartrate_stream"] = m[
                    "metricsIndex"
                ]

    def _parse_relevant_metrics(
        self, activity_detail_metrics_attr: list[dict[str, list[float | None]]]
    ):
        # Initialize all streams vars to en empty list.
        for stream_name in self._all_stream_names:
            setattr(self, stream_name, [])

        # Fill all streams lists.
        for metric in activity_detail_metrics_attr:
            x: list = metric["metrics"]
            self._elapsed_time_stream.append(
                x[self._relevant_metric_descriptors["elapsed_time_stream"]]
            )
            self._moving_time_stream.append(
                x[self._relevant_metric_descriptors["moving_time_stream"]]
            )
            self._non_paused_time_stream.append(
                x[self._relevant_metric_descriptors["non_paused_time_stream"]]
            )
            self._ts_stream.append(x[self._relevant_metric_descriptors["ts_stream"]])
            self._distance_stream.append(
                x[self._relevant_metric_descriptors["distance_stream"]]
            )
            self._speed_stream.append(
                x[self._relevant_metric_descriptors["speed_stream"]]
            )
            self._lat_stream.append(x[self._relevant_metric_descriptors["lat_stream"]])
            self._lng_stream.append(x[self._relevant_metric_descriptors["lng_stream"]])
            self._altitude_stream.append(
                x[self._relevant_metric_descriptors["altitude_stream"]]
            )
            self._heartrate_stream.append(
                x[self._relevant_metric_descriptors["heartrate_stream"]]
            )


class ActivityTypedSplitsResponse(BaseGarminResponse):
    """
    See docstring in GarminConnectClient.get_activity_splits().
    """

    # IMP: do NOT assign values to INSTANCE attrs here at class-level, but only type
    #  annotations. If you assign values they become CLASS attrs.
    data: dict[str, Any]

    @property
    def splits(self) -> dict:
        """
        ** Typed ** splits are useful when the activity is a workout with:
         - automatica laps: eg. run for 2 mins at a certain pace;
         - or laps started by the athlete the lap button is pressed: eg. during
            a 6x300m run.

        I verified that the splits started with a lap button press have:
         "type": "INTERVAL_ACTIVE".
        And you can get them with: response.get_interval_active_splits()

        However, some activities, when I never pressed the lap button, still have
         1 single INTERVAL_ACTIVE split which is the whole activity.
        """
        return self.data["splits"]

    def get_interval_active_splits(self) -> Generator[dict]:
        """
        Get the splits started with a lap button press.

        They have:
         "type": "INTERVAL_ACTIVE".
        However, some activities, when I never pressed the lap button, still have
         1 single INTERVAL_ACTIVE split which is the whole activity.
        """
        for split in self.splits:
            if split["type"] == "INTERVAL_ACTIVE":
                yield split


class SearchActivitiesResponse(BaseGarminResponse):
    """
    See docstring in GarminConnectClient.search_activity().
    """

    # IMP: do NOT assign values to INSTANCE attrs here at class-level, but only type
    #  annotations. If you assign values they become CLASS attrs.
    data: list[dict[str, Any]]


class DownloadFitContentResponse(BaseGarminResponse):
    # IMP: do NOT assign values to INSTANCE attrs here at class-level, but only type
    #  annotations. If you assign values they become CLASS attrs.

    # Zip bytes.
    data: bytes

    def save_to_file(self, zip_file_path: Path | str):
        with open(zip_file_path, "wb") as fb:
            fb.write(self.data)

    def get_stream(self, stream_name: str):
        if stream_name not in (
            "timestamp",
            "position_lat",
            "position_long",
            "distance",
            "enhanced_speed",
            "enhanced_altitude",
            "heart_rate",
            "temperature",
        ):
            raise DownloadFitContentResponseError(f"Stream name unknown: {stream_name}")

        content = None

        with zipfile.ZipFile(io.BytesIO(self.data)) as zip_file:
            file_names = zip_file.namelist()
            if len(file_names) < 1:
                raise DownloadFitContentResponseError(
                    "No file found in the downloaded zip file"
                )
            elif len(file_names) > 1:
                raise DownloadFitContentResponseError(
                    "Many files found in the downloaded zip file"
                )
            file_name = file_names[0]
            with zip_file.open(file_name) as fit_file:
                content = fit_file.read()

        # stream = Stream.from_file("~/Desktop/18606916834_ACTIVITY.fit")
        stream = Stream.from_bytes_io(io.BytesIO(content))
        decoder = Decoder(stream)

        data_stream = []

        def mesg_listener(mesg_num, message):
            if mesg_num == Profile["mesg_num"]["RECORD"]:
                # `message` is a dict like:
                # {
                #     "timestamp": datetime.datetime(
                #         2025, 4, 18, 7, 17, 9, tzinfo=datetime.timezone.utc
                #     ),
                #     "position_lat": 545465659,
                #     "position_long": 115541086,
                #     "distance": 0.0,
                #     "enhanced_speed": 0.205,
                #     "enhanced_altitude": 289.79999999999995,
                #     "grit": 0.0,
                #     "flow": 0.0,
                #     "heart_rate": 54,
                #     "temperature": 25,
                #     107: 0,
                #     134: 100,
                #     135: 1,
                #     136: 51,
                #     137: 99,
                #     138: 99,
                #     143: 83,
                #     144: 54,
                # }
                data = message.get(stream_name)
                if data:
                    data_stream.append(data)

        messages, errors = decoder.read(mesg_listener=mesg_listener)

        if len(errors) > 0:
            raise DownloadFitContentResponseError(
                f"Error while decoding fit file: {errors}"
            )

        return data_stream


class BaseGarminResponseException(Exception):
    pass


class DownloadFitContentResponseError(BaseGarminResponseException):
    pass
