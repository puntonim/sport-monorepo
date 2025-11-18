import json
import os
from typing import Iterator

import pytest
from _pytest.fixtures import SubRequest
from _pytest.unittest import TestCaseFunction
from aws_parameter_store_client import aws_parameter_store_client
from vcr.cassette import Cassette
from vcr.errors import CannotOverwriteExistingCassetteException

IS_VCR_EPISODE_OR_ERROR = True  # False to record new cassettes.
IS_VCR_ENABLED = True


def pytest_collection_modifyitems(items: list[TestCaseFunction]):
    """
    Enable vcr for all tests.
    By marking all tests with `vcr`.
    Unless the test function/class/module is marked with:
        `@pytest.mark.novcr` for functions and classes
        `pytestmark = pytest.mark.novcr` for modules.
    """
    for item in items:
        # Slow tests (@pytest.mark.slow) skipped by default. To run the slow tests:
        # $ pytest -m slow tests/
        if "slow" in item.keywords and (
            not item.config.getoption("-m") or item.config.getoption("-m") != "slow"
        ):
            item.add_marker("skip")
        if "novcr" in item.keywords:
            continue
        item.add_marker("vcr")


def pytest_configure(config):
    config.addinivalue_line("markers", "withlogs: enable logs")
    config.addinivalue_line("markers", "novcr: disable vcr")
    config.addinivalue_line("markers", "slow: slow test")


# @pytest.fixture(autouse=True, scope="function")
# def test_settings_fixture(monkeypatch, request):
#     # Copy all test settings to settings.
#     attr_names = [
#         attr
#         for attr in dir(test_settings)
#         if not callable(getattr(test_settings, attr)) and not attr.startswith("__")
#     ]
#     for attr_name in attr_names:
#         attr_value = getattr(test_settings, attr_name)
#         setattr(settings, attr_name, attr_value)


# @pytest.fixture(autouse=True, scope="function")
# def logging_mock(request):
#     """
#     Logging is disabled in tests.
#     In order to enable logging, mark the test function/class/module with:
#         `@pytest.mark.withlogs` for functions and classes
#         `pytestmark = pytest.mark.withlogs` for modules.
#     Then use the fixture `caplog`.
#     """
#     if "withlogs" not in request.keywords:
#         from villa_savi_backend.utils.log_utils import logger
#
#         logger.logger_handler.level = 100
#         yield
#         return
#     yield


def is_vcr_episode_or_error():
    global IS_VCR_EPISODE_OR_ERROR
    if "IS_VCR_EPISODE_OR_ERROR" in os.environ:
        IS_VCR_EPISODE_OR_ERROR = os.getenv(
            "IS_VCR_EPISODE_OR_ERROR", ""
        ).lower().strip() in ("true", "yes")
    return IS_VCR_EPISODE_OR_ERROR


def get_record_mode() -> str:
    return "none" if is_vcr_episode_or_error() else "new_episodes"


def is_vcr_enabled() -> bool:
    global IS_VCR_ENABLED
    if "IS_VCR_ENABLED" in os.environ:
        IS_VCR_ENABLED = os.getenv("IS_VCR_ENABLED", "").lower().strip() in (
            "true",
            "yes",
        )
    return IS_VCR_ENABLED


def get_match_on() -> tuple:
    """
    The default behavior for request matching is:
      ['method', 'scheme', 'host', 'port', 'path', 'query'].
    We also want to match on body.
    """
    return ("method", "scheme", "host", "port", "path", "query", "body")


def before_record_request(request):
    """
    Redact sensitive information.
    """
    # Do not record requests to Strava token endpoint.
    if "strava.com/oauth/token" in request.uri:
        return None

    # for i in range(len(request.query)):
    #     if "api.telegram.org/bot" in request.uri:
    #         request.uri = re.sub(
    #             r"api.telegram.org/bot([^/]+)",
    #             "api.telegram.org/bot**REDACTED**",
    #             request.uri,
    #         )
    return request


