import re
import sys
from typing import Literal

import click
import log_utils as logger
from click import Context
from rich.console import Console

from .conf import settings

rich_log = logger.RichAdapter()
rich_log.configure_default()
logger.set_adapter(rich_log)


class BaseClickCommand(click.Command):
    ## Commented out because now the disconnection from TWS is done in
    ##  tws_api_client module's atexit
    # from click import Context
    # def invoke(self, ctx: Context) -> Any:
    #     try:
    #         result = super().invoke(ctx)
    #     finally:
    #         from ..clients.tws_api_client import disconnect
    #         disconnect()
    #     return result
    pass


# TODO deleteme, use ActivityIdParamType instead.
class ActivityIdType(click.ParamType):
    """
    Parameter type that can be an int or the string "LATEST" or "LATEST-3".
    """

    name = "activity_id"

    def convert(self, value, param=None, ctx=None) -> int | tuple[str, int]:

        # Garmin ride activity 19792668848 is broken as I switched sport half way.
        if value == "19792668848" or value == 19792668848:
            ConsoleAdapter().print(
                "[black italic on yellow]:red_circle: Mind that this ride is broken in"
                " Garmin as I switched sport half way (it's a  PR on Stelvio)!!"
                " However I merged the data in Strava, which might be easier to work"
                " with.[/]"
            )

        if isinstance(value, int):
            return value

        if isinstance(value, str) and (match := re.match(r"^LATEST(-\d+)?$", value)):
            n = match.group(1) or 0
            n = int(n)
            return "LATEST", n  # Eg. ("LATEST", 0) or ("LATEST", -3).

        # Try to convert it to int.
        try:
            return int(value)
        except ValueError:
            self.fail(
                f"{value!r} is not a valid integer nor LATEST nor LATEST-3", param, ctx
            )


# TODO deleteme, use ACTIVITY_ID_PARAM_TYPE instead.
ACTIVITY_ID_TYPE = ActivityIdType()


class ConsoleAdapter:
    def __init__(self):
        self.stdout_console = Console(file=sys.stdout)

    def log(self, message: str, extra: dict | None = None):
        if not settings.ARE_CONSOLE_LOGS_ENABLED:
            return
        logger.get_adapter()._log(message, extra)

    def log_error(self, message: str, extra: dict | None = None):
        if not settings.ARE_CONSOLE_LOGS_ENABLED:
            return
        logger.get_adapter().error(f"[bold white on red]{message}[/]", extra)

    def print(self, *args, **kwargs):
        if not settings.ARE_CONSOLE_PRINTS_ENABLED:
            return
        self.stdout_console.print(*args, **kwargs)

    def print_error(self, *args, **kwargs):
        if not settings.ARE_CONSOLE_PRINTS_ENABLED:
            return
        self.stdout_console.print(*args, **kwargs, style="bold white on red")


class ActivityId:
    """
    This class handles a Garmin or Strava activity identifier given as a string in one
     of these formats:
         ActivityId.make_from_string("garmin-11313479371")
         ActivityId.make_from_string("g-11313479371")
         ActivityId.make_from_string("strava-9240064780")
         ActivityId.make_from_string("s-9240064780")
         ActivityId.make_from_string("LATEST")
         ActivityId.make_from_string("LATEST-3")

    Note: this class is meant to be instantiated via the factory method,
     like: ActivityId.make_from_string("LATEST-3").
    """

    def __init__(
        self,
        strava_id: int | None = None,
        garmin_id: int | None = None,
        latest_id: int | None = None,
    ):
        """
        Note: this class is meant to be instantiated via the factory method,
         like: ActivityId.make_from_string("LATEST-3").
        """
        self.strava_id = strava_id
        self.garmin_id = garmin_id
        self.latest_id = latest_id

        c = (strava_id, garmin_id, latest_id).count(None)
        if c != 2:
            raise ValueError(
                f"Exactly 1 arg between strava_id, garmin_id, latest_id should be given: strava_id={strava_id}, garmin_id={garmin_id}, latest_id={latest_id}"
            )

        if strava_id is not None and (
            not isinstance(strava_id, int) or not strava_id > 99999999
        ):
            raise ValueError(f"strava_id must be an int > 99999999: {strava_id}")

        elif garmin_id is not None and (
            not isinstance(garmin_id, int) or not garmin_id > 99999999
        ):
            raise ValueError(f"garmin_id must be an int > 99999999: {garmin_id}")

        elif latest_id is not None and (
            not isinstance(latest_id, int) or not latest_id <= 0
        ):
            raise ValueError(f"latest_id must be an int <= 0: {latest_id}")

    @staticmethod
    def _parse_string(value: str):
        strava_id = garmin_id = latest_id = None

        if not isinstance(value, str):
            raise ValidationError(f"The given arg must be a string: {value}")

        if match := re.match(r"^LATEST(-\d+)?$", value):
            n = match.group(1) or 0
            try:
                n = int(n)
            except ValueError as exc:
                raise ValidationError(f"Not a valid int: {n}") from exc
            latest_id = n

        elif match := re.match(r"^g(?:armin)?-(\d{9,99})$", value):
            n = match.group(1)
            try:
                n = int(n)
            except ValueError as exc:
                raise ValidationError(f"Not a valid int: {n}") from exc
            garmin_id = n

        elif match := re.match(r"^s(?:trava)?-(\d{9,99})$", value):
            n = match.group(1)
            try:
                n = int(n)
            except ValueError as exc:
                raise ValidationError(f"Not a valid int: {n}") from exc
            strava_id = n

        else:
            raise ValidationError(
                f"The given string is not in the right format: {value}\n"
                f"Valid formats: garmin-23309590263 | g-23309590263 | strava-18988079605 | s-18988079605 | LATEST | LATEST-3"
            )

        return strava_id, garmin_id, latest_id

    @classmethod
    def make_from_string(cls, value: str):
        """
        Factory method to use to instantiate this class,
         like: ActivityId.make_from_string("LATEST-3").
        """
        return cls(*cls._parse_string(value))


class BaseActivityIdException(Exception): ...


class ValidationError(BaseActivityIdException): ...


class ActivityIdParamType(click.ParamType):
    """
    Parameter type that can be a Garmin or Strava activity as string.
    Eg. garmin-23309590263 | g-23309590263 | strava-18988079605 | s-18988079605 | LATEST | LATEST-3.
    """

    name = "activity_id"

    def convert(self, value, param=None, ctx=None) -> ActivityId:

        try:
            a = ActivityId.make_from_string(value)
        except (ValidationError, ValueError) as exc:
            self.fail(str(exc), param, ctx)

        # Garmin ride activity 19792668848 (Strava 15104529341) is broken as I switched sport half way.
        if a.garmin_id == 19792668848 or a.strava_id == 15104529341:
            ConsoleAdapter().print(
                "[black italic on yellow]:red_circle: Mind that this ride is broken in"
                " Garmin as I switched sport half way (it's a PR on Stelvio)!! However"
                " I merged the data in Strava 15104529341, which might be easier to"
                " work with.[/]"
            )

        return a


ACTIVITY_ID_PARAM_TYPE = ActivityIdParamType()
