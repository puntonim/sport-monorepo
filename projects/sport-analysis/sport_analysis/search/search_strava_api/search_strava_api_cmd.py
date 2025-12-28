from datetime import datetime

import datetime_utils
import speed_utils
from garmin_connect_client import GarminConnectClient
from strava_client import (
    ActivityDetailsResponse,
    ListActivitiesResponse,
    SegmentEffortNotFound,
    SegmentResponse,
    StravaClient,
)
from strava_client.strava_token_managers import (
    AwsParameterStoreStravaTokenManager,
    FakeTestStravaTokenManager,
    FileStravaTokenManager,
)

from ...base_cli_view import ConsoleAdapter
from ...conf import settings
from ..search_matching_activity_api import (
    ActivityNotFound,
    search_garmin_activity_matching_strava_activity_api,
)

__all__ = [
    "SearchStravaApiCmd",
    "KNOWN_STRAVA_SEGMENTS",
]

console = ConsoleAdapter()

KNOWN_STRAVA_SEGMENTS = {
    "selvino": 14418673,
    "stelvio": 15756100,
}
KNOWN_STRAVA_SEGMENTS_DATA = {
    14418673: dict(
        name="Selvino Fontanella",
        start_latlng=[45.745995, 9.762249],
        distance=10160.9,
        total_elevation_gain=587.9,
        activity_type="Ride",
    ),
    15756100: dict(
        name="Passo Stelvio (via Bormio)",
        start_latlng=[46.47783, 10.367602],
        distance=19481.1,
        total_elevation_gain=1467.7,
        activity_type="Ride",
    ),
}


