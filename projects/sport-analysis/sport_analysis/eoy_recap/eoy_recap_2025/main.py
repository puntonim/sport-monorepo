from datetime import datetime
from pathlib import Path

import datetime_utils
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from strava_client import StravaClient
from strava_client.strava_token_managers import (
    AwsParameterStoreStravaTokenManager,
    FakeTestStravaTokenManager,
    FileStravaTokenManager,
)

from ...base_cli_view import ConsoleAdapter
from ...conf import settings
from .stats_activities_count import ActivitiesCountStats
from .stats_ride import RideStats
from .stats_run import RunStats
from .stats_weight import WeightStats
from .stats_weight_training import WeightTrainingStats

console = ConsoleAdapter()


class EoyRecap2025:
    def __init__(
        self,
        start_date_after: datetime | str = "2025-01-01T00:00:00+01:00",
        start_date_before: datetime | str = "2025-12-31T23:59:59+01:00",
        strava_token_manager: (
            AwsParameterStoreStravaTokenManager
            | FileStravaTokenManager
            | FakeTestStravaTokenManager
            | None
        ) = None,
    ):
        """
        Args:
            start_date_after: eg. "2024-01-01T00:00:01+01:00" or datetime(2024, 1, 6, 17, 20, tzinfo=ZoneInfo("Europe/Rome")).
            start_date_before: eg. "2024-01-01T00:00:01+01:00" or datetime(2024, 1, 6, 17, 20, tzinfo=ZoneInfo("Europe/Rome")).
            strava_token_manager: use FakeTestStravaTokenManager when
             replaying VCR episodes.
        """
        # Parse start_date_after|before.
        self.start_date_after: datetime = datetime_utils.parse_datetime_arg(
            start_date_after
        )
        self.start_date_before: datetime = datetime_utils.parse_datetime_arg(
            start_date_before
        )
        # Eg. 365.
        self.n_days_in_period = (
            self.start_date_before - self.start_date_after
        ).days + 1

        strava_token_manager = (
            strava_token_manager
            or AwsParameterStoreStravaTokenManager(
                settings.TOKEN_JSON_PARAMETER_STORE_KEY_PATH,
                settings.CLIENT_ID_PARAMETER_STORE_KEY_PATH,
                settings.CLIENT_SECRET_PARAMETER_STORE_KEY_PATH,
            )
        )
        self.strava = StravaClient(strava_token_manager.get_access_token())
        self.summaries: list[dict] = list()

    def _collect_strava_activities_summaries(self):
        # Collect all Strava activity summaries in the period.
        page_n = 1
        while True:
            response = self.strava.list_activities(
                after_ts=self.start_date_after,
                before_ts=self.start_date_before,
                n_results_per_page=100,
                page_n=page_n,
            )
            n = len(response.data)

            self.summaries.extend(response.data)

            # If we got 100 results, then there must be another page, otherwise this was
            #  the last page.
            if n < 100:
                break
            page_n += 1

    def plot(self):
        console.print("\n[bold underline on white]EOY RECAP 2025[/]")
        console.print(
            f"[underline]Filter[/]: [bold on yellow]start-date-after[/] = {self.start_date_after.isoformat()}",
            highlight=False,
        )
        console.print(
            f"[underline]Filter[/]: [bold on yellow]start-date-before[/] = {self.start_date_before.isoformat()}",
            highlight=False,
        )

        self.figure, self.axes_mosaic = self._make_subplot_mosaic()
        self.figure: Figure
        self.axes_mosaic: dict[str, Axes]

        self._collect_strava_activities_summaries()
        self._plot_title()
        self._plot_stats()

        save_to_png_file_path = Path(__file__).parent / "2025.png"
        plt.savefig(save_to_png_file_path)
        # plt.show()

    def _plot_title(self):
        ax: Axes = self.axes_mosaic["title"]
        ax.annotate(
            text="Year in sport 2025",
            # Point to annotate: the top right of the bar.
            xy=(0.5, 0.5),
            # Position of the text, a tuple made of:
            #  - a number big enough to center vertically;
            #  - a number to move it just above the first chart.
            xytext=(-5.5, 1.0),
            textcoords="offset fontsize",  # Coord system of xytext.
            fontsize=15,
            fontweight="bold",
        )

    def _plot_stats(self):
        activities_count_stats = ActivitiesCountStats(self.n_days_in_period)
        weight_training_stats = WeightTrainingStats(self.n_days_in_period)
        run_stats = RunStats(self.n_days_in_period)
        ride_stats = RideStats(self.n_days_in_period)
        weight_stats = WeightStats()

        for summary in self.summaries:
            activities_count_stats.add_activity_summary(summary)
            weight_training_stats.add_activity_summary(summary)
            run_stats.add_activity_summary(summary)
            ride_stats.add_activity_summary(summary)

        ## Activities count.
        activities_count_stats.finalize_stats()
        activities_count_stats.print_stats()
        activities_count_stats.plot(
            self.axes_mosaic["activity-types"],
            self.axes_mosaic["activity-hours"],
            self.axes_mosaic["activity-freq"],
        )

        ## Weight training.
        weight_training_stats.finalize_stats()
        weight_training_stats.print_stats()
        weight_training_stats.plot(
            self.axes_mosaic["weight-target"], self.axes_mosaic["weight-text"]
        )

        ## Run.
        run_stats.finalize_stats()
        run_stats.print_stats()
        run_stats.plot(self.axes_mosaic["run-category"], self.axes_mosaic["run-text"])

        ## Ride.
        ride_stats.finalize_stats()
        ride_stats.print_stats()
        ride_stats.plot(
            self.axes_mosaic["ride-category"], self.axes_mosaic["ride-text"]
        )

        ## Body weight.
        weight_stats.finalize_stats()
        weight_stats.print_stats()
        weight_stats.plot(self.axes_mosaic["weight"])

    def _make_subplot_mosaic(self) -> tuple[Figure, dict[str, Axes]]:
        # Docs for subplot_mosaic():
        #  https://matplotlib.org/stable/users/explain/axes/arranging_axes.html#variable-widths-or-heights-in-a-grid
        #  https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplot_mosaic.html#matplotlib.pyplot.subplot_mosaic
        # fmt: off
        _matrix = [
            # 2 rows, 6 cols.
            # Note: "_N" are empty charts used for spacing between actual charts.
            [".", "title", "title", "title", "title", "title", "title", "."],
            [".", "activity-types", ".", "activity-hours", ".", "activity-freq", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", "weight-target", "weight-text", "weight-text", "weight-text", "weight-text", "weight-text", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            ["run-text", "run-text", "run-text", "run-text", "run-text", "run-text", "run-category", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", "ride-category", "ride-text", "ride-text", "ride-text", "ride-text", "ride-text", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", "weight", "weight", "weight", "weight", "weight", "weight", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
        ]
        # fmt: on
        figure, mosaic = plt.subplot_mosaic(
            _matrix,
            gridspec_kw=dict(
                # The relative sizes of the subplots.
                width_ratios=(
                    0.4,  # 1st spacing col.
                    1.0,  # Col used fi. for Activity types bar chart in the first row.
                    1.0,  # 2nd spacing col.
                    1.0,  # Col used fi. for Duration bar chart in the first row.
                    2.6,  # 3rd spacing col.
                    1.0,  # Col used fi. for Daily freq bar chart in the first row.
                    1.0,  # Col used fi. for the Run bar chart in the 3rd row.
                    0.9,  # Last spacing col.
                ),
                height_ratios=(
                    0.35,  # 1st spacing row, on top of everything.
                    0.7,  # Row with the Activity chart.
                    0.25,  # 2nd spacing row, between the 1st and 2nd chart rows.
                    0.6,  # Row with the Weight Training chart.
                    0.1,  # 3rd spacing row, between the 2nd and 3rd chart rows.
                    0.7,  # Row with the Run chart.
                    0.1,  # 3rd spacing row, between the 3rd and 4th chart rows.
                    0.8,  # Row with the Ride chart.
                    0.1,  # 4th spacing row, between the 4th and 5th chart rows.
                    0.4,  # Row with the Weight chart.
                    0.1,  # Last spacing row, at the bottom of everything.
                ),
            ),
            figsize=(5, 14.2),  # width, height.
            layout="constrained",
        )
        for r in _matrix:
            for ax in r:
                if ax != ".":
                    mosaic[ax].set_axis_off()
        return figure, mosaic
