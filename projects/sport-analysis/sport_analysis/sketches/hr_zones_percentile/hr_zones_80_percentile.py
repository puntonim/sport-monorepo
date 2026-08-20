"""
Find the 80th percentile (P80) of HR frequencies, so the min freq which is higher
 than 80% of samples.

Note: this script uses VCR.py to record HTTP interactions. Just because I wanted to
 test how to use VCR.py in a live code.

Usage:
    $ poetry run python -m sport_analysis.sketches.hr_zones_percentile.hr_zones_80_percentile 23819721623
    To record new VCR.py episodes:
    $ IS_VCR_EPISODE_OR_ERROR=y poetry run python -m sport_analysis.sketches.hr_zones_percentile.hr_zones_80_percentile 23819721623
"""

from pathlib import Path

import click
import numpy as np
import pandas as pd
import vcr as vcr_module
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)
from vcr.errors import CannotOverwriteExistingCassetteException

from tests import conftest

from ...base_cli_view import BaseClickCommand, ConsoleAdapter
from ...plot.base_api import MixinGarminRequestsApi

console = ConsoleAdapter()


def configure_vcr():
    return vcr_module.VCR(**conftest.vcr_config())


def configure_garmin_token_manager():
    return (
        None
        if conftest.is_vcr_record_mode() or not conftest.is_vcr_enabled()
        # Use a fake test token (expiration in 3999) when replaying episodes.
        else FakeTestGarminConnectTokenManager()
    )


@click.command(
    cls=BaseClickCommand,
    name="hr-p80",
    help="""Compute 80 percentile.""",
)
@click.argument("garmin-activity-id", nargs=1, type=int)
def cli(garmin_activity_id: int) -> None:
    cli_cmd(garmin_activity_id)


def cli_cmd(garmin_activity_id: int):
    m = Main(
        garmin_activity_id,
        garmin_connect_token_manager=configure_garmin_token_manager(),
    )
    # Configure VCR.py.
    vcr = configure_vcr()
    # Use VCR.py with the cassette named after this file and in this same dir.
    cassette_path = (
        Path(__file__).parent / "cassettes" / (Path(__file__).stem + ".yaml")
    )
    console.print(f"[italic dim]Using VCR.py cassette: {cassette_path}[/]")
    with vcr.use_cassette(cassette_path):
        try:
            m.compute_80_percentile()
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


class Main(MixinGarminRequestsApi):
    def __init__(
        self,
        garmin_activity_id: int,
        garmin_connect_token_manager: (
            FileGarminConnectTokenManager | FakeTestGarminConnectTokenManager | None
        ) = None,
    ):
        super().__init__(garmin_connect_token_manager)
        self.garmin_activity_id = garmin_activity_id

    def compute_80_percentile(self):
        details_resp = self._api_get_activity_details(
            self.garmin_activity_id, max_metrics_data_count=100_000
        )
        hr_stream = details_resp.get_heartrate_stream(
            # None values cause exceptions in self._plot_hr_histogram_mixin().
            do_remove_none_values=True
        )
        console.log(f"HR list length: {len(hr_stream)}")

        # With Pandas (lighter than numpy).
        df = pd.DataFrame(hr_stream, columns=["HR"])
        percentile80 = df["HR"].quantile(0.80)

        # With numpy (heavier than Pandas).
        percentile80 = np.percentile(hr_stream, 80)

        console.log(f"80 percentile at: {percentile80}")
        console.log(f"Z1 range run (50-60% of 174): 87-103")
        console.log(f"Z2 range run (60-70% of 174): 104-121")
        console.log(f"Z3 range run (70-80% of 174): 122-138")


if __name__ == "__main__":
    print("START")
    cli()
    print("END")
