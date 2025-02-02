import os
from datetime import datetime
from typing import Any, Dict

# Objects declared outside of the Lambda's handler method are part of Lambda's
# *execution environment*. This execution environment is sometimes reused for subsequent
# function invocations. Note that you can not assume that this always happens.
# Typical use case: database connection. The same connection can be re-used in some
# subsequent function invocations. It is recommended though to add logic to check if a
# connection already exists before creating a new one.
# The execution environment also provides 512 MB of *disk space* in the /tmp directory.
# Again, this can be re-used in some subsequent function invocations.
# See: https://docs.aws.amazon.com/lambda/latest/dg/runtimes-context.html#runtimes-lifecycle-shutdown


print("AUTHORIZER: LOADING")


def lambda_handler(event: Dict[str, Any], context) -> dict:
    """
    Authorizer for Lambda function.
    Docs:
     - https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-lambda-authorizer.html
     - https://www.serverless.com/framework/docs/providers/aws/events/http-api#lambda-request-authorizers

    Args:
        event: an AWS event, eg. SNS Message.
        context: the context passed to the Lambda.

    The `event` is a dict (that can be casted to `APIGatewayProxyEventV2`) like:
        {
            "version": "2.0",
            "type": "REQUEST",
            "routeArn": "arn:aws:execute-api:us-east-1:289485838881:om3jkmajs9/$default/GET/dataset-summary",
            "identitySource": [
                "XXX"
            ],
            "routeKey": "GET /dataset-summary",
            "rawPath": "/dataset-summary",
            "rawQueryString": "",
            "headers": {
                "accept": "*/*",
                "authorization": "XXX",
                "content-length": "0",
                "host": "om3jkmajs9.execute-api.us-east-1.amazonaws.com",
                "user-agent": "curl/7.64.1",
                "x-amzn-trace-id": "Root=1-62ad9d15-0c106d3261435bb12149082c",
                "x-forwarded-for": "151.55.223.93",
                "x-forwarded-port": "443",
                "x-forwarded-proto": "https"
            },
            "requestContext": {
                "accountId": "289485838881",
                "apiId": "om3jkmajs9",
                "domainName": "om3jkmajs9.execute-api.us-east-1.amazonaws.com",
                "domainPrefix": "om3jkmajs9",
                "http": {
                    "method": "GET",
                    "path": "/dataset-summary",
                    "protocol": "HTTP/1.1",
                    "sourceIp": "151.55.223.93",
                    "userAgent": "curl/7.64.1"
                },
                "requestId": "T6V7Uh_vIAMEMPA=",
                "routeKey": "GET /dataset-summary",
                "stage": "$default",
                "time": "18/Jun/2022:09:38:29 +0000",
                "timeEpoch": 1655545109036
            }
        }

    The `context` is a `LambdaContext` instance with properties similar to:
        {
            'aws_request_id': '75e62f43-062b-4b16-b877-e4662ea0ed32',
            'log_group_name': '/aws/lambda/lambda-s3',
            'log_stream_name': '2020/11/19/[$LATEST]071cab333b4c4a5b94ab0ae0a10c4b7c',
            'function_name': 'lambda-s3',
            'memory_limit_in_mb': '128',
            'function_version': '$LATEST',
            'invoked_function_arn': 'arn:aws:lambda:ap-southeast-1:477353422995:function:lambda-s3',
            'client_context': None,
            'identity': "<__main__.CognitoIdentity object at 0x7f8cbb404280>",
            '_epoch_deadline_time_in_ms': 1605769759863,
        }
    More info here: https://docs.aws.amazon.com/lambda/latest/dg/python-context.html
    """
    print("AUTHORIZER: START")

    is_authorized = event["headers"].get("authorization") == os.getenv(
        "API_AUTHORIZER_TOKEN"
    )

    context = dict(ts=datetime.now().astimezone().isoformat())
    response = {"isAuthorized": is_authorized, "context": context}
    return response
