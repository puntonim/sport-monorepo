import json

from aws_utils.aws_testfactories.api_gateway_event_to_lambda_factory import (
    ApiGatewayV2EventToLambdaFactory,
)
from aws_utils.aws_testfactories.lambda_context_factory import LambdaContextFactory

from strava_facade_api.views.create_activity_view import lambda_handler


class TestEndpointCreateActivity:
    def setup_method(self):
        self.context = LambdaContextFactory().make()

    def test_happy_flow(self):
        data = dict(
            name="Name from pytest",
            activityType="WeightTraining",
            startDate="2025-10-09T08:00:00+02:00",
            durationSeconds=3660,
            description="Descr from pytest",
        )
        response = lambda_handler(
            ApiGatewayV2EventToLambdaFactory.make_for_post_request(
                path="/create-activity",
                body_dict=data,
            ),
            self.context,
        )
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["name"] == data["name"]
        assert body["description"] == data["description"]
