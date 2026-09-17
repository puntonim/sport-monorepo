"""
In a run class I run 16 intervals: 1 min fast and 1 min slow.
The first  interval (starting at 0 seconds) is a fast one.
The last interval is a slow one.

Note: this script uses VCR.py to record HTTP interactions. Just because I wanted to
 test how to use VCR.py in a live code.

Usage:
    $ poetry run python -m sport_analysis.sketches.time_interval_run.time_interval_run 24387737173
    To record new VCR.py episodes:
    $ IS_VCR_EPISODE_OR_ERROR=n poetry run python -m sport_analysis.sketches.time_interval_run.time_interval_run 24387737173
"""

from pathlib import Path
from statistics import fmean

import click
import speed_utils
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
    name="time-interval-run",
    help="""Plot a time interval run.""",
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
            m.plot_time_interval_run()
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

    def plot_time_interval_run(self):
        details_resp = self._api_get_activity_details(
            self.garmin_activity_id, max_metrics_data_count=100_000
        )

        elapsed_time_stream = details_resp.get_elapsed_time_stream()
        distance_stream = details_resp.get_distance_stream()
        hr_stream = details_resp.get_heartrate_stream(
            # None values cause exceptions in self._plot_hr_histogram_mixin().
            do_remove_none_values=False
        )

        # Make sure all streams have the same size.
        assert len(elapsed_time_stream) == len(distance_stream) == len(hr_stream)

        fast_intervals = dict(
            paces=[],
            hrs_avg=[],
            hrs_max=[],
        )
        slow_intervals = dict(
            paces=[],
            hrs_avg=[],
            hrs_max=[],
        )

        ix_start = ix_end = 0
        interval_count = 1
        for i, elapsed_time in enumerate(elapsed_time_stream):
            if elapsed_time >= (60 * interval_count):
                ix_start = ix_end
                ix_end = i

                interval_time = (
                    elapsed_time_stream[ix_end] - elapsed_time_stream[ix_start]
                )
                interval_distance = distance_stream[ix_end] - distance_stream[ix_start]
                pace_mps = interval_distance / interval_time
                pace_minpkm = speed_utils.minpkm_base10_to_base60(
                    speed_utils.mps_to_minpkm_base10(pace_mps)
                )
                hr_avg = fmean(hr_stream[ix_start : ix_end + 1])
                hr_max = max(hr_stream[ix_start : ix_end + 1])

                # Check if it was a fast or slow interval.
                if interval_count % 2 == 1:
                    print(f"{interval_count} % 2 == 0")
                    fast_intervals["paces"].append(pace_mps)
                    fast_intervals["hrs_avg"].append(hr_avg)
                    fast_intervals["hrs_max"].append(hr_max)
                else:
                    print(f"{interval_count} % 2 != 0")
                    slow_intervals["paces"].append(pace_mps)
                    slow_intervals["hrs_avg"].append(hr_avg)
                    slow_intervals["hrs_max"].append(hr_max)

                print(f"Interval: {interval_count}")
                print(f"Duration: {interval_time}")
                print(f"Distance: {round(interval_distance)}")
                print(f"Pace: {pace_minpkm}/km")

                print("\n\n")
                interval_count += 1

            if interval_count >= 33:
                break

        # Ensure there are 16 datapoints.
        def _ensure_datapoint_length(data, length, name):
            if len(data) != length:
                raise Exception(
                    f"The length of {name} is {len(data)}, expected {length}"
                )

        _ensure_datapoint_length(fast_intervals["paces"], 16, "fast_intervals['paces']")
        _ensure_datapoint_length(
            fast_intervals["hrs_avg"], 16, "fast_intervals['hrs_avg']"
        )
        _ensure_datapoint_length(
            fast_intervals["hrs_max"], 16, "fast_intervals['hrs_max']"
        )
        _ensure_datapoint_length(slow_intervals["paces"], 16, "slow_intervals['paces']")
        _ensure_datapoint_length(
            slow_intervals["hrs_avg"], 16, "slow_intervals['hrs_avg']"
        )
        _ensure_datapoint_length(
            slow_intervals["hrs_max"], 16, "slow_intervals['hrs_max']"
        )

        fast_pace_avg = fmean(fast_intervals["paces"])
        slow_pace_avg = fmean(slow_intervals["paces"])
        print(
            f"Pace avg in fast intervals: {speed_utils.minpkm_base10_to_base60(speed_utils.mps_to_minpkm_base10(fast_pace_avg))}/km"
        )
        print(
            f"Pace avg in slow intervals: {speed_utils.minpkm_base10_to_base60(speed_utils.mps_to_minpkm_base10(slow_pace_avg))}/km"
        )

        fast_hr_avg = fmean(fast_intervals["hrs_avg"])
        slow_hr_avg = fmean(slow_intervals["hrs_avg"])
        print(f"HR avg in fast intervals: {round(fast_hr_avg)}")
        print(f"HR avg in slow intervals: {round(slow_hr_avg)}")

        fast_hr_max = fmean(fast_intervals["hrs_max"])
        slow_hr_max = fmean(slow_intervals["hrs_max"])
        print(f"Avg of HR max in fast intervals: {round(fast_hr_max)}")
        print(f"Avg of HR max in slow intervals: {round(slow_hr_max)}")


if __name__ == "__main__":
    print("START")
    cli()
    print("END")
