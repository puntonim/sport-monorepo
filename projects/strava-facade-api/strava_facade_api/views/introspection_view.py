from datetime import datetime
from typing import Any

from ..__version__ import __version__
from .http_response import NotFound404Response, Ok200Response

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


print("INTROSPECTION: LOADING")


def lambda_handler(event: dict[str, Any], context) -> dict:
    print("INTROSPECTION: START")

    if event["requestContext"]["http"]["method"].upper() != "GET":
        return NotFound404Response().to_dict()

    if event["rawPath"].endswith("/version"):
        return Ok200Response(__version__).to_dict()

    if event["rawPath"].endswith("/health"):
        now = datetime.now().astimezone().isoformat()
        print("Health")
        return Ok200Response(now).to_dict()

    if event["rawPath"].endswith("/unhealth"):
        now = datetime.now().astimezone().isoformat()
        print("Unhealth")
        raise UnhealthCommandException(ts=now)

    return NotFound404Response().to_dict()


class UnhealthCommandException(Exception):
    def __init__(self, ts: str):
        self.ts = ts
