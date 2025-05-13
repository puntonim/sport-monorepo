import json
from datetime import date, datetime

from garmin_connect_client import (
    ActivityDetailsResponse,
    ActivitySplitsResponse,
    ActivitySummaryResponse,
    ActivityTypedSplitsResponse,
    GarminConnectClient,
)
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)

from ..conf.settings_module import ROOT_DIR


class BaseApi:
    pass


class MixinGarminRequestsApi(BaseApi):
    def __init__(
        self,
        garmin_connect_token_manager: (
            FileGarminConnectTokenManager | FakeTestGarminConnectTokenManager | None
        ) = None,
    ):
        # Note: you don't necessary have to invoke super().__init__(), you can just
        #  define `self.garmin` in the sub-class __init__().
        self.garmin = GarminConnectClient(
            token_manager=garmin_connect_token_manager
            or FileGarminConnectTokenManager(
                token_file_path=ROOT_DIR / "garmin-connect-token.json"
            )
        )

    def _api_get_activity_summary(
        self, garmin_activity_id: int
    ) -> ActivitySummaryResponse | None:
        # In brief: use a fixture for a 6x300m activity that was actually split into
        #  2 activities.
        # Details: on 13/03/2025 I was running a 6x300m, but the watch stopped for an
        #  Incident Detection while I've just finished the 5th lap.
        #  It was indeed a false positive, but I had to start a new activity for the
        #   6th lap. So I ended up with 2 activities:
        #  https://connect.garmin.com/modern/activity/18520928352
        #  https://connect.garmin.com/modern/activity/18520928686
        #  Now it gets difficult to analyze the data, and for the sake of this method
        #   which only returns summaries, I filter out the 2nd activity.
        if garmin_activity_id == 18520928686:
            raise InterruptedActivity
        return self.garmin.get_activity_summary(garmin_activity_id)

    def _api_get_activity_details(
        self,
        garmin_activity_id: int,
        max_metrics_data_count: int = 2000,
        do_include_polyline: bool = False,
        max_polyline_count: int = 4000,
        do_keep_raw_data: bool = False,
    ) -> ActivityDetailsResponse | None:
        # In brief: use a fixture for a 6x300m activity that was actually split into
        #  2 activities.
        # Details: on 13/03/2025 I was running a 6x300m, but the watch stopped for an
        #  Incident Detection while I've just finished the 5th lap.
        #  It was indeed a false positive, but I had to start a new activity for the
        #   6th lap. So I ended up with 2 activities:
        #  https://connect.garmin.com/modern/activity/18520928352
        #  https://connect.garmin.com/modern/activity/18520928686
        #  Now it gets difficult to analyze the data, and for the sake of this method
        #   which only returns summaries, I filter out the 2nd activity.
        if garmin_activity_id == 18520928686:
            raise InterruptedActivity
        return self.garmin.get_activity_details(
            garmin_activity_id,
            max_metrics_data_count=max_metrics_data_count,
            do_include_polyline=do_include_polyline,
            max_polyline_count=max_polyline_count,
            do_keep_raw_data=do_keep_raw_data,
        )

    def _api_get_activity_typed_splits(
        self, garmin_activity_id: int
    ) -> ActivityTypedSplitsResponse | None:
        """
        Get the ** TYPED ** splits for the given activity.
        Regular splits are defined automatically with the Auto Lap feature: eg. every
         1km in a run and 3km in a ride.
        TYPED splits are the more detailed version of regular splits.
        They are useful when the activity is a Garmin ** workout ** with:
         - automatic laps defined by time or distance: eg. run for 2 mins at
            a certain pace;
         - or laps started by the athlete the lap button is pressed: eg. during
            a 6x300m run.
        With such a workout activity, there would be ~10 regular splits
         and ~50 typed splits.

        I verified that the splits started with a lap button press have:
         "type": "INTERVAL_ACTIVE".
        And you can get them with: response.get_interval_active_splits()

        However, some activities, when I never pressed the lap button, still have
         1 single INTERVAL_ACTIVE split which is the whole activity.
        """
        # In brief: use a fixture for a 6x300m activity that was actually split into
        #  2 activities.
        # Details: on 13/03/2025 I was running a 6x300m, but the watch stopped for an
        #  Incident Detection while I've just finished the 5th lap.
        #  It was indeed a false positive, but I had to start a new activity for the
        #   6th lap. So I ended up with 2 activities:
        #  https://connect.garmin.com/modern/activity/18520928352
        #  https://connect.garmin.com/modern/activity/18520928686
        #  Now it gets difficult to analyze the data, so I collected all the splits
        #   from the 2 activities and merged them into one JSON fixture.
        if garmin_activity_id == 18520928686:
            raise InterruptedActivity
        elif garmin_activity_id == 18520928352:
            with open(
                ROOT_DIR
                / "fixtures"
                / "garmin-activities-typed-splits-18520928352-and-18520928686-merged.json",
                "r",
            ) as fin:
                data = json.loads(fin.read())
            return ActivityTypedSplitsResponse(data)
        return self.garmin.get_activity_typed_splits(garmin_activity_id)

    def _api_get_activity_splits(
        self, garmin_activity_id: int
    ) -> ActivitySplitsResponse:
        """
        Get the (regular) splits for the given activity.
        Regular splits are defined automatically with the Auto Lap feature: eg. every
         1km in a run and 3km in a ride.
        (TYPED splits are the more detailed version of regular splits, see
          get_activity_splits())
        """
        return self.garmin.get_activity_splits(garmin_activity_id)

    def _api_search_activities(
        self,
        filter_exclude: list[int] | None = None,
        text: str | None = None,
        day_start: date | datetime | str | None = None,
        day_end: date | datetime | str | None = None,
        activity_type: str | None = None,
        distance_min: int | None = None,
        distance_max: int | None = None,
        duration_min: int | None = None,
        duration_max: int | None = None,
        elevation_min: int | None = None,
        elevation_max: int | None = None,
        start_offset: int = 0,
        n_results: int = 20,
    ) -> list[int]:
        """
        Args:
            filter_exclude: list of Garmin activity ids to be excluded from the
             results.
            All other args are the same as in GarminConnectClient.search_activities().
        """
        if filter_exclude is None:
            filter_exclude = []

        response = self.garmin.search_activities(
            text=text,
            day_start=day_start,
            day_end=day_end,
            activity_type=activity_type,
            distance_min=distance_min,
            distance_max=distance_max,
            duration_min=duration_min,
            duration_max=duration_max,
            elevation_min=elevation_min,
            elevation_max=elevation_max,
            start_offset=start_offset,
            n_results=n_results,
        )
        activity_ids = list()
        for activity in response.data:
            activity_id = activity["activityId"]
            # Do ignore the main Garmin activity self.garmin_activity_id.
            if activity_id in filter_exclude:
                continue
            # Handle the case of the activity that was interrupted for a
            #  false Incident Detection and ended up as 2 activities (as better
            #  explained in MixinGarminRequestsApi._api_get_activity_splits()).
            if activity_id == 18520928686:
                if 18520928352 not in activity_ids:
                    activity_ids.append(18520928352)
                else:
                    continue
            elif activity_id == 18520928352:
                if 18520928352 not in activity_ids:
                    activity_ids.append(18520928352)
                else:
                    continue
            else:
                activity_ids.append(activity_id)
        return activity_ids


class BaseApiException(Exception):
    pass


class InterruptedActivity(BaseApiException):
    pass
