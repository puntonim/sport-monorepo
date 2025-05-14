from pathlib import Path

import log_utils as logger
import matplotlib.pyplot as plt
from garmin_connect_client import GarminConnectClient
from garmin_connect_client.garmin_connect_token_managers import (
    FakeTestGarminConnectTokenManager,
    FileGarminConnectTokenManager,
)
from strava_client import StravaClient
from strava_client.strava_token_managers import (
    AwsParameterStoreStravaTokenManager,
    FakeTestStravaTokenManager,
    FileStravaTokenManager,
)

from ...conf import settings
from ...conf.settings_module import ROOT_DIR

# IMP: there is NOT a CLI command for this function because it's more like a testing
#  thing. I don't really see a use case for it, so no need for a CLI.


def plot_like_garmin_and_strava_websites_api(
    strava_activity_id: int,
    garmin_activity_id: int,
    title: str | None = None,
    strava_token_manager: (
        AwsParameterStoreStravaTokenManager
        | FileStravaTokenManager
        | FakeTestStravaTokenManager
        | None
    ) = None,
    garmin_connect_token_manager: (
        FileGarminConnectTokenManager | FakeTestGarminConnectTokenManager | None
    ) = None,
    save_to_png_file_path: Path | None = None,
):
    """
    Create exactly the same charts as in Strava website and Garmin Connect website.
    Strava website plots charts over distance only (x-axis is distance).
    Garmin Connect website plots charts over time or distance, so you can choose if the
     x-axis is time or distance.
    This function creates exactly the same charts.

    Note: sometime the charts on Strava and Garmin Connect websites are slightly
     different, mostly due to how they consider not moving datapoints. The
     charts created by this function always replicate the charts in the website, so
     sometimes the Garmin and Strava lines do not match (because they don't match in
     the websites either). There is not right and wrong, it is just a slightly different
     way to consider not moving datapoints.
    """

    ## Strava.
    strava_token_manager = strava_token_manager or AwsParameterStoreStravaTokenManager(
        settings.TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
        settings.CLIENT_ID_PARAMETER_STORE_KEY_PATH,
        settings.CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
    )
    strava = StravaClient(strava_token_manager.get_access_token())
    strava_streams = strava.get_streams(
        strava_activity_id,
        stream_types=[
            "time",
            "distance",
            "altitude",
            "heartrate",
            "moving",
        ],
    )
    # Shortcuts.
    strava_elapsed_time_stream = strava_streams.get_elapsed_time_stream()
    strava_moving_time_stream = strava_streams.compute_moving_time_stream()
    strava_hr_stream = strava_streams.get_heartrate_stream()
    strava_distance_stream = strava_streams.get_distance_stream()
    strava_altitude_stream = strava_streams.get_altitude_stream()

    ## Garmin.
    garmin_token_manager = (
        garmin_connect_token_manager
        or FileGarminConnectTokenManager(
            token_file_path=ROOT_DIR / "garmin-connect-token.json"
        )
    )
    garmin = GarminConnectClient(token_manager=garmin_token_manager)
    response = garmin.get_activity_details(
        garmin_activity_id,
        max_metrics_data_count=100 * 1000,
        do_include_polyline=False,
        # max_polyline_count: int = 4000,
        do_keep_raw_data=False,
    )
    # Shortcuts.
    garmin_hr_stream = response.get_heartrate_stream()
    garmin_non_paused_time_stream = response.get_non_paused_time_stream()
    garmin_distance_stream = response.get_distance_stream()
    # Ensure all Garmin and Strava dataset have the same size.
    if not (
        response.original_dataset_size
        == len(garmin_hr_stream)
        == len(garmin_non_paused_time_stream)
        == len(garmin_distance_stream)
    ):
        logger.info(
            "\n\nNote: NOT all Garmin streams in the datasets have the same size as the original dataset!!\n\n"
        )

    if not (response.original_dataset_size == len(strava_hr_stream)):
        logger.info(
            "\n\nNote: the Strava dataset does NOT have the same size as the original dataset!!\n\n"
        )

    ## Charts.
    plt.figure(figsize=(10, 6), layout="constrained")

    # First chart.
    plt.subplot(2, 1, 1)
    ln_hr_strava = plt.plot(
        strava_distance_stream,
        strava_hr_stream,
        color="red",
        linewidth=1,
        linestyle="-",
        # marker=".",
        label="Strava",
    )
    ln_hr_garmin = plt.plot(
        garmin_distance_stream,
        garmin_hr_stream,
        color="blue",
        linewidth=1,
        linestyle="-",
        # marker=".",
        label="Garmin",
    )

    axes = plt.gca()
    axes.set_ylabel("Heart rate [bpm]")
    # axes.yaxis.label.set_color("red")
    axes.set_xlabel(f"{'Distance [m]'}")
    axes.yaxis.grid(
        color="gray",
        alpha=0.2,
        linestyle="--",
    )

    plt.twinx()
    axes = plt.gca()

    ln_alt = plt.plot(
        strava_distance_stream,
        strava_altitude_stream,
        color="gray",
        alpha=0.2,
        linewidth=0,
        linestyle="-",
        # marker=".",
        label="Altitude",
    )
    plt.fill_between(
        x=strava_distance_stream,
        y1=strava_altitude_stream,
        color="gray",
        alpha=0.1,
    )
    axes.set_ylabel("Altitude [m]")

    title = title + "\n" or ""
    title += f"Heart rate for Strava activity {strava_activity_id} and Garmin activity {garmin_activity_id}"
    plt.title(title)
    lns = ln_hr_strava + ln_hr_garmin + ln_alt
    labs = [l.get_label() for l in lns]
    plt.legend(lns, labs, loc="upper right")

    # Second chart.
    plt.subplot(2, 1, 2)
    ln_hr_strava = plt.plot(
        strava_moving_time_stream,
        # strava_elapsed_time_stream,
        strava_hr_stream,
        color="red",
        linewidth=1,
        linestyle="-",
        # marker=".",
        label="Strava",
    )
    ln_hr_garmin = plt.plot(
        garmin_non_paused_time_stream,
        garmin_hr_stream,
        color="blue",
        linewidth=1,
        linestyle="-",
        # marker=".",
        label="Garmin",
    )

    axes = plt.gca()
    axes.set_ylabel("Heart rate [bpm]")
    # axes.yaxis.label.set_color("red")
    axes.set_xlabel(f"{'Time [s]'}")
    axes.yaxis.grid(
        color="gray",
        alpha=0.2,
        linestyle="--",
    )

    plt.twinx()
    axes = plt.gca()

    ln_alt = plt.plot(
        strava_moving_time_stream,
        strava_altitude_stream,
        color="gray",
        alpha=0.2,
        linewidth=0,
        linestyle="-",
        # marker=".",
        label="Altitude",
    )
    plt.fill_between(
        x=strava_moving_time_stream,
        y1=strava_altitude_stream,
        color="gray",
        alpha=0.1,
    )
    axes.set_ylabel("Altitude [m]")

    lns = ln_hr_strava + ln_hr_garmin + ln_alt
    labs = [l.get_label() for l in lns]
    plt.legend(lns, labs, loc="upper right")

    if save_to_png_file_path:
        logger.info(f"Created image: {save_to_png_file_path}")
        plt.savefig(save_to_png_file_path)
    else:
        plt.show()
