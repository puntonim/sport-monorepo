from contextlib import suppress

import click
import questionary

from ...base_cli_view import (
    ActivityId,
    ActivityIdParamType,
    BaseClickCommand,
    ConsoleAdapter,
)
from ...utils import questionary_parsers
from .get_activity_urls_api_cmd import GetActivityUrlsApiCmd

console = ConsoleAdapter()

ACTIVITY_ID_PARAM_TYPE = ActivityIdParamType()


@click.command(
    cls=BaseClickCommand,
    name="get-activity-urls",
    help="""
    Get the Garmin and Strava urls for the given activity.

    \b
    EXAMPLES
    \b
    Required args: activity-id.
    So to suppress any interactive questions:
      $ san get-activity-urls LATEST-RUN-3 --no-questions
    \b
    Most popular, no questions:
      $ san get-activity-urls LATEST
      $ san get-activity-urls g-23309590263
    """,
)
@click.argument(
    # REQUIRED arg (via cli arg or questionary).
    # id (int) of Garmin or Strava activity to analyze or a latest string in the following formats:
    # Eg. garmin-23309590263 | g-23309590263 | strava-18988079605 | s-18988079605 | LATEST | LATEST-3 | LATEST-RUN | LATEST-RIDE | LATEST-RUN-3.
    "activity-id",
    nargs=1,
    type=ACTIVITY_ID_PARAM_TYPE,
    required=False,  # `click.argument` is required by default (unlike `click.option`).
)
def get_activity_urls_api_cli_view(activity_id: ActivityId) -> None:
    """
    Get the Garmin and Strava urls for the given activity.
    """
    ## Prompt for all args that were not provided in the CLI.
    # Required arg: activity_id.
    while not activity_id:
        text = "*Required* ACTIVITY ID\n"
        instruction = "Eg. garmin-23309590263 | g-23309590263 | strava-18988079605 | s-18988079605 | LATEST | LATEST-3 | LATEST-RUN | LATEST-RIDE | LATEST-RUN-3\n"
        x = (
            # unsafe_ask() so it can be stopped with ctrl-c.
            # Cannot use `validate=<questionary.Validator subclass>` because that is for
            #  the live validation, it's run on every keystroke and returns None.
            questionary.text(text, instruction=instruction).unsafe_ask()
            or None
        )
        if x is None:  # Required.
            console.print_error("Required!")
            continue
        with suppress(questionary_parsers.ParserValidationError):
            activity_id = questionary_parsers.parse_activity_id_input(
                x, activity_id_param_type=ACTIVITY_ID_PARAM_TYPE
            )

    g = GetActivityUrlsApiCmd(activity_id)
    return g.get()
