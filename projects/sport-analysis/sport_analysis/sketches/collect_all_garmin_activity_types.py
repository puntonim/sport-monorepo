"""
Collect all the activity types in Garmin.

The interesting field is "activityType"."typeKey".

The results are stored in garmin-connect-client.

Usage:
    $ poetry run python -m sport_analysis.sketches.collect_all_garmin_activity_types

Results (stored in garmin-connect-client):
    TYPES = [
        "backcountry_snowboarding",
        "cross_country_skiing_ws",
        "cycling",
        "hiking",
        "mountain_biking",
        "multi_sport",
        "resort_snowboarding",
        "road_biking",
        "running",
        "snow_shoe_ws",
        "strength_training",
        "trail_running",
        "walking",
    ]
"""

from datetime import datetime, timedelta

import datetime_utils
import log_utils as logger
from garmin_connect_client import GarminConnectClient, SearchActivitiesResponse
from garmin_connect_client.garmin_connect_token_managers import (
    FileGarminConnectTokenManager,
)

from sport_analysis.conf.settings_module import ROOT_DIR


def main(
    start_date_after: datetime | str,
    start_date_before: datetime | str | None = None,
):
    # Parse start_date_after|before.
    start_date_after: datetime = datetime_utils.parse_datetime_arg(start_date_after)
    logger.info(
        f"[underline]Filter[/]: [bold on yellow]start-date-after[/] = {start_date_after.isoformat()}"
    )
    start_date_before: datetime = datetime_utils.parse_datetime_arg(start_date_before)
    if start_date_before:
        logger.info(
            f"[underline]Filter[/]: [bold on yellow]start-date-before[/] = {start_date_before.isoformat()}"
        )

    garmin_token_manager = FileGarminConnectTokenManager(
        token_file_path=ROOT_DIR / "garmin-connect-token.json"
    )
    garmin = GarminConnectClient(token_manager=garmin_token_manager)
    N_RESULTS = 100
    kwargs = dict(
        day_start=start_date_after,
        n_results=N_RESULTS,
    )
    if start_date_before:
        kwargs["day_end"] = start_date_before + timedelta(seconds=5 * 60)

    GARMIN_TYPES = set()
    count = 0
    while True:
        response: SearchActivitiesResponse = garmin.search_activities(
            **kwargs, start_offset=count
        )
        n = len(response.data)
        count += n
        # print(f"Count: {count}")

        for activity in response.data:
            GARMIN_TYPES.add(activity.get("activityType", {}).get("typeKey"))
            logger.info(
                f"Garmin id: {activity.get('activityId')} - {activity.get('activityName')}"
            )

        if n == 0:
            break

    logger.info(f"Garmin types: {sorted(list(GARMIN_TYPES))}")


if __name__ == "__main__":
    logger.info("START")
    main(
        start_date_after="1990-01-01T00:00:00+01:00",
        # start_date_before="2022-12-31T23:59:59+01:00",
    )
    logger.info("END")
