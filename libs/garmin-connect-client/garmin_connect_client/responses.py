from functools import lru_cache
from typing import Any

__all__ = [
    "ActivityDetailsResponse",
    "ListActivitiesResponse",
    "ActivitySummaryResponse",
]


class BaseGarminResponse:
    def __init__(self, data: Any):
        # `data` is the raw response data received by `garminconnect` lib.
        self.data = data


class ListActivitiesResponse(BaseGarminResponse):
    data: [str, dict]

    @lru_cache
    def get_activities(self):
        for x in self.data["ActivitiesForDay"]["payload"]:
            x: dict[str, Any]
            yield x


class ActivitySummaryResponse(BaseGarminResponse):
    data: [str, Any]


class ActivityDetailsResponse(BaseGarminResponse):
    """
    Args:
        data [dict]: see real example in `docs/activity details.md`.
         Format:
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
    """

    data: dict[str, Any] | None = None
    _relevant_metric_descriptors: dict[str, int]

    ## Public attrs.
    activity_id: int
    # The tot number datapoints in the original dataset collected by the device.
    original_size: int
    # The number of datapoints in this response: it is <= `original_size`
    #  as it can be a subset of the original dataset collected by the device.
    streams_size: int
    ## Interesting metrics.
    # There are more like directGradeAdjustedSpeed, directVerticalSpeed,
    #  directGroundContactTime, ...
    # Timestamp GMT when the datapoint was collected.
    ts_stream: list[float] = []  # directTimestamp in gmt [s], eg. 1742663472000.0.
    # Seconds elapsed since the start. It's the diff between timestamps.
    elapsed_time_stream: list[float] = []  # sumElapsedDuration [s], eg. 3996.0.
    # Seconds since the start, excluding the time when the device was paused.
    # Note that the device might not have been paused, but the athlete be still (because
    #  the athlete forgot to pause).
    # Note: it's the x-axis used in Garmin Connect website for charts over time,
    #  for example for the chart HR over time.
    non_paused_time_stream: list[float] = []  # sumDuration [s], eg. 3996.0.
    # Seconds since start, when the athlete was actually moving.
    # It's computed checking the cioords and it is the most realible stream for the
    #  moving time, as the device might not have been propelry paused when the athlete
    #  was still.
    moving_time_stream: list[float] = []  # sumMovingDuration [s], eg. 3993.0.
    distance_stream: list[float] = []  # sumDistance [m], eg. 10100.8203125.
    speed_stream: list[float] = []  # directSpeed [mps], eg. 4.198999881744385.
    lat_stream: list[float] = []  # directLatitude, eg. 44.16305732913315.
    lng_stream: list[float] = []  # directLongitude, eg. 7.572167655453086.
    altitude_stream: list[float] = []  # directElevation [m], eg. 1476.4000244140625.
    heartrate_stream: list[float] = []  # directHeartRate [bpm], eg. 138.0.

    def __init__(self, data: dict, do_keep_raw_data: bool = False):
        """

        Args:
            data [dict]: the raw response data received by `garminconnect` lib.
            do_keep_raw_data: True to keep the raw response data. It can be large.
        """
        self._parse_raw_data(data)

        # Store data only if requested. It duplicates data and it can be large.
        if not do_keep_raw_data:
            del data
        else:
            super().__init__(data)

    def _parse_raw_data(self, data: dict[str, Any]):
        ## Parse basic attrs.
        self.activity_id = data["activityId"]
        # The tot number datapoints in the original dataset collected by the device.
        self.original_size = data["totalMetricsCount"]
        # The number of datapoints in this response: it is <= `original_size`
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
        for metric in activity_detail_metrics_attr:
            x: list = metric["metrics"]
            self.elapsed_time_stream.append(
                x[self._relevant_metric_descriptors["elapsed_time_stream"]]
            )
            self.moving_time_stream.append(
                x[self._relevant_metric_descriptors["moving_time_stream"]]
            )
            self.non_paused_time_stream.append(
                x[self._relevant_metric_descriptors["non_paused_time_stream"]]
            )
            self.ts_stream.append(x[self._relevant_metric_descriptors["ts_stream"]])
            self.distance_stream.append(
                x[self._relevant_metric_descriptors["distance_stream"]]
            )
            self.speed_stream.append(
                x[self._relevant_metric_descriptors["speed_stream"]]
            )
            self.lat_stream.append(x[self._relevant_metric_descriptors["lat_stream"]])
            self.lng_stream.append(x[self._relevant_metric_descriptors["lng_stream"]])
            self.altitude_stream.append(
                x[self._relevant_metric_descriptors["altitude_stream"]]
            )
            self.heartrate_stream.append(
                x[self._relevant_metric_descriptors["heartrate_stream"]]
            )
