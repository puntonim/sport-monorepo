from datetime import datetime, timedelta

import click
import datetime_utils
import log_utils as logger
from strava_client import StravaClient
from strava_client.strava_token_managers import (
    AwsParameterStoreStravaTokenManager,
    FakeTestStravaTokenManager,
    FileStravaTokenManager,
)

from ..base_cli_view import BaseClickCommand
from ..conf import settings
from .eoy_stats import EoyStats


@click.command(
    cls=BaseClickCommand,
    name="eoy-recap",
    # The `\b` prevents the word-wrapping.
    help="""
    Create end-of-year recap from activities in Strava.

    \b
    Eg.: san eoy-recap --start-date-after 2024-01-01T00:00:01+01:00 --start-date-before 2024-12-31T23:59:59+01:00
    """,
)
@click.option(
    "--start-date-after",
    type=click.DateTime(formats=["%Y-%m-%dT%H:%M:%S%z"]),
    required=True,
    help="Filter on activity's start date; eg. 2024-01-01T00:00:01+01:00",
)
@click.option(
    "--start-date-before",
    type=click.DateTime(formats=["%Y-%m-%dT%H:%M:%S%z"]),
    help="Filter on activity's start date; eg. 2024-01-01T00:00:01+01:00",
)
def eoy_recap_api_cli_view(
    start_date_after: datetime | str | None = None,
    start_date_before: datetime | str | None = None,
):
    return eoy_recap_api(start_date_after, start_date_before)


def eoy_recap_api(
    start_date_after: datetime | str,
    start_date_before: datetime | str | None = None,
    strava_token_manager: (
        AwsParameterStoreStravaTokenManager
        | FileStravaTokenManager
        | FakeTestStravaTokenManager
        | None
    ) = None,
):
    """
    Create end-of-year recap from activities in Strava API, filtering by activity start date.

    Args:
        start_date_after: eg. "2024-01-01T00:00:01+01:00" or datetime(2024, 1, 6, 17, 20, tzinfo=ZoneInfo("Europe/Rome")).
        start_date_before: eg. "2024-01-01T00:00:01+01:00" or datetime(2024, 1, 6, 17, 20, tzinfo=ZoneInfo("Europe/Rome")).
        strava_token_manager: use FakeTestStravaTokenManager when
         replaying VCR episodes.
    """
    # Parse start_date_after|before.
    start_date_after: datetime = datetime_utils.parse_datetime_arg(start_date_after)
    logger.info(
        f"[underline]Filter[/]: [bold on yellow]start-date-after[/] = {start_date_after.isoformat()}",
        highlight=False,
    )
    start_date_before: datetime = datetime_utils.parse_datetime_arg(start_date_before)
    if start_date_before:
        logger.info(
            f"[underline]Filter[/]: [bold on yellow]start-date-before[/] = {start_date_before.isoformat()}",
            highlight=False,
        )

    strava_token_manager = strava_token_manager or AwsParameterStoreStravaTokenManager(
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

    activities = list()

    while True:
        response = strava.list_activities(**kwargs, page_n=page_n)
        n = len(response.data)

        activities.extend(response.data)

        if n < 100:
            break
        page_n += 1

    stats = EoyStats(activities)
    stats.plot()

    logger.info(
        f"Strava API, [bold on red]TOT[/] filtered activities #: {len(activities)}"
    )


class BaseEoyRecapApiException(Exception):
    pass
