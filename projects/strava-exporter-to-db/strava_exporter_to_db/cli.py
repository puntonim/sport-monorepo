"""
See ../../README.md to know how to use this CLI.
"""

import argparse
import sys
from datetime import datetime

import log_utils as logger

from .console import console
from .exporter import ExporterToDb, StrategyEnum

rich_log = logger.RichAdapter()
logger.set_adapter(rich_log)

# Argparse docs: https://docs.python.org/3/library/argparse.html
# Argparse tutorial: https://docs.python.org/3/howto/argparse.html#argparse-tutorial
parser = argparse.ArgumentParser(
    prog="export-to-db",
    description="Export activities from Strava API to a SQLite DB."
    " By default it only exports activity *summaries*."
    " To export also activities *details* use the flags --with-details or"
    " --only-details."
    " Mind that exporting details might hit Strava API rate limits:"
    " if so, then a message will tell you how to run it again after max 15 mins.",
)

# Add the main command: summaries or details.
parser.add_argument(
    "command",
    help="Main command: summaries or details.",
    choices=["summaries", "details"],
    type=str,
)

# Add the optional: --strategy OVERWRITE_IF_CHANGED or ONLY_MISSING.
parser.add_argument(
    "--strategy",
    dest="strategy",
    help="OVERWRITE_IF_CHANGED overwrites the existing DB data if the data found in"
    " Strava API has changed. ONLY_MISSING fetches only missing data (so it does not"
    " overwrite data in the DB).",
    choices=[x for x in StrategyEnum],
    type=str,
    required=True,
)


def _to_datetime(x):
    try:
        return datetime.fromisoformat(x)
    except Exception:
        raise argparse.ArgumentTypeError("Supported format: 2025-01-18T14:30:00+01:00")


# Add the optional: --before-ts 2025-01-18T14:30:00+01:00.
parser.add_argument(
    "--before-ts",
    dest="before_ts",
    help="Before timestamp, format like: 2025-01-18T14:30:00+01:00.",
    # type=datetime.fromisoformat,
    type=_to_datetime,
    required=False,
    default=False,
)

# Add the optional: --after-ts 2025-01-18T14:30:00+01:00.
parser.add_argument(
    "--after-ts",
    dest="after_ts",
    help="After timestamp, format like: 2025-01-18T14:30:00+01:00.",
    # type=datetime.fromisoformat,
    type=_to_datetime,
    required=False,
    default=False,
)


def main(test_cmd_line_args: list[str] | None = None):
    """
    The entrypoint of the CLI.
    See ../../README.md to know how to use this CLI.

    Args:
        test_cmd_line_args: used in unit tests.
    """

    if test_cmd_line_args:
        parser.exit_on_error = False
        args = parser.parse_args(test_cmd_line_args)
    else:
        args = parser.parse_args()

    if not test_cmd_line_args:
        a = console.input(
            f"[green]So you want to export: [b]{args.command}[/b]\n"
            f" with strategy: [b]{args.strategy}[/b]\n"
            f" and before_ts: [b]{args.before_ts or '-'}[/b]\n"
            f" and after_ts: [b]{args.after_ts or '-'}[/b]\n"
            " Continue? \\[y/n] "
        )
        if a.lower() not in ("yes", "y", "true", "t"):
            sys.exit(1)

    if not test_cmd_line_args:
        if args.command == "details":
            console.input(
                "[yellow][i]Mind that this command might hit Strava API rate limits,"
                " if so, then a message will tell you how to run it again after max 15 mins. "
            )

    exporter = ExporterToDb(args.strategy, args.before_ts, args.after_ts)
    if args.command == "summaries":
        try:
            exporter.export_summaries()
        except NotImplementedError as exc:
            console.print(f"[red]{exc.args[0]}")
            sys.exit(1)
    elif args.command == "details":
        exporter.export_details()
