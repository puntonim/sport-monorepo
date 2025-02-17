from datetime import datetime
from typing import Any

from .. import domain, domain_exceptions
from .http_response import BadRequest400Response, Ok200Response

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


print("LIST ACTIVITIES: LOAD")


def lambda_handler(event: dict[str, Any], context) -> dict:
    """
    List Strava activities by afterTs and beforeTs timestamps and by activityType.

    Args:
        event: a dict representing a Lambda Url HTTP request.
        context: the context passed to the Lambda.

    The `event` is a dict representing a Lambda Url HTTP request, like:
    {
        "version": "2.0",
        "routeKey": "GET /activity",
        "rawPath": "/activity",
        "rawQueryString": "after-ts=1739374800&before-ts=1739376800&activity-type=WeightTraining&n-results-per-page=10&page-n=1",
        "headers": {
            "accept": "*/*",
            "authorization": "XXX",
            "content-length": "0",
            "host": "ejxyxviele.execute-api.eu-south-1.amazonaws.com",
            "user-agent": "curl/8.1.2",
            "x-amzn-trace-id": "Root=1-67adf0d8-1167c9602b1193ad4f7d7621",
            "x-forwarded-for": "151.55.110.36",
            "x-forwarded-port": "443",
            "x-forwarded-proto": "https",
        },
        "queryStringParameters": {
            "activity-type": "WeightTraining",
            "after-ts": "1739374800",
            "before-ts": "1739376800",
            "n-results-per-page": "10",
            "page-n": "1",
        },
        "requestContext": {
            "accountId": "477353422995",
            "apiId": "ejxyxviele",
            "authorizer": {"lambda": {"ts": "2025-02-13T12:34:57.185893+00:00"}},
            "domainName": "ejxyxviele.execute-api.eu-south-1.amazonaws.com",
            "domainPrefix": "ejxyxviele",
            "http": {
                "method": "GET",
                "path": "/activity",
                "protocol": "HTTP/1.1",
                "sourceIp": "151.55.110.36",
                "userAgent": "curl/8.1.2",
            },
            "requestId": "F7KR2j-3su8EP4g=",
            "routeKey": "GET /activity",
            "stage": "$default",
            "time": "13/Feb/2025:13:17:12 +0000",
            "timeEpoch": 1739452632226,
        },
        "isBase64Encoded": False,
    }

    Example:
        & curl https://ejxyxviele.execute-api.eu-south-1.amazonaws.com/activity?after-ts=1739374800&before-ts=1739376800&activity-type=WeightTraining&n-results-per-page=10&page-n=1 \
         -H 'Authorization: XXX' | jq

        [
          {
            "resource_state": 2,
            "athlete": {
              "id": 115890775,
              "resource_state": 1
            },
            "name": "Weight training: legs isometrics, left elbow isometrics",
            "distance": 0.0,
            "moving_time": 3027,
            "elapsed_time": 3027,
            "total_elevation_gain": 0,
            "type": "WeightTraining",
            "sport_type": "WeightTraining",
            "id": 13609478847,
            "start_date": "2025-02-12T15:43:30Z",
            "start_date_local": "2025-02-12T16:43:30Z",
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
              "id": "a13609478847",
              "summary_polyline": "",
              "resource_state": 2
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
            "average_temp": 25,
            "has_heartrate": true,
            "average_heartrate": 69.9,
            "max_heartrate": 98.0,
            "heartrate_opt_out": false,
            "display_hide_heartrate_option": true,
            "elev_high": 0.0,
            "elev_low": 0.0,
            "upload_id": 14520986383,
            "upload_id_str": "14520986383",
            "external_id": "garmin_ping_410474177234",
            "from_accepted_tag": false,
            "pr_count": 0,
            "total_photo_count": 0,
            "has_kudoed": false
          }
        ]
    """
    print("LIST ACTIVITIES: START")

    # Parse the query string.
    qs = event.get("queryStringParameters", {})
    before_ts = qs.get("before-ts")  # Eg.: "1739374800".
    after_ts = qs.get("after-ts")  # Eg.: "1739374800".
    activity_type = qs.get("activity-type")  # Eg.: "WeightTraining".
    n_results_per_page = qs.get("n-results-per-page")  # Eg.: 100.
    page_n = qs.get("page-n")  # Eg.: 2.

    # Validate query string.
    try:
        datetime.fromtimestamp(int(before_ts))
    except (ValueError, OverflowError) as exc:
        return BadRequest400Response(
            "before-ts is an invalid timestamp, eg: 1739374800"
        ).to_dict()
    try:
        datetime.fromtimestamp(int(after_ts))
    except (ValueError, OverflowError) as exc:
        return BadRequest400Response(
            "after-ts is an invalid timestamp, eg: 1739374800"
        ).to_dict()
    try:
        n_results_per_page = int(n_results_per_page)
    except ValueError as exc:
        return BadRequest400Response("n_results_per_page is not an int").to_dict()
    try:
        page_n = int(page_n)
    except ValueError as exc:
        return BadRequest400Response("page_n is not an int").to_dict()

    try:
        activities = domain.list_activities(
            after_ts=after_ts,
            before_ts=before_ts,
            activity_type=activity_type,
            n_results_per_page=n_results_per_page,
            page_n=page_n,
        )
    except domain_exceptions.RequestedResultsPageDoesNotExistInStravaApi as exc:
        return BadRequest400Response(
            f"The requested page-n does not exist: page-n={exc.page_n}"
        ).to_dict()
    except domain_exceptions.AfterTsInTheFutureInStravaApi as exc:
        return BadRequest400Response(
            f"The requested after-ts is in the future: after-ts={exc.after_ts}"
        ).to_dict()
    except domain_exceptions.StravaAuthenticationError as exc:
        return BadRequest400Response(str(exc)).to_dict()
    except domain_exceptions.StravaApiError as exc:
        return BadRequest400Response(str(exc)).to_dict()
    except domain_exceptions.StravaApiRateLimitExceededError as exc:
        return BadRequest400Response(str(exc.__cause__)).to_dict()

    return Ok200Response(activities).to_dict()
