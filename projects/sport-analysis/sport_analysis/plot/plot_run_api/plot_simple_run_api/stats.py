from typing import Literal

import pandas as pd
import speed_utils


def compute_stats_for_custom_splits(
    distance_stream: list[float],
    moving_time_stream: list[float],
    hr_stream: list[float],
    splits_distance: Literal["AUTO"] | int,
) -> pd.DataFrame:
    """
    Compute stats for custom splits: splits that are not those automatically computed
     by Garmin.

    Args:
        distance_stream: see garmin_connect_client.ActivityDetailsResponse.get_distance_stream().
        moving_time_stream: see garmin_connect_client.ActivityDetailsResponse.get_moving_time_stream().
        hr_stream: see garmin_connect_client.ActivityDetailsResponse.get_heartrate_stream().
        splits_distance: "AUTO" to plot custom splits with default distance
         (5000m splits for run >= 15km, else 2000m splits); 2500 (or any int) to
         choose the splits distance; None (default) not to plot splits. Custom splits
         are not those automatically computer by Garmin.
    """
    # Validate split_distance.
    if splits_distance != "AUTO" and not isinstance(splits_distance, int):
        raise ValueError(
            f"split_distance arg invalid: {splits_distance}\nValid values: AUTO or an integer"
        )

    df = pd.DataFrame(
        {
            "distance": distance_stream,
            "moving_time": moving_time_stream,
            "hr": hr_stream,
        }
    )

    # If split_distance is not given, use 5000m splits if the run is 15+ km,
    #  2000m splits if the run is shorter.
    max_distance = df.iloc[-1]["distance"]
    if splits_distance == "AUTO":
        if max_distance >= 15_000:
            splits_distance = 5_000
        else:
            splits_distance = 2_000

    # Add the split_id group: 0 for the first 5000m, 1 for the next 5000m, etc.
    df["split_id"] = (df["distance"] // splits_distance).astype(int)
    # If the last split is long < 5000/2 meters, then join it to the second last.
    if (max_distance % splits_distance) <= (splits_distance / 2):
        last = df.iloc[-1]["split_id"]
        df.loc[df["split_id"] == last, "split_id"] = last - 1

    # Group by split_id and aggregate the meaningful data.
    df = df.groupby("split_id").agg(
        start_distance=("distance", "min"),
        end_distance=("distance", "max"),
        start_moving_time=("moving_time", "min"),
        end_moving_time=("moving_time", "max"),
        split_hr_avg=("hr", "mean"),
    )

    # Compute split_speed_avg.
    df["split_speed_avg"] = (df["end_distance"] - df["start_distance"]) / (
        df["end_moving_time"] - df["start_moving_time"]
    )
    df["split_speed_avg_str"] = speed_utils.minpkm_base10_to_base60(
        speed_utils.mps_to_minpkm_base10(df["split_speed_avg"])
    )

    # df example:
    #           start_distance  end_distance  start_moving_time  end_moving_time  split_hr_avg  split_speed_avg split_speed_avg_str
    # split_id
    # 0               0.000000   4998.080078                0.0           1435.0    142.786908         3.482983                4:47
    # 1            5001.240234   9998.389648             1436.0           2917.0    141.076248         3.374172                4:56
    # 2           10002.040039  14997.139648             2918.0           4398.0    145.268194         3.375067                4:56
    # 3           15000.259766  19997.599609             4399.0           5866.0    149.896458         3.406503                4:54
    # 4           20000.900391  24811.689453             5867.0           7239.0    155.822287         3.506406                4:45
    return df
