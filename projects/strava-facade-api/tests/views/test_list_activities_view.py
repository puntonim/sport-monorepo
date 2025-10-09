import json

from aws_utils.aws_testfactories.api_gateway_event_to_lambda_factory import (
    ApiGatewayV2EventToLambdaFactory,
)
from aws_utils.aws_testfactories.lambda_context_factory import LambdaContextFactory

from strava_facade_api.views.list_activities_view import lambda_handler


class TestEndpointListActivitiesView:
    def setup_method(self):
        self.context = LambdaContextFactory().make()

    def test_happy_flow(self):
        after_ts = 1759424400
        response = lambda_handler(
            ApiGatewayV2EventToLambdaFactory.make_for_get_request(
                path="/activity",
                raw_query_string=f"after-ts={after_ts}&n-results-per-page=1",
            ),
            self.context,
        )
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body[0]["id"] == 16013371380
        assert body[0]["name"] == "Weight training: powerlifting"

    def test_no_activity(self):
        after_ts = 1759424400
        response = lambda_handler(
            ApiGatewayV2EventToLambdaFactory.make_for_get_request(
                path="/activity",
                raw_query_string=f"after-ts={after_ts}&activity-type=XXX",
            ),
            self.context,
        )
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body == []
