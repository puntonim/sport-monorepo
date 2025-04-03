import functools
import sys
from collections.abc import Generator
from datetime import datetime, time
from enum import StrEnum
from time import sleep

import checksum_utils
import datetime_utils
import log_utils as logger
import peewee_utils
from strava_client import (
    RequestedResultsPageDoesNotExist,
    StravaApiRateLimitExceeded,
    StravaClient,
)
from strava_client.token_managers import AwsParameterStoreTokenManager

from .console import console
from .data_models import Activity, RawActivityDetails, RawActivitySummary

TOKEN_JSON_PARAMETER_STORE_KEY_PATH = (
    "/strava-facade-api/production/strava-api-token-json"
)
CLIENT_ID_PARAMETER_STORE_KEY_PATH = (
    "/strava-facade-api/production/strava-api-client-id"
)
CLIENT_SECRET_PARAMETER_STORE_KEY_PATH = (
    "/strava-facade-api/production/strava-api-client-secret"
)


class StrategyEnum(StrEnum):
    OVERWRITE_IF_CHANGED = "OVERWRITE_IF_CHANGED"
    ONLY_MISSING = "ONLY_MISSING"


def handle_strava_api_rate_limit_error(fn):
    @functools.wraps(fn)
    def closure(*args, **kwargs):
        # `self` in the original method.
        # zelf = args[0]  # noqa

        while True:
            try:
                return fn(*args, **kwargs)
            except StravaApiRateLimitExceeded as exc:
                # Handle the Strava API rate limits:
                #  100 requests every 15 minutes: reset at natural 15-minute intervals
                #   corresponding to 0, 15, 30 and 45 minutes after the hour.
                #  1000 per day: resets at midnight UTC.
                #  https://developers.strava.com/docs/rate-limits/
                a = console.input(
                    f"[i][yellow]{exc.msg}\n[/i]"
                    f"[b]Do you want me to wait until {exc.reset_ts}? \\[y/n] "
                )
                if a.lower() not in ("yes", "y", "true", "t"):
                    console.print(f"[yellow]Ok, then you can retry at {exc.reset_ts}")
                    sys.exit(1)
                else:
                    # The user asked the software to wait until the rate limit rests.
                    while datetime.now().astimezone() < exc.reset_ts:
                        # Compute the # mins until the reset.
                        delta = exc.reset_ts - datetime.now().astimezone()
                        delta = int(delta.total_seconds() / 60) + 1
                        console.print(
                            f"[yellow]Sleeping util {exc.reset_ts}, {delta} mins to go..."
                        )
                        sleep(30)  # 30 secs.
                    continue

    return closure


