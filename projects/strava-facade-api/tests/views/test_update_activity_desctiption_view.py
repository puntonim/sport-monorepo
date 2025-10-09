import json

from aws_utils.aws_testfactories.api_gateway_event_to_lambda_factory import (
    ApiGatewayV2EventToLambdaFactory,
)
from aws_utils.aws_testfactories.lambda_context_factory import LambdaContextFactory

from strava_facade_api.views.update_activity_description_view import lambda_handler


class TestEndpointUpdateActivityDescription:
    def setup_method(self):
        self.context = LambdaContextFactory().make()

    def test_happy_flow(self):
        new_desc = "New desc rom Pytest"
        new_name = "New name from pytest"
        body = dict(
            activityId=16013371380,
            description=new_desc,
            name=new_name,
            doStopIfDescriptionNotNull="false",
        )
        response = lambda_handler(
            ApiGatewayV2EventToLambdaFactory.make_for_post_request(
                path="/update-activity-description",
                body_dict=body,
            ),
            self.context,
        )
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["id"] == 16013371380
        assert body["name"] == new_name
        assert body["description"] == new_desc
