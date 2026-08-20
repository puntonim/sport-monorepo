"""
Create an HTML page with a calendar of all activities in the given range.
This script actually collects the activities from Strava API and writes them to
 the file DATA.js. Then just open calendar.html to trigger the Javascript code that
 loads the activities into the HTML calendar.

Note: this script uses VCR.py to record HTTP interactions, so it avoids hammering
 Strava APIs and hitting rate limits.

Usage:
    $ poetry run python -m sport_analysis.sketches.calendar.main --start-date-after 2025-12-29T00:00:00+01:00 --start-date-before 2026-08-20T23:59:59+02:00
    To record new VCR.py episodes:
    $ IS_VCR_EPISODE_OR_ERROR=n poetry run python -m sport_analysis.sketches.calendar.main --start-date-after 2025-12-29T00:00:00+01:00 --start-date-before 2026-08-20T23:59:59+02:00
"""

import json
from contextlib import suppress
from datetime import datetime, timedelta
from enum import StrEnum
from pathlib import Path

import click
import datetime_utils
import log_utils as logger
import questionary
import speed_utils
import vcr as vcr_module
import yaml
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
)
from strava_client import StravaClient
from strava_client.strava_token_managers import (
    AwsParameterStoreStravaTokenManager,
    FakeTestStravaTokenManager,
    FileStravaTokenManager,
)
from vcr.errors import CannotOverwriteExistingCassetteException

from tests import conftest

from ...base_cli_view import BaseClickCommand, ConsoleAdapter
from ...conf import settings

CURR_DIR = Path(__file__).parent
DAYS_OF_WEEK = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)
# ACTIVITY_TYPES_TRANSLATION = {
#     "BackcountrySki": "bski",
#     "Hike": "hike",
#     "Kayaking": "kayak",
#     "NordicSki": "nski",
#     "Ride": "ride",
#     "RockClimbing": "rock",
#     "Run": "run",
#     "Snowboard": "snowboard",
#     "Snowshoe": "snowshoe",
#     "Walk": "walk",
#     "WeightTraining": "weight",
#     "Workout": "workout",
# }
# NAMES_TRANSLATION = {
#     "BackcountrySki": "Backcountry Ski",
#     "Hike": "Hike",
#     "Kayaking": "Kayak",
#     "NordicSki": "Nordic Ski",
#     "Ride": "Ride",
#     "RockClimbing": "Rock Climb",
#     "Run": "Run",
#     "Snowboard": "Snowboard",
#     "Snowshoe": "Snowshoe",
#     "Walk": "Walk",
#     "WeightTraining": "Weight",
#     "Workout": "Workout",
# }

# Use VCR.py with the cassette named after this file and in this same dir.
VCR_CASSETTE_PATH = (
    Path(__file__).parent / "cassettes" / (Path(__file__).stem + ".yaml")
)


class ItemEnum(StrEnum):
    DAY = "DAY"
    WEEKLY_RECAP = "WEEKLY_RECAP"
    MONTHLY_RECAP = "MONTHLY_RECAP"


console = ConsoleAdapter()


def configure_vcr():
    return vcr_module.VCR(**conftest.vcr_config_dict())


def configure_garmin_token_manager():
    return (
        None
        if conftest.is_vcr_record_mode() or not conftest.is_vcr_enabled()
        # Use a fake test token (expiration in 3999) when replaying episodes.
        else FakeTestGarminConnectTokenManager()
    )


@click.command(
    cls=BaseClickCommand,
    name="calendar",
    help="""Create a monthly calendar.""",
)
@click.option(
    "--start-date-after",
    type=click.DateTime(formats=["%Y-%m-%dT%H:%M:%S%z"]),
    help="Activity start date after; eg. 2024-01-01T00:00:00+01:00",
)
@click.option(
    "--start-date-before",
    type=click.DateTime(formats=["%Y-%m-%dT%H:%M:%S%z"]),
    help="Activity start date before; eg. 2024-12-31T23:59:59+01:00",
)
def cli(
    start_date_after: datetime | str | None = None,
    start_date_before: datetime | str | None = None,
) -> None:
    cli_cmd(
        start_date_after=start_date_after,
        start_date_before=start_date_before,
    )