class ExporterToDb:
    def __init__(
        self,
        strategy: str,
        before_ts: datetime | None = None,
        after_ts: datetime | None = None,
    ):
        if strategy not in StrategyEnum:
            raise InvalidStrategy
        self.strategy = strategy
        self.before_ts = before_ts
        self.after_ts = after_ts
        for d in (before_ts, after_ts):
            if d and _is_naive(d):
                raise NaiveDatetime(d)

        self._token_mgr = AwsParameterStoreTokenManager(
            TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
            CLIENT_ID_PARAMETER_STORE_KEY_PATH,
            CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
        )

    @property
    def client(self):
        return StravaClient(self._token_mgr.get_access_token())

    @peewee_utils.use_db
    def export_summaries(self):
        # Only strategy OVERWRITE_IF_CHANGED supported for summaries.
        if self.strategy == StrategyEnum.ONLY_MISSING:
            raise NotImplementedError("ONLY_MISSING for summaries not implemented yet")

        #
        # Logic:
        #  - API get all activity summaries with before_ts and after_ts
        #  - DB check if a RawActivitySummary exists for that strava_id:
        #     - if not found:
        #       - DB create (or update, not the case) RawActivitySummary
        #       - DB create (or update, not the case) Activity
        #     - if found, compare the md5_checksum:
        #        - if different:
        #           - DB update (or create, not the case) the RawActivitySummary with the data from API
        #           - DB update (or create, not the case) Activity
        #

        # Get all activity summaries from Strava API:
        for batch_summary_data in self._api_yield_all_activity_summaries():
            batch_summary_data: list[dict]
            for summary_data in batch_summary_data:
                summary_data: dict
                strava_id = summary_data["id"]

                # If this RawActivitySummary does not exist in the db:
                #  create the RawActivitySummary and Activity.
                found = RawActivitySummary.get_or_none(strava_id=strava_id)
                if not found:
                    self._db_create_or_update_raw_activity_summary(summary_data)
                    logger.info(f"Created RawActivitySummary strava_id={strava_id}")
                    self._db_create_or_update_activity(summary_data)
                    logger.info(
                        f"Created Activity strava_id={strava_id} start_date={summary_data['start_date']}"
                    )

                # If this RawActivitySummary already exists in the db:
                #  compute the checksum and if changed, update RawActivitySummary
                #  and update the matching Activity.
                else:
                    md5_checksum = checksum_utils.md5_checksum_for_data(summary_data)
                    if found.md5_checksum != md5_checksum:
                        self._db_create_or_update_raw_activity_summary(summary_data)
                        logger.info(f"Updated RawActivitySummary strava_id={strava_id}")
                        self._db_create_or_update_activity(summary_data)
                        logger.info(
                            f"Updated Activity strava_id={strava_id} start_date={summary_data['start_date']}"
                        )

    @peewee_utils.use_db
    def export_details(self):
        #
        # Logic:
        #  - DB select all Activities
        #     [if ONLY_MISSING strategy] that have no matching RawActivityDetails
        #     and with the given before_ts and after_ts
        #     and for each:
        #    - API get details by strava_id
        #    - DB get matching RawActivityDetails
        #       - if it doesn't exist: DB create RawActivityDetails and update matching Activity details attrs
        #       - if it exists, check if checksums for details from API and RawActivityDetails match
        #           - if no match: DB update RawActivityDetails and update Activity details attrs
        #

        # Select Activity with the given before_ts and after_ts.
        query = Activity.select()
        if self.before_ts:
            query = query.where(Activity.start_date <= self.before_ts)
        if self.after_ts:
            query = query.where(Activity.start_date >= self.after_ts)
        # If strategy=ONLY_MISSING, sub-select Activities that have NO matching RawActivityDetails.
        if self.strategy == StrategyEnum.ONLY_MISSING:
            query = query.where(
                Activity.strava_id.not_in(
                    RawActivityDetails.select(RawActivityDetails.strava_id)
                )
            )

        # The `iterator()` method behaves like a generator, so perfect for big queries.
        for activity in query.iterator():
            strava_id = activity.strava_id
            details_data: dict = self._api_get_activity_details(strava_id)

            # If this RawActivityDetails does not exist in the db:
            #  create the RawActivityDetails and Activity.
            found = RawActivityDetails.get_or_none(strava_id=strava_id)
            if not found:
                self._db_create_or_update_raw_activity_details(details_data)
                logger.info(f"Created RawActivityDetails strava_id={strava_id}")
                self._db_create_or_update_activity(details_data)
                logger.info(
                    f"Updated Activity strava_id={strava_id} start_date={activity.start_date}"
                )

            # If this RawActivityDetails already exists in the db:
            #  compute the checksum and if changed, update RawActivityDetails
            #  and update the matching Activity.
            else:
                md5_checksum = checksum_utils.md5_checksum_for_data(details_data)
                if found.md5_checksum != md5_checksum:
                    self._db_create_or_update_raw_activity_details(details_data)
                    logger.info(f"Updated RawActivityDetails strava_id={strava_id}")
                    self._db_create_or_update_activity(details_data)
                    logger.info(
                        f"Updated Activity strava_id={strava_id} start_date={activity.start_date}"
                    )

    def _api_yield_all_activity_summaries(self) -> Generator[list[dict]]:
        # Trick: using a closure here only because the decorator does not work
        #  on the method, maybe because it is a generator. It does work on this
        #  closure instead.
        @handle_strava_api_rate_limit_error
        def _closure():
            return self.client.list_activities(
                # Don't use `after_ts` and `before_ts` to get all activities since
                #  the oldest.
                after_ts=self.after_ts,
                before_ts=self.before_ts,
                n_results_per_page=100,
                page_n=i,
            )

        i = 1
        while True:
            try:
                response = _closure()
                yield response
            except RequestedResultsPageDoesNotExist:
                break
            i += 1

    def _db_create_or_update_raw_activity_summary(self, data: dict):
        create_data = dict(
            raw_summary=data,
            strava_id=data["id"],
            md5_checksum=checksum_utils.md5_checksum_for_data(data),
        )
        update_data = {k: v for k, v in create_data.items() if k != "strava_id"}
        RawActivitySummary.insert(**create_data).on_conflict(
            conflict_target=[RawActivitySummary.strava_id],
            update=update_data,
        ).execute()

    @handle_strava_api_rate_limit_error
    def _api_get_activity_details(self, strava_id: int) -> dict:
        response = self.client.get_activity_details(strava_id)
        return response

    def _db_create_or_update_raw_activity_details(self, data: dict):
        create_data = dict(
            raw_details=data,
            strava_id=data["id"],
            md5_checksum=checksum_utils.md5_checksum_for_data(data),
        )
        update_data = {k: v for k, v in create_data.items() if k != "strava_id"}
        RawActivityDetails.insert(**create_data).on_conflict(
            conflict_target=[RawActivityDetails.strava_id],
            update=update_data,
        ).execute()

    def _db_create_or_update_activity(self, data: dict):
        # Activity summary attrs.
        create_data = dict(
            strava_id=data["id"],
            name=data["name"],
            distance=data["distance"],
            moving_time=data["moving_time"],
            elapsed_time=data["elapsed_time"],
            total_elevation_gain=data["total_elevation_gain"],
            type=data["type"],
            sport_type=data["sport_type"],
            start_date=datetime_utils.iso_string_to_date(data["start_date"]),
            start_date_local_str=data["start_date_local"],
            timezone=data["timezone"],
            utc_offset=data["utc_offset"],
            gear_id=data["gear_id"],
        )
        # Heart rate data in the summary.
        _all_hr_values = [
            data.get("has_heartrate"),
            data.get("average_heartrate"),
            data.get("max_heartrate"),
        ]
        # If they are not all True and not all False, then there is an error.
        if (not all(_all_hr_values)) and (not all([not x for x in _all_hr_values])):
            raise HeartRateError(
                data["id"],
                data.get("has_heartrate"),
                data.get("average_heartrate"),
                data.get("max_heartrate"),
            )
        if data.get("average_heartrate"):
            create_data["heartrate_avg"] = data["average_heartrate"]
            create_data["heartrate_max"] = data["max_heartrate"]

        # Activity details attrs are optional (nullable).
        if "description" in data:
            create_data["description"] = data["description"]
        if "gear" in data:
            # Gear details are optional in the original data, for example for
            #  a WeightTraining there is no gear data.
            create_data["gear_name"] = data.get("gear", {}).get("name")
            create_data["gear_distance"] = data.get("gear", {}).get("distance")

            # Also, make sure that the gear id is consistent in the 2 attributes
            #  returned by Strava API.
            if data.get("gear") and data["gear_id"] != data["gear"]["id"]:
                raise GearIdMismatch(
                    data["id"],
                    data["gear_id"],
                    data["gear"]["id"],
                )

        update_data = {k: v for k, v in create_data.items() if k != "strava_id"}
        Activity.insert(**create_data).on_conflict(
            conflict_target=[Activity.strava_id],
            update=update_data,
        ).execute()


