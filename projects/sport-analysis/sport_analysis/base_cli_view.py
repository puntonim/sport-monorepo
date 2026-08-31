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


class ActivityIdType(click.ParamType):
    """
    Parameter type that can be an int or the string "LATEST" or "LATEST-3".
    """

    name = "activity_id"

    def convert(self, value, param=None, ctx=None) -> int | tuple[str, int]:
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