def cli_cmd(
    start_date_after: datetime | str | None = None,
    start_date_before: datetime | str | None = None,
):
    # Prompt for the date args that were not provided in the CLI.
    # start_date_after.
    is_input_valid = True if start_date_after is not None else False
    while not is_input_valid:
        text = "Activity START DATE AFTER (eg. 2024-01-01T00:00:00+01:00)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            start_date_after = _parse_datetime_input(x)
            is_input_valid = True

    # start_date_before.
    is_input_valid = True if start_date_before is not None else False
    while not is_input_valid:
        text = "Activity START DATE BEFORE (eg. 2024-12-31T23:59:59+01:00)"
        # unsafe_ask() so it can be stopped with ctrl-c.
        x = questionary.text(text).unsafe_ask() or None
        with suppress(ValidationError):
            start_date_before = _parse_datetime_input(x)
            is_input_valid = True

    c = CalendarCmd(
        start_date_after=start_date_after, start_date_before=start_date_before
    )
    # Configure VCR.py.
    vcr = configure_vcr()
    console.print(f"[italic dim]Using VCR.py cassette: {VCR_CASSETTE_PATH}[/]")
    with vcr.use_cassette(VCR_CASSETTE_PATH):
        try:
            c.create()
        # Enrich VCR.py's `CannotOverwriteExistingCassetteException` original exception
        #  with some useful info.
        except Exception as exc:
            if isinstance(exc, CannotOverwriteExistingCassetteException) or isinstance(
                getattr(exc, "kwargs", dict()).get("error"),
                CannotOverwriteExistingCassetteException,
            ):
                args = list(exc.args)
                args[0] += "\nUse IS_VCR_EPISODE_OR_ERROR=no to record a new episode."
                exc.args = tuple(args)
            raise


