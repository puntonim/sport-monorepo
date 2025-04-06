from typing import Any


class ActivityDetailsResponse:
    def __init__(
        self, raw_response: dict[str, Any], do_keep_raw_response: bool = False
    ):
        self.activity_id = None
        # The tot number of metrics datapoints collected by the watch.
        self.original_metrics_data_count = None
        # The number of metrics datapoints in this response: it is <= original_metrics_data_count
        #  as it can be a subset of all datapoints.
        self.metrics_data_count = None
        # The actual metrics.
        # Each metric is a tuple.
        # The order and the meaning is defined in self.metrics_cols.
        self.metrics: list[tuple] = None
        self.metrics_cols = (
            "ts",  # GMT.
            "hr",  # bpm.
            "duration",  # sec.
            "distance",  # meter.
            "elevation",  # meter.
            "speed",  # mps.
        )

        self._parse_raw_response(raw_response)

        if not do_keep_raw_response:
            del raw_response
        else:
            self.raw_response = raw_response

    def _parse_raw_response(self, raw_response: dict[str, Any]):
        ## Parse basic attrs.
        self.activity_id = raw_response["activityId"]
        # The tot number of metrics datapoints collected by the watch.
        self.original_metrics_data_count = raw_response["totalMetricsCount"]
        # The number of metrics datapoints in this response: it is <= original_metrics_data_count
        #  as it can be a summary of all datapoints.
        self.metrics_data_count = raw_response["metricsCount"]
        self.metrics = None

        ## Parse the metrics descriptors, which have different order in every response.
        self._parse_relevant_metric_descriptors(raw_response["metricDescriptors"])

        ## Parse the relevant metrics (and ignore the rest).
        self._parse_relevant_metrics(raw_response["activityDetailMetrics"])

    def _parse_relevant_metric_descriptors(self, metric_descriptors_attr: list[dict]):
        data = dict()
        for metric in metric_descriptors_attr:
            if metric["key"] == "directTimestamp":  # GMT.
                data["ts"] = metric["metricsIndex"]
            elif metric["key"] == "directHeartRate":  # bpm.
                data["hr"] = metric["metricsIndex"]
            elif metric["key"] == "sumDuration":  # sec.
                data["duration"] = metric["metricsIndex"]
            elif metric["key"] == "sumDistance":  # meter.
                data["distance"] = metric["metricsIndex"]
            elif metric["key"] == "directElevation":  # meter.
                data["elevation"] = metric["metricsIndex"]
            elif metric["key"] == "directSpeed":  # mps.
                data["speed"] = metric["metricsIndex"]

        self._relevant_metric_descriptors = data
        del data

    def _parse_relevant_metrics(
        self, activity_detail_metrics_attr: list[dict[str, list[float | None]]]
    ):
        data = list()
        for metric in activity_detail_metrics_attr:
            m: list = metric["metrics"]
            data.append(
                (
                    m[self._relevant_metric_descriptors["ts"]],  # GMT.
                    m[self._relevant_metric_descriptors["hr"]],  # bpm.
                    m[self._relevant_metric_descriptors["duration"]],  # sec.
                    m[self._relevant_metric_descriptors["distance"]],  # meter.
                    m[self._relevant_metric_descriptors["elevation"]],  # meter.
                    m[self._relevant_metric_descriptors["speed"]],  # mps.
                )
            )
        self.metrics = data
        del data
