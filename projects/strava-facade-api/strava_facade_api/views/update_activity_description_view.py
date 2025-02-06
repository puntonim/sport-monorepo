import base64
import binascii
import json
from typing import Any

from .. import domain, domain_exceptions
from .http_response import BadRequest400Response, NotFound404Response, Ok200Response

# Objects declared outside of the Lambda's handler method are part of Lambda's
# *execution environment*. This execution environment is sometimes reused for subsequent
# function invocations. Note that you can not assume that this always happens.
# Typical use case: database connection. The same connection can be re-used in some
# subsequent function invocations. It is recommended though to add logic to check if a
# connection already exists before creating a new one.
# The execution environment also provides 512 MB of *disk space* in the /tmp directory.
# Again, this can be re-used in some subsequent function invocations.
# See: https://docs.aws.amazon.com/lambda/latest/dg/runtimes-context.html#runtimes-lifecycle-shutdown

# The Lambda is configured with 0 retries. So do raise exceptions in the view.


print("UPDATE ACTIVITY DESCRIPTION: LOAD")


def lambda_handler(event: dict[str, Any], context) -> dict:
    """
    Update the description of an existing Strava activity.
    It finds the activity by afterTs and beforeTs timestamps and by activityType.

    Args:
        event: an AWS event, eg. SNS Message.
        context: the context passed to the Lambda.

    Example:
        $ curl -X POST https://s8afs561v2.execute-api.eu-south-1.amazonaws.com/update-activity-description \
         -H 'Authorization: XXX' \
         -d '{"afterTs": 1707174000, "beforeTs": 1707260399, "description": "My new descr", "activityType": "WeightTraining", "name": "test1", "doStopIfDescriptionNotNull": "false"}'

        {
          "resource_state": 3,
          "athlete": {
            "id": 115890775,
            "resource_state": 1
          },
          "name": "test1",
          "distance": 0.0,
          "moving_time": 7157,
          "elapsed_time": 7157,
          "total_elevation_gain": 0,
          "type": "WeightTraining",
          "sport_type": "WeightTraining",
          "id": 10709853894,
          "start_date": "2024-02-06T17:20:32Z",
          "start_date_local": "2024-02-06T18:20:32Z",
          "timezone": "(GMT+01:00) Africa/Algiers",
          "utc_offset": 3600.0,
          "location_city": null,
          "location_state": null,
          "location_country": "Italy",
          "achievement_count": 0,
          "kudos_count": 0,
          "comment_count": 0,
          "athlete_count": 1,
          "photo_count": 0,
          "map": {
            "id": "a10709853894",
            "polyline": "",
            "resource_state": 3,
            "summary_polyline": ""
          },
          "trainer": true,
          "commute": false,
          "manual": false,
          "private": false,
          "visibility": "followers_only",
          "flagged": false,
          "gear_id": null,
          "start_latlng": [],
          "end_latlng": [],
          "average_speed": 0.0,
          "max_speed": 0.0,
          "average_temp": 24,
          "has_heartrate": true,
          "average_heartrate": 77.0,
          "max_heartrate": 148.0,
          "heartrate_opt_out": false,
          "display_hide_heartrate_option": true,
          "elev_high": 0.0,
          "elev_low": 0.0,
          "upload_id": 11453524654,
          "upload_id_str": "11453524654",
          "external_id": "garmin_ping_319619866387",
          "from_accepted_tag": false,
          "pr_count": 0,
          "total_photo_count": 0,
          "has_kudoed": false,
          "description": "My new descr",
          "calories": 404.0,
          "perceived_exertion": null,
          "prefer_perceived_exertion": null,
          "segment_efforts": [],
          "laps": [
            {
              "id": 37068060147,
              "resource_state": 2,
              "name": "Lap 1",
              "activity": {
                "id": 10709853894,
                "visibility": "followers_only",
                "resource_state": 1
              },
              "athlete": {
                "id": 115890775,
                "resource_state": 1
              },
              "elapsed_time": 7157,
              "moving_time": 7157,
              "start_date": "2024-02-06T17:20:32Z",
              "start_date_local": "2024-02-06T18:20:32Z",
              "distance": 0.0,
              "average_speed": 0.0,
              "max_speed": 0.0,
              "lap_index": 1,
              "split": 1,
              "start_index": 0,
              "end_index": 4321,
              "total_elevation_gain": 0,
              "device_watts": false,
              "average_heartrate": 77.0,
              "max_heartrate": 148.0
            }
          ],
          "photos": {
            "primary": null,
            "count": 0
          },
          "stats_visibility": [
            {
              "type": "heart_rate",
              "visibility": "everyone"
            },
            {
              "type": "pace",
              "visibility": "everyone"
            },
            {
              "type": "power",
              "visibility": "everyone"
            },
            {
              "type": "speed",
              "visibility": "everyone"
            },
            {
              "type": "calories",
              "visibility": "everyone"
            }
          ],
          "hide_from_home": false,
          "device_name": "Garmin Forerunner 965",
          "embed_token": "33f24624d0d69cfd987523970ae102065eb6b101",
          "private_note": "",
          "available_zones": []
        }
    """
    print("UPDATE ACTIVITY DESCRIPTION: START")

    body = event.get("body", "")
    if event.get("isBase64Encoded"):
        try:
            body = base64.b64decode(body).decode()
        except (UnicodeDecodeError, binascii.Error) as exc:
            print(f"Posted invalid body: {exc}")
            return BadRequest400Response("Invalid body").to_dict()
    body = json.loads(body)

    if not isinstance(body, dict):
        return BadRequest400Response("Posted body must be a JSON object").to_dict()

    after_ts = body.get("afterTs")
    if not after_ts:
        return BadRequest400Response(
            "Posted body must include the key 'afterTs'"
        ).to_dict()

    before_ts = body.get("beforeTs")
    if not before_ts:
        return BadRequest400Response(
            "Posted body must include the key 'beforeTs'"
        ).to_dict()

    activity_type = body.get("activityType")
    if not activity_type:
        return BadRequest400Response(
            "Posted body must include the key 'activityType'"
        ).to_dict()

    description = body.get("description")
    if not description:
        return BadRequest400Response(
            "Posted body must include the key 'description'"
        ).to_dict()

    name = body.get("name")

    do_stop_if_description_not_null = body.get("doStopIfDescriptionNotNull", True)
    if (
        do_stop_if_description_not_null is not True
        and do_stop_if_description_not_null.lower() in ("false", "f", "no", "n")
    ):
        do_stop_if_description_not_null = False

    try:
        updated_activity = domain.update_activity_description(
            after_ts=after_ts,
            before_ts=before_ts,
            activity_type=activity_type,
            description=description,
            name=name,
            do_stop_if_description_not_null=do_stop_if_description_not_null,
        )
    except domain_exceptions.NoActivityFound as exc:
        return NotFound404Response(
            "No activity found in the given time range"
        ).to_dict()
    except domain_exceptions.ActivityAlreadyHasDescription as exc:
        return BadRequest400Response(
            f"The activity found already has a description: id={exc.activity_id} description={exc.description}"
        ).to_dict()
    except domain_exceptions.StravaAuthenticationError as exc:
        return BadRequest400Response(str(exc)).to_dict()
    except domain_exceptions.StravaApiError as exc:
        return BadRequest400Response(str(exc)).to_dict()
    except domain_exceptions.StravaApiRateLimitExceededError as exc:
        return BadRequest400Response(str(exc.__cause__)).to_dict()

    return Ok200Response(updated_activity).to_dict()