class CalendarCmd:
    def __init__(
        self,
        start_date_after: datetime,
        start_date_before: datetime,
        strava_token_manager: (
            AwsParameterStoreStravaTokenManager
            | FileStravaTokenManager
            | FakeTestStravaTokenManager
            | None
        ) = None,
    ):
        """
        Args:
            start_date_after: eg. "2024-01-01T00:00:01+01:00" or datetime(2024, 1, 6, 17, 20, tzinfo=ZoneInfo("Europe/Rome")).
            start_date_before: eg. "2024-01-01T00:00:01+01:00" or datetime(2024, 1, 6, 17, 20, tzinfo=ZoneInfo("Europe/Rome")).
            strava_token_manager: use FakeTestStravaTokenManager when
             replaying VCR episodes.
        """
        self.start_date_after = start_date_after
        self.start_date_before = start_date_before

        # Eg. 365 or 181 for the 1st semester.
        self.n_days_in_period = (
            self.start_date_before - self.start_date_after
        ).days + 1

        strava_token_manager = (
            strava_token_manager
            or AwsParameterStoreStravaTokenManager(
                settings.TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
                settings.CLIENT_ID_PARAMETER_STORE_KEY_PATH,
                settings.CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            )
        )
        self.strava = StravaClient(strava_token_manager.get_access_token())
        self.summaries: list[dict] = list()
        self.return_data: list[dict] = list()
        self._vcr_cassette_content = None

    def _collect_strava_activities_summaries(self):
        # Collect all Strava activity summaries in the period.
        page_n = 1
        while True:
            response = self.strava.list_activities(
                after_ts=self.start_date_after,
                before_ts=self.start_date_before,
                n_results_per_page=100,
                page_n=page_n,
            )
            self.summaries.extend(response.data)

            n = len(response.data)
            # If we got 100 results, then there must be another page, otherwise this was
            #  the last p page.
            if n < 100:
                break
            page_n += 1

    def _get_vcr_cassette_content(self):
        """
        Load and cache the YAML content of the VCR cassette.
        """
        if not self._vcr_cassette_content:
            with open(VCR_CASSETTE_PATH, "r") as stream:
                self._vcr_cassette_content = yaml.safe_load(stream)
        return self._vcr_cassette_content

    def _get_strava_activity_details(self, activity_id: int):
        """
        Before performing the actual HTTP request (intercepted by VCR.py), manually
         check in the cassette if there is a request with the same URL and, if found,
         return the response.

        Why am I doing this since it is exactly what VCR.py does??
        Keep reading for an interesting answer!

        If the VCR cassette contains many requests, then something breaks in the
         `requests` lib that leads to an error like:

         requests.exceptions.ConnectionError:
          HTTPSConnectionPool(host='www.strava.com', port=443): Max retries exceeded
          with url: /api/v3/activities/19680693097 (Caused by
          NameResolutionError("HTTPSConnection(host='www.strava.com', port=443):
          Failed to resolve 'www.strava.com' ([Errno 8] nodename nor servname provided,
          or not known)"))

        Note that if I empty the cassette then it works. My guess is that it has to do
         with the fact that every episode match is actually, under the hood, a failed
         `requests`'request that eventually leads to `Max retries exceeded`.
        """
        vcr_cassette_content = self._get_vcr_cassette_content()

        for interaction in vcr_cassette_content["interactions"]:
            if (
                interaction["request"]["uri"]
                == f"https://www.strava.com/api/v3/activities/{activity_id}"
                and interaction["request"]["method"].upper() == "GET"
            ):
                logger.info(
                    f"Strava activity details found in cached VCR cassette: {activity_id}"
                )
                return json.loads(interaction["response"]["body"]["string"])

        return self.strava.get_activity_details(activity_id=activity_id).data

    def create(self):
        # Collect all activity summaries from Strava (only for activities in the given
        #  dates range) into `self.summaries`.
        self._collect_strava_activities_summaries()

        weekly_run_tot_km = 0
        weekly_run_times = 0
        weekly_run_duration = 0
        weekly_legs_times = 0
        cur_date = self.start_date_after.date()
        # Iterate through all days in the given interval.
        while cur_date <= self.start_date_before.date():
            day_of_week = DAYS_OF_WEEK[cur_date.weekday()]

            # Keep track of weekly recaps.
            if day_of_week == "monday":
                weekly_run_tot_km = 0
                weekly_run_times = 0
                weekly_run_duration = 0
                weekly_legs_times = 0

            return_data__day = dict(
                index=len(self.return_data),
                itemType=ItemEnum.DAY,
                date=cur_date.isoformat(),
                dayOfWeek=day_of_week,
                activities=[],
            )
            for summary in self.summaries[::-1]:
                start_date_local = datetime_utils.parse_datetime_arg(
                    summary["start_date_local"]
                ).date()
                # If the date of this activity is not the current date: skip.
                if start_date_local < cur_date:
                    continue
                if start_date_local > cur_date:
                    break

                # Get activity details from Strava.
                details_dict = self._get_strava_activity_details(
                    activity_id=summary["id"]
                )

                sport = _get_sport(details_dict)
                distance = summary["distance"]
                moving_time = summary["moving_time"]
                name = summary["name"]
                return_data__activity = dict(
                    sport=sport,
                    shortDescription=_get_short_description(details_dict),
                    url=f"https://www.strava.com/activities/{summary['id']}",
                    # hasHeartRateMonitor= to know this I should use the Garmin client
                    #  to `get_activity_summary(id)` and then `ActivitySummaryResponse.has_heart_rate_monitor()`.
                    originalData=dict(
                        id=summary["id"],
                        startDateLocal=summary["start_date_local"],
                        name=name,
                        type=summary["type"],
                        description=details_dict["description"],
                        distance=distance,
                        totalElevationGain=summary["total_elevation_gain"],
                        movingTime=moving_time,
                        elapsedTime=summary["elapsed_time"],
                        averageSpeed=summary["average_speed"],
                        maxSpeed=summary["max_speed"],
                        # Can be None.
                        averageHeartrate=summary.get("average_heartrate"),
                        maxHeartrate=summary.get("max_heartrate"),  # Can be None.
                        elevHigh=summary.get("elev_high"),  # Can be None.
                        elevLow=summary.get("elev_low"),  # Can be None.
                    ),
                )
                return_data__day["activities"].append(return_data__activity)

                if sport == "run":
                    weekly_run_times += 1
                    weekly_run_tot_km += distance
                    weekly_run_duration += moving_time
                if "powerlifting" in name.lower() or "legs" in name.lower():
                    weekly_legs_times += 1

            self.return_data.append(return_data__day)

            if day_of_week == "sunday":
                return_data__weekly_recap = dict(
                    index=len(self.return_data),
                    itemType=ItemEnum.WEEKLY_RECAP,
                    activities=[
                        dict(
                            sport="run",
                            shortDescription=f"#{weekly_run_times} {round(weekly_run_tot_km/1000)}km {_shortest_time_format(weekly_run_duration)}",
                        ),
                        dict(
                            sport="weight",
                            shortDescription=f"Legs #{weekly_legs_times}",
                        ),
                    ],
                )
                self.return_data.append(return_data__weekly_recap)

            cur_date += timedelta(days=1)

        # console.log(json.dumps(self.return_data, indent=4))

        with open(CURR_DIR / "DATA.js", "w") as fout:
            fout.write(
                "const CALENDAR_DATA = " + json.dumps(self.return_data, indent=4)
            )


