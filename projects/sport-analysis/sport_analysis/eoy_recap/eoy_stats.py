import re
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from datetime import date, datetime
from statistics import mean

import datetime_utils
import log_utils as logger

N_DAYS_IN_PERIOD = 0  # Eg. 365.
N_WEEKS_IN_PERIOD = 0  # Eg. 52.143.


class EoyStats:
    def __init__(
        self,
        strava_activities_summaries: list[dict],
        start_date_after: datetime,
        start_date_before: datetime,
    ):
        self.summaries = strava_activities_summaries
        global N_DAYS_IN_PERIOD
        N_DAYS_IN_PERIOD = (start_date_before - start_date_after).days + 1
        global N_WEEKS_IN_PERIOD
        N_WEEKS_IN_PERIOD = N_DAYS_IN_PERIOD / 7

    def collect_stats(self):
        activities_count_stats = ActivitiesCountStats()
        weight_training_stats = WeightTrainingStats()
        run_stats = RunStats()
        ride_stats = RideStats()

        for summary in self.summaries:
            activities_count_stats.add_activity_summary(summary)
            weight_training_stats.add_activity_summary(summary)
            run_stats.add_activity_summary(summary)
            ride_stats.add_activity_summary(summary)

        activities_count_stats.finalize_stats()
        activities_count_stats.print_stats()
        weight_training_stats.finalize_stats()
        weight_training_stats.print_stats()
        run_stats.finalize_stats()
        run_stats.print_stats()
        ride_stats.finalize_stats()
        ride_stats.print_stats()

    def plot(self):
        self.collect_stats()


class BaseStats(ABC):
    @abstractmethod
    def add_activity_summary(self, activity): ...

    @abstractmethod
    def finalize_stats(self): ...

    @abstractmethod
    def print_stats(self): ...


class ActivitiesCountStats(BaseStats):
    def __init__(self):
        # Eg. {'WeightTraining': 211, 'Run': 60, 'Ride': 37, 'Snowboard': 7, 'Snowshoe': 3, 'Walk': 2, 'NordicSki': 2, 'Hike': 1, 'RockClimbing': 1}
        self.types_counter: dict | Counter = Counter()
        # Eg.
        # {
        #     "WeightTraining": [6263, 5321, ...],
        #     "Ride": [7984, 6788, ...],
        #     "Run": [4340, 4462, ...],
        #     "Snowboard": [8473, 7246, ...],
        #     "Snowshoe": [5183, 6258, 7381],
        #     "NordicSki": [7942, 7776],
        #     "RockClimbing": [10800],
        #     "Walk": [4232, 4494],
        #     "Hike": [2935],
        # }
        self.types_hours: dict = defaultdict(list)
        self.activities_count = 0
        self.time_tot = 0

        # Eg. {0: 63, 1: 249, 2: 36, 3: 1}
        self.n_activities_in_same_day__count__counter: dict | Counter = Counter()
        # Eg.
        # {
        #     "2025-01-10": 3,
        #     "2025-12-09": 2,
        #     "2025-11-20": 2,
        #     "2025-11-05": 1,
        #     ...
        # }
        self._day_str__n_activities__counter = Counter()

    def add_activity_summary(self, summary):
        self.activities_count += 1

        # types_counter stat: # activities by type.
        activity_type = summary["type"]
        self.types_counter.update([activity_type])

        # types_hours stat: # hours by type.
        self.types_hours[activity_type].append(summary["moving_time"])
        self.time_tot += summary["moving_time"]

        # n_activities_in_same_day__count__counter: # days by # activities in the same day.
        day_str = (
            datetime_utils.iso_string_to_datetime(summary["start_date_local"])
            .date()
            .isoformat()
        )
        self._day_str__n_activities__counter.update([day_str])

    def finalize_stats(self):
        # Sort types_counter.
        self.types_counter = dict(
            sorted(self.types_counter.items(), key=lambda item: item[1], reverse=True)
        )

        # Sort types_hours.
        self.types_hours = dict(
            sorted(
                self.types_hours.items(), key=lambda item: sum(item[1]), reverse=True
            )
        )

        # Build n_activities_in_same_day__count__counter and sort it.
        self.n_activities_in_same_day__count__counter.update(
            self._day_str__n_activities__counter.values()
        )
        # Rest days.
        self.n_activities_in_same_day__count__counter[0] = N_DAYS_IN_PERIOD - sum(
            self.n_activities_in_same_day__count__counter.values()
        )
        self.n_activities_in_same_day__count__counter = dict(
            sorted(
                self.n_activities_in_same_day__count__counter.items(),
                key=lambda item: item[0],
                reverse=False,
            )
        )

    def print_stats(self):
        rest_days = self.n_activities_in_same_day__count__counter[0]
        active_days = N_DAYS_IN_PERIOD - rest_days

        logger.info("[bold on green] > Activity types[/]")
        logger.info(f"[dim bright_black]TOT activities: {self.activities_count}[/]")
        for k, v in self.types_counter.items():
            logger.info(f"{k}: {v} ({round(v*100/self.activities_count)}%)")

        logger.info("[bold on green] > Duration (moving time)[/]")
        avg_time_per_active_day = self.time_tot / active_days
        avg_time_per_week = self.time_tot / N_WEEKS_IN_PERIOD
        _ = datetime_utils.seconds_to_hh_mm
        logger.info(
            f"[dim bright_black]TOT time: {_(self.time_tot)} ({_(round(avg_time_per_active_day))} per active day, {_(round(avg_time_per_week))} per week)[/]"
        )
        for k, v in self.types_hours.items():
            logger.info(
                f"{k}{' (elapsed time)' if k == 'WeightTraining' else ''}: {_(sum(v))} (avg {_(round(mean(v)))}, max {_(max(v))}, {round(sum(v)*100/self.time_tot)}%)"
            )

        logger.info("[bold on green] > Activities in the same day[/]")
        logger.info(
            f"[dim bright_black]rest days: {rest_days} days ({round(rest_days / N_WEEKS_IN_PERIOD, 1)} per week)[/]"
        )
        logger.info(
            f"[dim bright_black]active days: {active_days} days ({round(active_days / N_WEEKS_IN_PERIOD, 1)} per week)[/]"
        )
        for k, v in self.n_activities_in_same_day__count__counter.items():
            if k != 0:
                logger.info(
                    f"{k} activit{'y' if k < 2 else 'ies'}: {v} day{'s' if v > 1 else ''} ({round(v/N_WEEKS_IN_PERIOD, 1)} per week)"
                )


