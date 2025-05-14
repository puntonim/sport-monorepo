"""
Entrypoint for the CLI.
To be run (after a `poetry install`) from the root dir with:
$ analysis --help
"""

import click

from .health_cli_view import health_cli_view
from .plot.plot_interval_run_api.plot_interval_300m_run_api import (
    plot_interval_300m_run_api_cli_view,
)
from .plot.plot_interval_run_api.plot_interval_1000m_run_api import (
    plot_interval_1000m_run_api_cli_view,
)
from .plot.plot_run_api.plot_10km_run_api import plot_10km_run_api_cli_view
from .plot.plot_run_api.plot_21km_run_api import plot_21km_run_api_cli_view
from .search.search_matching_activity_api import (
    search_garmin_activity_matching_strava_activity_api_cli_view,
    search_strava_activity_matching_garmin_activity_api_cli_view,
)
from .search.search_text_db import search_text_db_cli_view


@click.group(help="Sport Analysis CLI.")
def cli() -> None:
    pass


# Register all sub-commands.
cli.add_command(health_cli_view)
cli.add_command(search_garmin_activity_matching_strava_activity_api_cli_view)
cli.add_command(search_strava_activity_matching_garmin_activity_api_cli_view)
cli.add_command(plot_10km_run_api_cli_view)
cli.add_command(plot_21km_run_api_cli_view)
cli.add_command(plot_interval_300m_run_api_cli_view)
cli.add_command(plot_interval_1000m_run_api_cli_view)
cli.add_command(search_text_db_cli_view)