class SearchStravaApiCmd:
    def __init__(
        self,
        start_date_after: datetime | str | None = None,
        start_date_before: datetime | str | None = None,
        title_contains: str | None = None,
        # Note: all types described in https://github.com/puntonim/sport-monorepo/blob/main/libs/strava-db-models/strava_db_models/strava_db_models.py#L106.
        activity_type: str | None = None,
        start_latlng: tuple[float, float, int] | tuple[float, float] | None = None,
        end_latlng: tuple[float, float, int] | tuple[float, float] | None = None,
        location_visited_latlng: (
            tuple[float, float, int] | tuple[float, float] | None
        ) = None,
        segment_id: int | None = None,
        distance_range: tuple[int, int] | None = None,
        moving_time_range: tuple[int, int] | None = None,
        elapsed_time_range: tuple[int, int] | None = None,
        elevation_gain_range: tuple[int, int] | None = None,
        elevation_highest_range: tuple[int, int] | None = None,
        elevation_lowest_range: tuple[int, int] | None = None,
        speed_avg_range: tuple[float, float] | None = None,
        speed_max_range: tuple[float, float] | None = None,
        pace_avg_range: tuple[str, str] | None = None,
        pace_max_range: tuple[str, str] | None = None,
        hr_avg_range: tuple[int, int] | None = None,
        hr_max_range: tuple[int, int] | None = None,
        do_select_only_if_with_hr_band: bool = False,
        strava_token_manager: (
            AwsParameterStoreStravaTokenManager
            | FileStravaTokenManager
            | FakeTestStravaTokenManager
            | None
        ) = None,
    ):
        self.start_date_after = start_date_after
        self.start_date_before = start_date_before
        self.title_contains = title_contains
        self.activity_type = activity_type
        self.start_latlng = start_latlng
        self.end_latlng = end_latlng
        self.location_visited_latlng = location_visited_latlng
        self.segment_id = segment_id
        self.distance_range = distance_range
        self.moving_time_range = moving_time_range
        self.elapsed_time_range = elapsed_time_range
        self.elevation_gain_range = elevation_gain_range
        self.elevation_highest_range = elevation_highest_range
        self.elevation_lowest_range = elevation_lowest_range
        self.speed_avg_range = speed_avg_range
        self.speed_max_range = speed_max_range
        self.pace_avg_range = pace_avg_range
        self.pace_max_range = pace_max_range
        self.hr_avg_range = hr_avg_range
        self.hr_max_range = hr_max_range
        self.do_select_only_if_with_hr_band = do_select_only_if_with_hr_band

        if segment_id is not None and location_visited_latlng is not None:
            raise ValueError(
                "segment_id and location_visited_latlng args are mutually exclusive, so"
                " use only one of them"
            )

        strava_token_manager = (
            strava_token_manager
            or AwsParameterStoreStravaTokenManager(
                settings.TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
                settings.CLIENT_ID_PARAMETER_STORE_KEY_PATH,
                settings.CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            )
        )
        self.client = StravaClient(strava_token_manager.get_access_token())

    def search(self) -> None:
        filters_kwargs = dict(
            # start_date_after: done later as it is not a filter but a param to list_activities().
            # start_date_before: done later as it is not a filter but a param to list_activities().
            title_contains=self.title_contains,
            activity_type=self.activity_type,
            start_latlng=self.start_latlng,
            end_latlng=self.end_latlng,
            location_visited_latlng=self.location_visited_latlng,
            distance_range=self.distance_range,
            moving_time_range=self.moving_time_range,
            elapsed_time_range=self.elapsed_time_range,
            elevation_gain_range=self.elevation_gain_range,
            elevation_highest_range=self.elevation_highest_range,
            elevation_lowest_range=self.elevation_lowest_range,
            speed_avg_range=self.speed_avg_range,
            speed_max_range=self.speed_max_range,
            pace_avg_range=self.pace_avg_range,
            pace_max_range=self.pace_max_range,
            hr_avg_range=self.hr_avg_range,
            hr_max_range=self.hr_max_range,
        )

        segment_data = None
        if self.segment_id is not None:
            segment_data = self._get_segment_data(self.segment_id)
            if filters_kwargs["activity_type"] is None:
                filters_kwargs["activity_type"] = segment_data.get("activity_type")
            if filters_kwargs["distance_range"] is None:
                distance = round(segment_data["distance"])
                filters_kwargs["distance_range"] = (distance - 1, distance + 99_000_000)
            if filters_kwargs["elevation_gain_range"] is None:
                elevation = round(segment_data["total_elevation_gain"])
                filters_kwargs["elevation_gain_range"] = (
                    elevation - 1,
                    elevation + 99_000,
                )
            if filters_kwargs["location_visited_latlng"] is None:
                filters_kwargs["location_visited_latlng"] = (
                    *segment_data["start_latlng"],
                    250,
                )

        page_n = 1
        while True:
            summary_resp: ListActivitiesResponse = self.client.list_activities(
                after_ts=self.start_date_after,
                before_ts=self.start_date_before,
                n_results_per_page=100,
                page_n=page_n,
            )
            n = len(summary_resp.data)

            for summary in summary_resp.filter(**filters_kwargs):
                ## Get the segment efforts if segment_id was given.
                segment_efforts: list[dict] = []  # See specs later.
                if self.segment_id is not None:
                    # Get the activity details and the segment efforts.
                    details_resp: ActivityDetailsResponse = (
                        self.client.get_activity_details(summary["id"])
                    )
                    try:
                        segment_efforts: list[dict] = details_resp.get_segment_efforts(
                            [(self.segment_id, segment_data["name"])]
                        )
                    except SegmentEffortNotFound:
                        continue
                    # Each item in the list `segment_efforts` is a dict that contains
                    #  segment efforts data with these interesting attrs (and others):
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
                    #         ...
                    #     }

                ## Check in Garmin API if the heart rate band monitor was used.
                hr_band_msg = "[bold on red]??[/]"
                if self.do_select_only_if_with_hr_band:
                    garmin_activity = None
                    try:
                        garmin_activity = (
                            search_garmin_activity_matching_strava_activity_api(
                                strava_activity_id=summary["id"],
                            )
                        )
                    except ActivityNotFound as exc:
                        hr_band_msg = (
                            "[bold on red]Garmin matching activity not found[/]"
                        )
                    if garmin_activity:
                        garmin = GarminConnectClient()
                        response = garmin.get_activity_summary(
                            garmin_activity["activityId"]
                        )
                        if response.has_heart_rate_monitor():
                            hr_band_msg = "Yes"
                        else:
                            continue

                msg = f"[bold on yellow]{summary['name']}[/]"
                msg += f"\nhttps://www.strava.com/activities/{summary['id']}"
                msg += f"\n{summary['type']} - {summary['sport_type']}"
                msg += f"\n{summary['start_date_local']}"
                if distance := summary.get("distance") / 1000:
                    msg += f"\nDistance: {round(distance)} km"
                if moving_time := summary.get("moving_time"):
                    msg += f"\nDuration: {datetime_utils.seconds_to_hh_mm(moving_time)} (elapsed {datetime_utils.seconds_to_hh_mm(summary['elapsed_time'])})"
                if elevation := summary.get("total_elevation_gain"):
                    msg += f"\nElevation: {round(elevation)} m (max {summary.get('elev_high') or '?'} m, min {summary.get('elev_low') or '?'} m)"
                if hr_avg := summary.get("average_heartrate"):
                    msg += f"\nHR: {hr_avg} (max {round(summary['max_heartrate'])})"
                if self.do_select_only_if_with_hr_band:
                    msg += f"\nHR band: {hr_band_msg}"
                if summary["type"] == "Run":
                    if average_speed := summary.get("average_speed"):
                        msg += f"\nPace: {speed_utils.minpkm_base10_to_base60(speed_utils.mps_to_minpkm_base10(average_speed))} min/km (max {speed_utils.minpkm_base10_to_base60(speed_utils.mps_to_minpkm_base10(summary.get('max_speed')))} min/km)"
                else:
                    if average_speed := summary.get("average_speed"):
                        msg += f"\nSpeed: {round(speed_utils.mps_to_kmph(average_speed), 2)} km/h (max {round(speed_utils.mps_to_kmph(summary.get('max_speed')), 2)} km/h)"
                if start_latlng := summary.get("start_latlng"):
                    msg += f"\nStart loc: {start_latlng}"
                if end_latlng := summary.get("end_latlng"):
                    msg += f"\nEnd loc: {end_latlng}"
                for segment_effort in segment_efforts:
                    msg += f"\n[underline]Segment {segment_effort['name']}[/]"
                    msg += f"\n   Duration: {datetime_utils.seconds_to_hh_mm(segment_effort['elapsed_time'])} (moving: {datetime_utils.seconds_to_hh_mm(segment_effort['moving_time'])})"
                    msg += f"\n   Distance: {round(segment_effort['distance'] / 1000, 2)} km"
                    msg += f"\n   HR: avg {round(segment_effort['average_heartrate'])} (max {round(segment_effort['max_heartrate'])})"
                console.print(msg + "\n")

            # If we got 100 results, then there must be another page, otherwise this was
            #  the last page.
            if n < 100:
                break
            page_n += 1

    def _get_segment_data(self, segment_id: int) -> dict:
        """
        Get the coords as list[lat-float, lon-float] of the Strava segment starting
         location.

        Args:
            segment_id: Strava segment id.

        Returns: coords as tuple[float, float], eg. [45.745995, 9.762249].

        """
        if segment_id in KNOWN_STRAVA_SEGMENTS_DATA:
            # Selvino Fontanella and Passo Stelvio (via Bormio).
            return KNOWN_STRAVA_SEGMENTS_DATA[segment_id]
        else:
            response: SegmentResponse = self.client.get_segment(segment_id)
            # Example:
            # {
            #     "id": 14418673,
            #     "name": "Selvino Fontanella",
            #     "activity_type": "Ride",
            #     "distance": 10160.9,
            #     "average_grade": 5.9,
            #     "maximum_grade": 26.2,
            #     "elevation_high": 911.7,
            #     "elevation_low": 325.8,
            #     "start_latlng": [45.745995, 9.762249],
            #     "end_latlng": [45.778911, 9.743986],
            #     "total_elevation_gain": 587.9,
            #     "map": {
            #         "id": "s14418673",
            #         "polyline": "kwevGwtq...",
            #         "resource_state": 3,
            #     },
            #     ...
            # }
            return response.data