class WeightTrainingStats(BaseStats):
    def __init__(self):
        self.target_counter: dict | Counter = Counter()

    def add_activity_summary(self, summary):
        # target_counter stat: # times I trained that target.
        if summary["type"].lower() != "weighttraining":
            return
        name = summary["name"]

        # Clean-up the prefix.
        if name.lower().startswith("weight training: "):
            name = name[17:]
        if name.lower().startswith("powerbuilding class: "):
            name = name[21:]

        targets = [x.lower().strip() for x in name.split(",")]

        # Clean-up names.
        for i in range(len(targets)):
            target = targets[i]

            # "powerlifting class" -> "powerlifting".
            if "powerlifting" in target:
                targets[i] = "powerlifting"
            # "calisthenics class" -> "calisthenics".
            elif "calisthenics" in target:
                targets[i] = "calisthenics"
            # "pr bench press: 105 kg💪🏆" -> "powerlifting".
            elif "bench press" in target:
                targets[i] = "powerlifting"
            # "ring muscle-up progression day #10" -> "calisthenics".
            elif target.startswith("ring muscle-up progression"):
                targets[i] = "calisthenics"
            # "triceps 🦠" -> "triceps".
            elif target.endswith(" 🦠"):
                targets[i] = target[:-2]
            # "left elbow isometrics" -> "left elbow".
            elif re.match(r"^left elbow .*$", target):
                targets[i] = "left elbow"
            # "legs isometrics" -> "legs".
            elif re.match(r"^legs .*$", target):
                targets[i] = "legs"
            # "chest (push&pull party 🎉)" -> "chest".
            elif res := re.match(r"^(.*) \(.*\)$", target):
                targets[i] = res.group(1)

        self.target_counter.update(targets)

    def finalize_stats(self):
        # Sort target_counter.
        self.target_counter = dict(
            sorted(self.target_counter.items(), key=lambda item: item[1], reverse=True)
        )

    def print_stats(self):
        logger.info("[bold on green] > Weight training target[/]")
        activities_count = sum(self.target_counter.values())
        for k, v in self.target_counter.items():
            logger.info(f"{k}: {v} ({round(v*100/activities_count)}%)")


