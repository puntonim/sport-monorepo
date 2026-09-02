"""
Collect all the activity types (and sport types) in Strava.

There is one interesting field named "type",
 and a less interesting filed named "sport_type".

The results are stored in strava-client and strava-db-models.

Usage:
    $ poetry run python -m sport_analysis.sketches.collect_all_strava_activity_types
    $ poetry run python sport_analysis/sketches/collect_all_strava_activity_types.py

Results (stored in strava-db-models):
    TYPES = [
        "BackcountrySki",
        "Hike",
        "Kayaking",
        "NordicSki",
        "Ride",
        "RockClimbing",
        "Run",
        "Snowboard",
        "Snowshoe",
        "Walk",
        "WeightTraining",
        "Workout",
    ]

    SPORT_TYPES = [
        "BackcountrySki",
        "Hike",
        "Kayaking",
        "MountainBikeRide",
        "NordicSki",
        "Racquetball",
        "Ride",
        "RockClimbing",
        "Run",
        "Snowboard",
        "Snowshoe",
        "TrailRun",
        "Walk",
        "WeightTraining",
        "Workout",
    ]
"""

from datetime import datetime, timedelta

import datetime_utils
import log_utils as logger
from strava_client import StravaClient
from strava_client.strava_token_managers import AwsParameterStoreStravaTokenManager

from sport_analysis.conf import settings


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

    strava_token_manager = AwsParameterStoreStravaTokenManager(
        settings.TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
        settings.CLIENT_ID_PARAMETER_STORE_KEY_PATH,
        settings.CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
    )
    strava = StravaClient(strava_token_manager.get_access_token())
    page_n = 1
    kwargs = dict(
        after_ts=start_date_after - timedelta(seconds=5 * 60),
        n_results_per_page=100,
    )
    if start_date_before:
        kwargs["before_ts"] = start_date_before + timedelta(seconds=5 * 60)

    STRAVA_TYPES = set()
    STRAVA_SPORT_TYPES = set()

    while True:
        response = strava.list_activities(**kwargs, page_n=page_n)
        n = len(response.data)

        for activity in response.data:
            STRAVA_TYPES.add(activity.get("type"))
            STRAVA_SPORT_TYPES.add(activity.get("sport_type"))

        if n < 100:
            break
        page_n += 1

    logger.info(f"Strava types: {sorted(list(STRAVA_TYPES))}")
    logger.info(f"Strava sport types: {sorted(list(STRAVA_SPORT_TYPES))}")


if __name__ == "__main__":
    logger.info("START")
    main(
        start_date_after="1990-01-01T00:00:00+01:00",
        # start_date_before="2022-12-31T23:59:59+01:00",
    )
    logger.info("END")