def _parse_datetime_input(value: str):
    try:
        return datetime_utils.parse_datetime_arg(
            value, is_type_str_allowed=True, is_type_none_allowed=False
        )
    except datetime_utils.datetime_utils.BaseDatetimeUtilsException as exc:
        msg = "Invalid input, format like 2024-01-01T00:00:00+01:00"
        console.print_error(msg)
        raise ValidationError(msg) from exc


def _get_sport(details_dict):
    ACTIVITY_TYPES_TRANSLATION = {
        "BackcountrySki": "backcountry-ski",
        "Hike": "hike",
        "Kayaking": "kayak",
        "NordicSki": "nordic-ski",
        "Ride": "ride",
        "RockClimbing": "rock-climbing",
        "Run": "run",
        "Snowboard": "snowboard",
        "Snowshoe": "snowshoe",
        "Walk": "walk",
        "WeightTraining": "weight",
        "Workout": "workout",
    }
    sport = ACTIVITY_TYPES_TRANSLATION[details_dict["type"]]

    if sport == "weight":
        if "cali" in details_dict["name"].lower():
            sport = "cali"
        elif "power" in details_dict["name"].lower():
            sport = "power"

    return sport


def _get_short_description(details_dict):
    sport = _get_sport(details_dict)
    descr = details_dict["description"].lower()

    if sport == "run":
        dist = round(details_dict["distance"] / 1000)
        avg_pace = details_dict["average_speed"]
        avg_pace = speed_utils.minpkm_base10_to_base60(
            speed_utils.mps_to_minpkm_base10(avg_pace)
        )
        moving_time_short = _shortest_time_format(details_dict["moving_time"])
        return f"{dist}km {avg_pace}/km {moving_time_short}"

    elif sport == "cali":
        return _shortest_time_format(details_dict["moving_time"])

    elif sport == "power":  # TODO handle powerbuilding
        exercises = []
        if "squat" in descr:
            exercises.append("BS")
        if "bench press" in descr or "larsen press" in descr:
            exercises.append("BP")
        if "deadlift" in descr:
            exercises.append("DL")
        if "rdl" in descr:
            exercises.append("RDL")
        if "shoulder press" in descr:
            exercises.append("SP")
        if "legs" in details_dict["name"].lower():
            exercises.append("legs")
        return ", ".join(exercises)

    return sport.capitalize()


def _shortest_time_format(seconds: int | float):
    hh_mm = datetime_utils.seconds_to_hh_mm(seconds)
    str = hh_mm
    if int(hh_mm.split(":")[0]) < 1:  # Hours is 0.
        str = hh_mm[2:] + "m"
    if int(hh_mm.split(":")[1]) < 1:  # Mins is 0.
        str = hh_mm.split(":")[0] + "h"
    if str.startswith("0"):  # Trim leading 0.
        str = str[1:]
    if ":" in str:
        str = str.replace(":", "h") + "m"
    return str


class BaseCalendarException(Exception): ...


class ValidationError(BaseCalendarException): ...


if __name__ == "__main__":
    print("START")
    cli()
    print("END")