class RunStats(BaseStats):
    def __init__(self):
        self.run_type = {
            "interval run 100m": 0,
            "interval run 200m": 0,
            "interval run 300m": 0,
            "interval run 400m": 0,
            "interval run 500m": 0,
            "interval run 600m": 0,
            "interval run 800m": 0,
            "interval run 1000m": 0,
            "interval run 1500m": 0,
            "interval run 2000m": 0,
            "interval run 2500m": 0,
            "interval run 3000m": 0,
            "interval run 4000m": 0,
            "interval run 5000m": 0,
            "run <10km": 0,
            "run 10km": 0,
            "run 10-21km": 0,
            "run HM 21km": 0,
            "run 21-30km": 0,
            "run >30km": 0,
            "trail run <250m elevation": 0,
            "trail run 250-500m elevation": 0,
            "trail run 500-1000m elevation": 0,
            "trail run 1000-1500m elevation": 0,
            "trail run 1500-2000m elevation": 0,
            "trail run >2000m elevation": 0,
        }
        self.run_count = 0
        self.distance_tot = 0
        self.elevation_gain_tot = 0

    def add_activity_summary(self, summary):
        if summary["type"].lower() != "run":
            return
        self.run_count += 1
        name = summary["name"]
        distance = summary["distance"]
        self.distance_tot += distance
        elevation_gain = summary["total_elevation_gain"]
        self.elevation_gain_tot += elevation_gain

        # run_type stat: # activities by run type, distance, elevation.
        # Split run, trail run, interval run.
        key = "run"
        if summary["sport_type"].lower() == "trailrun":
            key = "trail run"
        elif res := re.match(r"^\d{1,2}x(\d{3,4}m)$", name):
            key = f"interval run {res.group(1)}"

        # Split run by distance and trail run by elevation.
        if key == "run":
            if distance <= 9_500:
                key = "run <10km"
            elif 9_500 < distance <= 10_500:
                key = "run 10km"
            elif 10_500 < distance <= 20_500:
                key = "run 10-21km"
            elif 20_500 < distance <= 21_500:
                key = "run HM 21km"
            elif 21_500 < distance <= 30_500:
                key = "run 21-30km"
            elif distance > 30_500:
                key = "run >30km"
        elif key == "trail run":
            if elevation_gain < 250:
                key = "trail run <250m elevation"
            elif 250 <= elevation_gain < 500:
                key = "trail run 250-500m elevation"
            elif 500 <= elevation_gain < 1000:
                key = "trail run 500-1000m elevation"
            elif 1000 <= elevation_gain < 1500:
                key = "trail run 1000-1500m elevation"
            elif 1500 <= elevation_gain <= 2000:
                key = "trail run 1500-2000m elevation"
            elif elevation_gain > 2000:
                key = "trail run >2000m elevation"

        self.run_type[key] += 1

    def finalize_stats(self): ...

    def print_stats(self):
        logger.info("[bold on green] > Run[/]")
        logger.info(
            f"[dim bright_black]TOT runs: {self.run_count} ({round(self.run_count / N_WEEKS_IN_PERIOD, 1)} per week)[/]"
        )
        logger.info(
            f"[dim bright_black]TOT distance: {round(self.distance_tot/1000)}km ({round(self.distance_tot/1000 / N_WEEKS_IN_PERIOD)}km per week)[/]"
        )
        logger.info(
            f"[dim bright_black]TOT elevation gain: {round(self.elevation_gain_tot)}m[/]"
        )
        for k, v in self.run_type.items():
            if v:
                logger.info(f"{k}: {v}")


class RideStats(BaseStats):
    def __init__(self):
        self.ride_distance = {
            "<20km": 0,
            "20-50km": 0,
            ">50km": 0,
        }
        self.ride_elevation = {
            "<500m elevation": 0,
            "500-1000m elevation": 0,
            "1000-2000m elevation": 0,
            ">2000m elevation": 0,
        }
        self.ride_count = 0
        self.distance_tot = 0
        self.elevation_gain_tot = 0

    def add_activity_summary(self, summary):
        if summary["type"].lower() != "ride":
            return
        self.ride_count += 1
        # name = activity["name"]
        distance = summary["distance"]
        self.distance_tot += distance
        elevation_gain = summary["total_elevation_gain"]
        self.elevation_gain_tot += elevation_gain

        # ride_distance stat: # rides by distance.
        # Split ride by distance.
        if distance <= 19_500:
            key = "<20km"
        elif 19_500 < distance <= 50_500:
            key = "20-50km"
        elif distance > 50_500:
            key = ">50km"
        self.ride_distance[key] += 1

        # ride_elevation stat: # rides by elevation gain.
        # Split ride by elevation.
        if elevation_gain < 500:
            key = "<500m elevation"
        elif 500 <= elevation_gain < 1000:
            key = "500-1000m elevation"
        elif 1000 <= elevation_gain <= 2000:
            key = "1000-2000m elevation"
        elif elevation_gain > 2000:
            key = ">2000m elevation"
        self.ride_elevation[key] += 1

    def finalize_stats(self): ...

    def print_stats(self):
        logger.info("[bold on green] > Ride[/]")
        logger.info(f"[dim bright_black]TOT rides: {self.ride_count}[/]")
        logger.info(
            f"[dim bright_black]TOT distance: {round(self.distance_tot/1000)}km ({round(self.distance_tot/1000 / self.ride_count)}km per ride)[/]"
        )
        logger.info(
            f"[dim bright_black]TOT elevation gain: {round(self.elevation_gain_tot)}m[/]"
        )
        for k, v in self.ride_distance.items():
            if v:
                logger.info(f"{k}: {v}")
        for k, v in self.ride_elevation.items():
            if v:
                logger.info(f"{k}: {v}")