def before_record_response(response):
    """
    Redact any access token.
    """
    try:
        data = json.loads(response["body"]["string"].decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return response

    def _redact(_data):
        # Redact a generic OAuth access token.
        if "access_token" in _data:
            _data["access_token"] = "**REDACTED**"
        if "refresh_token" in _data:
            _data["refresh_token"] = "**REDACTED**"
        if "expires_at" in _data:
            _data["expires_at"] = 4095215440
        if "expires_in" in _data:
            _data["expires_in"] = 21600

    _redact(data)

    # Strava token (stored in WS Parameter Store).
    strava_token_in_aws_param_store: dict | None = None
    try:
        strava_token_in_aws_param_store = json.loads(
            data.get("Parameter", {}).get("Value", {})
        )
    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError, TypeError):
        pass
    if strava_token_in_aws_param_store:
        _redact(strava_token_in_aws_param_store)
        data["Parameter"]["Value"] = json.dumps(strava_token_in_aws_param_store)

    response["body"]["string"] = json.dumps(data).encode()
    return response


@pytest.fixture(scope="session")
def vcr_config():
    """
    Configure VCR.

    - Set the record mode.
    - Ignore some headers and hosts.
    - The default behavior for request matching is:
      ['method', 'scheme', 'host', 'port', 'path', 'query'].
      We also want to match on body.
    """

    if not is_vcr_enabled():
        # Disable VCR.
        return {"before_record": lambda *args, **kwargs: None}

    return {
        "decode_compressed_response": True,
        "filter_headers": (
            "Authorization",
            "User-Agent",
            "X-Amz-Security-Token",
            "X-Amz-Content-SHA256",
            "X-Amz-Date",
            "X-Amz-Target",
            "amz-sdk-invocation-id",
            "amz-sdk-request",
        ),
        # "filter_post_data_parameters": (
        #     ("client_id", "**REDACTED**"),
        #     ("client_secret", "**REDACTED**"),
        # ),
        "ignore_hosts": ("localhost",),
        "record_mode": get_record_mode(),
        "match_on": get_match_on(),
        "before_record_request": before_record_request,
        "before_record_response": before_record_response,
    }


@pytest.fixture(autouse=True, scope="function")
def assert_all_played(request: SubRequest, vcr: Cassette) -> Iterator:
    """
    Ensure that all episodes have been played in the current test.
    Only if the current test has a cassette.
    """
    yield
    if is_vcr_enabled() and is_vcr_episode_or_error() and vcr:
        assert vcr.all_played


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call():
    """
    Enrich `CannotOverwriteExistingCassetteException` original exception with some
    useful info.
    """
    try:
        outcome = yield
        outcome.get_result()
    except Exception as exc:
        if isinstance(exc, CannotOverwriteExistingCassetteException) or isinstance(
            getattr(exc, "kwargs", dict()).get("error"),
            CannotOverwriteExistingCassetteException,
        ):
            args = list(exc.args)
            args[0] += "\nUse IS_VCR_EPISODE_OR_ERROR=no to record a new episode."
            exc.args = tuple(args)
        raise


@pytest.fixture(autouse=True, scope="function")
def clear_cache_for_aws_param_store_client():
    """
    Clear the Python in-memory cache (for time) used by AWS Param Store client.
    Which is used in settings.py by `settings_utils.get_string_from_env_or_aws_parameter_store()`.
    Without clearing the cache the HTTP interactions are not deterministic and vcr.py
     raises exceptions for episodes not recorded or not played.
    """
    aws_parameter_store_client.cache.clear_cache()


@pytest.fixture(scope="session")
def monkeysession(request):
    from _pytest.monkeypatch import MonkeyPatch

    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


# @pytest.fixture(autouse=True, scope="function")
# def mock_aws_credentials(monkeypatch, request):
#     """
#     Boto3 requires existing credentials.
#     """
#     if "nomoto" not in request.keywords:
#         # See: http://docs.getmoto.org/en/latest/docs/getting_started.html#example-on-usage
#         monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
#         monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
#         monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
#         monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
#         monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-south-1")
