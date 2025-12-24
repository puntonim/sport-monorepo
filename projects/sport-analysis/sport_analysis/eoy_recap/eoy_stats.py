import re
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from datetime import date
from statistics import mean

import datetime_utils
import log_utils as logger

N_WEEKS_IN_A_YEAR = 52.143


class EoyStats:
    def __init__(self, strava_activities: list[dict]):
        self.strava_activities = strava_activities

    def collect_stats(self):
        activities_count_stats = ActivitiesCountStats()
        weight_training_stats = WeightTrainingStats()
        run_stats = RunStats()
        ride_stats = RideStats()

        for activity in self.strava_activities:
            activities_count_stats.add_activity(activity)
            weight_training_stats.add_activity(activity)
            run_stats.add_activity(activity)
            ride_stats.add_activity(activity)

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
    def add_activity(self, activity): ...

    @abstractmethod
    def finalize_stats(self): ...

    @abstractmethod
    def print_stats(self): ...


class ActivitiesCountStats(BaseStats):
    def __init__(self):
        self.types_counter: dict | Counter = Counter()
        self.types_hours: dict = defaultdict(list)
        self.activities_count = 0
        self.time_tot = 0

        self.activities_same_day_counter: dict | Counter = Counter()
        self._day_str__n_activities_counter = Counter()
        self._n_days_in_year = None

    def add_activity(self, activity):
        self.activities_count += 1

        # types_counter stat: # activities by type.
        activity_type = activity["type"]
        self.types_counter.update([activity_type])

        # types_hours stat: # hours by type.
        self.types_hours[activity_type].append(activity["moving_time"])
        self.time_tot += activity["moving_time"]

        # activities_same_day_counter: # days by # activities in the same day.
        day_str = (
            datetime_utils.iso_string_to_datetime(activity["start_date_local"])
            .date()
            .isoformat()
        )
        self._day_str__n_activities_counter.update([day_str])

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

        # Build activities_same_day_counter and sort it.
        self.activities_same_day_counter.update(
            self._day_str__n_activities_counter.values()
        )
        # Compute the number of days in the year (365 or 366).
        year = datetime_utils.iso_string_to_datetime(
            list(self._day_str__n_activities_counter.keys())[0]
        ).year
        self._n_days_in_year = (
            date(year=year + 1, month=1, day=1) - date(year=year, month=1, day=1)
        ).days
        self.activities_same_day_counter[0] = self._n_days_in_year - sum(
            self.activities_same_day_counter.values()
        )
        self.activities_same_day_counter = dict(
            sorted(
                self.activities_same_day_counter.items(),
                key=lambda item: item[0],
                reverse=False,
            )
        )

    def print_stats(self):
        rest_days = self.activities_same_day_counter[0]
        active_days = self._n_days_in_year - rest_days

        logger.info("[bold on green]Types[/]")
        logger.info(f"TOT activities: {self.activities_count}")
        for k, v in self.types_counter.items():
            logger.info(f"{k}: {v}")

        logger.info("[bold on green]Duration[/]")
        avg_time_per_active_day = self.time_tot / active_days
        avg_time_per_week = self.time_tot / N_WEEKS_IN_A_YEAR
        logger.info(
            f"TOT time: {datetime_utils.seconds_to_hh_mm(self.time_tot)} ({datetime_utils.seconds_to_hh_mm(round(avg_time_per_active_day))} per active day, {datetime_utils.seconds_to_hh_mm(round(avg_time_per_week))} per week)"
        )
        for k, v in self.types_hours.items():
            logger.info(
                f"{k}: {datetime_utils.seconds_to_hh_mm(sum(v))} (avg {datetime_utils.seconds_to_hh_mm(round(mean(v)))}, max {datetime_utils.seconds_to_hh_mm(max(v))})"
            )

        logger.info("[bold on green]Activities in the same day[/]")
        logger.info(
            f"rest days: {rest_days} days ({round(rest_days / N_WEEKS_IN_A_YEAR, 1)} per week)"
        )
        logger.info(
            f"active days: {active_days} days ({round(active_days / N_WEEKS_IN_A_YEAR, 1)} per week)"
        )
        for k, v in self.activities_same_day_counter.items():
            if k != 0:
                logger.info(
                    f"{k} activit{'y' if k < 2 else 'ies'}: {v} day{'s' if v > 1 else ''} ({round(v/N_WEEKS_IN_A_YEAR, 1)} per week)"
                )


class WeightTrainingStats(BaseStats):
    def __init__(self):
        self.target_counter: dict | Counter = Counter()

    def add_activity(self, activity):
        # target_counter stat: # times I trained that target.
        if activity["type"].lower() != "weighttraining":
            return
        name = activity["name"]

        # Clean-up the prefix.
        if name.lower().startswith("weight training: "):
            name = name[17:]

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
        logger.info("[bold on green]Weight training target[/]")
        for k, v in self.target_counter.items():
            logger.info(f"{k}: {v}")


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

    def add_activity(self, activity):
        if activity["type"].lower() != "run":
            return
        self.run_count += 1
        name = activity["name"]
        distance = activity["distance"]
        self.distance_tot += distance
        elevation_gain = activity["total_elevation_gain"]
        self.elevation_gain_tot += elevation_gain

        # run_type stat: # activities by run type, distance, elevation.
        # Split run, trail run, interval run.
        key = "run"
        if activity["sport_type"].lower() == "trailrun":
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
        logger.info("[bold on green]Run[/]")
        logger.info(
            f"TOT runs: {self.run_count} ({round(self.run_count / N_WEEKS_IN_A_YEAR, 1)} per week)"
        )
        logger.info(
            f"TOT distance: {round(self.distance_tot/1000)}km ({round(self.distance_tot/1000 / N_WEEKS_IN_A_YEAR)}km per week)"
        )
        logger.info(f"TOT elevation gain: {round(self.elevation_gain_tot)}m")
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

    def add_activity(self, activity):
        if activity["type"].lower() != "ride":
            return
        self.ride_count += 1
        # name = activity["name"]
        distance = activity["distance"]
        self.distance_tot += distance
        elevation_gain = activity["total_elevation_gain"]
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
        logger.info("[bold on green]Ride[/]")
        logger.info(f"TOT rides: {self.ride_count}")
        logger.info(
            f"TOT distance: {round(self.distance_tot/1000)}km ({round(self.distance_tot/1000 / self.ride_count)}km per ride)"
        )
        logger.info(f"TOT elevation gain: {round(self.elevation_gain_tot)}m")
        for k, v in self.ride_distance.items():
            if v:
                logger.info(f"{k}: {v}")
        for k, v in self.ride_elevation.items():
            if v:
                logger.info(f"{k}: {v}")
