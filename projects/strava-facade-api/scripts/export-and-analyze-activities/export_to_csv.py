from pathlib import Path

import requests
from strava_client import StravaClient
from strava_client.token_managers import (
    AwsParameterStoreTokenManager,
    AwsParameterStoreTokenManagerException,
)

from strava_facade_api import domain_exceptions as exceptions

CURR_DIR = Path(__file__).parent


def main():
    # Get an access token.
    try:
        access_token = AwsParameterStoreTokenManager(
            "/strava-facade-api/production/strava-api-token-json",
            "/strava-facade-api/production/strava-api-client-id",
            "/strava-facade-api/production/strava-api-client-secret",
        ).get_access_token()
    except AwsParameterStoreTokenManagerException as exc:
        raise exceptions.StravaAuthenticationError(str(exc)) from exc
    try:
        strava = StravaClient(access_token)
    except requests.HTTPError as exc:
        raise exceptions.StravaApiError(str(exc)) from exc

    data = list()

    # Get all activities of the given type for the given day.
    after_ts = 1704063600  # 2024-01-02 00:00:00 UTC.
    # after_ts = 1707174000
    # before_ts = 1707260399
    # activity_type = "WeightTraining"
    activities = strava.list_activities(after_ts, n_results_per_page=200)
    if not activities:
        raise exceptions.NoActivityFound

    for i, activity in enumerate(activities):
        if i > 70:
            # Rate limits: 100 requests every 15 minutes
            # https://developers.strava.com/docs/rate-limits/
            break

        # `activity` is a dict like:
        # {
        #     "resource_state": 2,
        #     "athlete": {
        #         "id": 115890775,
        #         "resource_state": 1
        #     },
        #     "name": "Weight training: broken finger, abs, triceps, legs",
        #     "distance": 0.0,
        #     "moving_time": 7157,
        #     "elapsed_time": 7157,
        #     "total_elevation_gain": 0,
        #     "type": "WeightTraining",
        #     "sport_type": "WeightTraining",
        #     "id": 10709853894,
        #     "start_date": "2024-02-06T17:20:32Z",
        #     "start_date_local": "2024-02-06T18:20:32Z",
        #     "timezone": "(GMT+01:00) Africa/Algiers",
        #     "utc_offset": 3600.0,
        #     "location_city": null,
        #     "location_state": null,
        #     "location_country": "Italy",
        #     "achievement_count": 0,
        #     "kudos_count": 0,
        #     "comment_count": 0,
        #     "athlete_count": 1,
        #     "photo_count": 0,
        #     "map": {
        #         "id": "a10709853894",
        #         "summary_polyline": "",
        #         "resource_state": 2
        #     },
        #     "trainer": true,
        #     "commute": false,
        #     "manual": false,
        #     "private": false,
        #     "visibility": "followers_only",
        #     "flagged": false,
        #     "gear_id": null,
        #     "start_latlng": [],
        #     "end_latlng": [],
        #     "average_speed": 0.0,
        #     "max_speed": 0.0,
        #     "average_temp": 24,
        #     "has_heartrate": true,
        #     "average_heartrate": 77.0,
        #     "max_heartrate": 148.0,
        #     "heartrate_opt_out": false,
        #     "display_hide_heartrate_option": true,
        #     "elev_high": 0.0,
        #     "elev_low": 0.0,
        #     "upload_id": 11453524654,
        #     "upload_id_str": "11453524654",
        #     "external_id": "garmin_ping_319619866387",
        #     "from_accepted_tag": false,
        #     "pr_count": 0,
        #     "total_photo_count": 0,
        #     "has_kudoed": false
        # }
        activity_details = strava.get_activity_details(activity["id"])
        # `activity_details` is a dict like:
        # {
        #     "resource_state": 3,
        #     "athlete": {
        #         "id": 115890775,
        #         "resource_state": 1
        #     },
        #     "name": "Weight training: broken finger, abs, triceps, legs",
        #     "distance": 0.0,
        #     "moving_time": 7157,
        #     "elapsed_time": 7157,
        #     "total_elevation_gain": 0,
        #     "type": "WeightTraining",
        #     "sport_type": "WeightTraining",
        #     "id": 10709853894,
        #     "start_date": "2024-02-06T17:20:32Z",
        #     "start_date_local": "2024-02-06T18:20:32Z",
        #     "timezone": "(GMT+01:00) Africa/Algiers",
        #     "utc_offset": 3600.0,
        #     "location_city": null,
        #     "location_state": null,
        #     "location_country": "Italy",
        #     "achievement_count": 0,
        #     "kudos_count": 0,
        #     "comment_count": 0,
        #     "athlete_count": 1,
        #     "photo_count": 0,
        #     "map": {
        #         "id": "a10709853894",
        #         "polyline": "",
        #         "resource_state": 3,
        #         "summary_polyline": ""
        #     },
        #     "trainer": true,
        #     "commute": false,
        #     "manual": false,
        #     "private": false,
        #     "visibility": "followers_only",
        #     "flagged": false,
        #     "gear_id": null,
        #     "start_latlng": [],
        #     "end_latlng": [],
        #     "average_speed": 0.0,
        #     "max_speed": 0.0,
        #     "average_temp": 24,
        #     "has_heartrate": true,
        #     "average_heartrate": 77.0,
        #     "max_heartrate": 148.0,
        #     "heartrate_opt_out": false,
        #     "display_hide_heartrate_option": true,
        #     "elev_high": 0.0,
        #     "elev_low": 0.0,
        #     "upload_id": 11453524654,
        #     "upload_id_str": "11453524654",
        #     "external_id": "garmin_ping_319619866387",
        #     "from_accepted_tag": false,
        #     "pr_count": 0,
        #     "total_photo_count": 0,
        #     "has_kudoed": false,
        #     "description": "Finger rehab: 15 reps x 20 sets\nDecline crunch: bodyweight x 15 reps x 5 sets\nRussian twist: 40 reps x 5 sets\nV-hold: 30s reps x 5 sets\nResistance band tricep pull-down: red band (25kg) x 15 reps x 5 sets\nBulgarian split squat: bodyweight+16kg x 10 reps x 5 sets\nSplit soleus raise: bodyweight x 20 reps x 4 sets\n",
        #     "calories": 404.0,
        #     "perceived_exertion": null,
        #     "prefer_perceived_exertion": null,
        #     "segment_efforts": [],
        #     "laps": [
        #         {
        #             "id": 37068060147,
        #             "resource_state": 2,
        #             "name": "Lap 1",
        #             "activity": {
        #                 "id": 10709853894,
        #                 "visibility": "followers_only",
        #                 "resource_state": 1
        #             },
        #             "athlete": {
        #                 "id": 115890775,
        #                 "resource_state": 1
        #             },
        #             "elapsed_time": 7157,
        #             "moving_time": 7157,
        #             "start_date": "2024-02-06T17:20:32Z",
        #             "start_date_local": "2024-02-06T18:20:32Z",
        #             "distance": 0.0,
        #             "average_speed": 0.0,
        #             "max_speed": 0.0,
        #             "lap_index": 1,
        #             "split": 1,
        #             "start_index": 0,
        #             "end_index": 4321,
        #             "total_elevation_gain": 0,
        #             "device_watts": false,
        #             "average_heartrate": 77.0,
        #             "max_heartrate": 148.0
        #         }
        #     ],
        #     "photos": {
        #         "primary": null,
        #         "count": 0
        #     },
        #     "stats_visibility": [
        #         {
        #             "type": "heart_rate",
        #             "visibility": "everyone"
        #         },
        #         {
        #             "type": "pace",
        #             "visibility": "everyone"
        #         },
        #         {
        #             "type": "power",
        #             "visibility": "everyone"
        #         },
        #         {
        #             "type": "speed",
        #             "visibility": "everyone"
        #         },
        #         {
        #             "type": "calories",
        #             "visibility": "everyone"
        #         }
        #     ],
        #     "hide_from_home": false,
        #     "device_name": "Garmin Forerunner 965",
        #     "embed_token": "33f24624d0d69cfd987523970ae102065eb6b101",
        #     "private_note": "",
        #     "available_zones": []
        # }

        # print(activity["id"], activity_details["description"])

        data.append(
            [
                activity.get("start_date_local") or activity.get("start_date"),
                activity["type"],
                activity["name"],
                activity["moving_time"],
                activity["distance"],
                activity["total_elevation_gain"],
                activity_details["description"],
            ]
        )

    with open(CURR_DIR / "activities.csv", "a") as fout:
        fout.write(
            "date\t"
            + "type\t"
            + "name\t"
            + "moving_time_hours\t"
            + "distance_km\t"
            + "elevation_m\t"
            + "descr\n"
        )
        for datum in data:
            moving_time_hours = round(datum[3] / 3600, 2)
            distance = round(datum[4] / 1000, 1)

            fout.write(
                f"`{datum[0]}`\t"
                + f"`{datum[1]}`\t"
                + f"`{datum[2]}`\t"
                + f"`{moving_time_hours}H`\t"
                + f"`{distance}km`\t"
                + f"`{datum[5]}m`\t"
                + f"`{datum[6]}`\n"
            )


if __name__ == "__main__":
    main()