class BaseExporterToDbExceptions(Exception):
    pass


class InvalidStrategy(BaseExporterToDbExceptions):
    pass


class NaiveDatetime(BaseExporterToDbExceptions):
    def __init__(self, d: datetime):
        self.d = d


class GearIdMismatch(BaseExporterToDbExceptions):
    def __init__(self, strava_id: int, gear_id_attr: str, gear_id_obj: str):
        self.strava_id = strava_id
        self.gear_id_attr = gear_id_attr
        self.gear_id_obj = gear_id_obj
        super().__init__(
            f"Gear id mismatch in details for strava_id={strava_id}:"
            f" gear_id={gear_id_attr} but gear.id={gear_id_obj}"
        )


class HeartRateError(BaseExporterToDbExceptions):
    def __init__(
        self,
        strava_id: int,
        has_heartrate: bool,
        average_heartrate: float,
        max_heartrate: float,
    ):
        self.strava_id = strava_id
        self.has_heartrate = has_heartrate
        self.average_heartrate = average_heartrate
        self.max_heartrate = max_heartrate
        super().__init__(
            f"Heart rate attrs inconsistent for strava_id={strava_id}:"
            f" has_heartrate={has_heartrate}, "
            f" average_heartrate={average_heartrate}, "
            f" max_heartrate={max_heartrate}"
        )


# Src: https://github.com/puntonim/utils-monorepo/blob/main/datetime-utils/datetime_utils/datetime_utils.py#L69C1-L73C17
def _is_naive(d: datetime | time):
    # Docs: https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive
    if d.tzinfo is None or d.tzinfo.utcoffset(d) is None:
        return True
    return False
