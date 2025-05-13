import json
import os
import re
from typing import Iterator

import pytest
from _pytest.fixtures import SubRequest
from _pytest.unittest import TestCaseFunction
from vcr.cassette import Cassette
from vcr.errors import CannotOverwriteExistingCassetteException

from sport_analysis.conf.settings_module import settings, test_settings

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


@pytest.fixture(autouse=True, scope="function")
def test_settings_fixture(monkeypatch, request):
    # Copy all test settings to settings.
    attr_names = [
        attr
        for attr in dir(test_settings)
        if not callable(getattr(test_settings, attr)) and not attr.startswith("__")
    ]
    for attr_name in attr_names:
        attr_value = getattr(test_settings, attr_name)
        setattr(settings, attr_name, attr_value)


def is_vcr_episode_or_error():
    global IS_VCR_EPISODE_OR_ERROR
    if "IS_VCR_EPISODE_OR_ERROR" in os.environ:
        IS_VCR_EPISODE_OR_ERROR = os.getenv(
            "IS_VCR_EPISODE_OR_ERROR", ""
        ).lower().strip() in ("true", "yes")
    return IS_VCR_EPISODE_OR_ERROR


def is_vcr_record_mode() -> bool:
    if not is_vcr_enabled():
        return False
    return not is_vcr_episode_or_error()


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
    # Do not record requests to the token endpoints.
    if (
        "strava.com/oauth/token" in request.uri
        or "sso.garmin.com" in request.uri
        or "oauth" in request.uri
        or "thegarth" in request.uri
    ):
        return None
    # Do not record requests to AWS Parameter Store.
    elif re.search(r"ssm\.[a-zA-Z0-9-]+\.amazonaws.com", request.uri):
        return None
    return request


def before_record_response(response):
    """
    Redact the access token.
    """
    try:
        data = json.loads(response["body"]["string"].decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    else:
        if "access_token" in data:
            data["access_token"] = "**REDACTED**"

        if isinstance(data, dict):
            if data.get("parametri", {}).get("sessione", {}).get("codice_sessione"):
                data["parametri"]["sessione"]["codice_sessione"] = "**REDACTED**"
            if data.get("parametri", {}).get("sessione", {}).get("idCliente"):
                data["parametri"]["sessione"]["idCliente"] = "**REDACTED**"
            if data.get("parametri", {}).get("sessione", {}).get("nomeCliente"):
                data["parametri"]["sessione"]["nomeCliente"] = "**REDACTED**"
            if data.get("parametri", {}).get("sessione", {}).get("cognomeCliente"):
                data["parametri"]["sessione"]["cognomeCliente"] = "**REDACTED**"
            if data.get("parametri", {}).get("sessione", {}).get("mail"):
                data["parametri"]["sessione"]["mail"] = "**REDACTED**"
            if data.get("parametri", {}).get("sessione", {}).get("pass"):
                data["parametri"]["sessione"]["pass"] = "**REDACTED**"

        response["body"]["string"] = json.dumps(data).encode()

    response_headers_to_delete = (
        "Set-Cookie",
        "CF-RAY",
        "NEL",
        "Report-To",
        "alt-svc",
        "cf-cache-status",
    )
    for key in response_headers_to_delete:
        try:
            del response["headers"][key]
            del response["headers"][key.lower()]
            del response["headers"][key.title()]
            del response["headers"][key.upper()]
        except KeyError:
            pass
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
            "Cookie",
            "referer",
        ),
        "filter_post_data_parameters": (
            ("mail", "**REDACTED**"),
            ("pass", "**REDACTED**"),
            ("codice_sessione", "**REDACTED**"),
        ),
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
