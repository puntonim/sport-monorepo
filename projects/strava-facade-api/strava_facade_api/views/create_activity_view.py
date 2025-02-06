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


print("CREATE ACTIVITY: LOAD")


def lambda_handler(event: dict[str, Any], context) -> dict:
    """
    Create a new Strava activity.
    It also tries to make sure that this new activity is not a duplicate.

    Args:
        event: an AWS event, eg. SNS Message.
        context: the context passed to the Lambda.

    Example:
        $ curl -X POST https://q0adsu470c.execute-api.eu-south-1.amazonaws.com/create-activity \
         -H 'Authorization: XXX' \
         -d '{"name": "test1", "activityType": "WeightTraining", "startDate": "2024-07-25T18:17:33.983+02:00", "durationSeconds": 3960, "description": "My new descr"}'

        {
          "resource_state": 3,
          "athlete": {
            "id": 115890775,
            "resource_state": 1
          },
          "name": "test14",
          "distance": 0.0,
          "moving_time": 3960,
          "elapsed_time": 3960,
          "total_elevation_gain": 0,
          "type": "WeightTraining",
          "sport_type": "WeightTraining",
          "id": 11978303355,
          "start_date": "2024-07-25T16:19:33Z",
          "start_date_local": "2024-07-25T18:19:33Z",
          "timezone": "(GMT+01:00) Europe/Rome",
          "utc_offset": 7200.0,
          "location_city": null,
          "location_state": null,
          "location_country": "Italy",
          "achievement_count": 0,
          "kudos_count": 0,
          "comment_count": 0,
          "athlete_count": 1,
          "photo_count": 0,
          "map": {
            "id": "a11978303355",
            "polyline": "",
            "resource_state": 3,
            "summary_polyline": ""
          },
          "trainer": false,
          "commute": false,
          "manual": true,
          "private": false,
          "visibility": "followers_only",
          "flagged": false,
          "gear_id": null,
          "start_latlng": [],
          "end_latlng": [],
          "average_speed": 0.0,
          "max_speed": 0,
          "has_heartrate": false,
          "heartrate_opt_out": false,
          "display_hide_heartrate_option": false,
          "upload_id": null,
          "external_id": null,
          "from_accepted_tag": false,
          "pr_count": 0,
          "total_photo_count": 0,
          "has_kudoed": false,
          "description": "My new descrdfdsf",
          "calories": 0,
          "perceived_exertion": null,
          "prefer_perceived_exertion": null,
          "segment_efforts": [],
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
          "embed_token": "fe1f44666a44609d8aa96551037f874cba5e3342",
          "available_zones": []
        }
    """
    print("CREATE ACTIVITY: START")

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

    name = body.get("name")
    if not name:
        return BadRequest400Response(
            "Posted body must include the key 'name'"
        ).to_dict()

    activity_type = body.get("activityType")
    if not activity_type:
        return BadRequest400Response(
            "Posted body must include the key 'activityType'"
        ).to_dict()

    start_date = body.get("startDate")
    if not start_date:
        return BadRequest400Response(
            "Posted body must include the key 'startDate'"
        ).to_dict()

    duration_seconds = body.get("durationSeconds")
    if not duration_seconds:
        return BadRequest400Response(
            "Posted body must include the key 'durationSeconds'"
        ).to_dict()

    description = body.get("description")
    if not description:
        return BadRequest400Response(
            "Posted body must include the key 'description'"
        ).to_dict()

    try:
        new_activity = domain.create_activity(
            name=name,
            activity_type=activity_type,
            start_date=start_date,
            duration_seconds=duration_seconds,
            description=description,
        )
    except domain_exceptions.InvalidDatetimeInput as exc:
        return BadRequest400Response(f"Invalid startDate: {exc.value}").to_dict()
    except domain_exceptions.NaiveDatetimeInput as exc:
        return BadRequest400Response(f"Naive startDate: {exc.value}").to_dict()
    except domain_exceptions.PossibleDuplicatedActivityFound as exc:
        return BadRequest400Response(
            f"Found a possible duplicate activity: {exc.activity_id}"
        ).to_dict()
    except domain_exceptions.StravaAuthenticationError as exc:
        return BadRequest400Response(str(exc)).to_dict()
    except domain_exceptions.StravaApiError as exc:
        return BadRequest400Response(str(exc)).to_dict()
    except domain_exceptions.StravaApiRateLimitExceededError as exc:
        return BadRequest400Response(str(exc.__cause__)).to_dict()

    return Ok200Response(new_activity).to_dict()
