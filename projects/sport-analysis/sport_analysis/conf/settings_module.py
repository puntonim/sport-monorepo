"""
A very basic settings manager. I chose this because this app requires only a few
 settings and no special features.

A better alternative, in case the app requires more settings and advanced features,
 is Dynaconf.
"""

import os
from contextlib import ContextDecorator
from pathlib import Path
from typing import Optional

import log_utils as logger

rich_log = logger.RichAdapter()
rich_log.configure_default()
logger.set_adapter(rich_log)

CURR_DIR = Path(__file__).parent
ROOT_DIR = CURR_DIR.parent.parent


def get_string_from_env(key: str, default: Optional[str] = None):
    value = os.getenv(key, "").strip()
    if not value:
        if default is None:
            raise KeyError
        return default
    return value


def get_bool_from_env(key: str, default: Optional[bool] = None):
    value = os.getenv(key, "").lower().strip()
    if not value:
        if default is None:
            raise KeyError
        return default
    return value in ("true", "yes")


class settings:
    """
    Usage:
        from conf import settings
        print(setting.APP_NAME)
    """

    APP_NAME = "strava-analysis-notebook"
    IS_TEST = False
    DB_PATH = get_string_from_env("DB_PATH", str((ROOT_DIR / "db.sqlite3").absolute()))
    DO_LOG_PEEWEE_QUERIES = False

    TOKEN_JSON_PARAMETER_STORE_KEY_PATH = (
        "/strava-facade-api/production/strava-api-token-json"
    )
    CLIENT_ID_PARAMETER_STORE_KEY_PATH = (
        "/strava-facade-api/production/strava-api-client-id"
    )
    CLIENT_SECRET_PARAMETER_STORE_KEY_PATH = (
        "/strava-facade-api/production/strava-api-client-secret"
    )


class test_settings:
    IS_TEST = True
    DB_PATH = get_string_from_env(
        "TEST_DB_PATH", str((ROOT_DIR / "db-pytest.sqlite3").absolute())
    )
    # DB_PATH = ":memory:"


class override_settings(ContextDecorator):
    """
    Context manager and decorator to override single keys in `conf.settings`.
    Only already existing keys can be overridden; non-existing keys are discarded.

    As a context manager:
        with override_settings(APP_NAME="XXX")
            assert settings.APP_NAME == "XXX"

    As decorator, you can decorate a test function or method like:
        @override_settings(APP_NAME="XXX")
        def test_happy_flow(...):
            assert settings.APP_NAME == "XXX"

    But you can NOT decorate a (test) class. To use it for the entire test class:
        class TestMyTest:
            def setup(self):
                self.override_settings = override_settings(APP_NAME="XXX")
                self.override_settings.__enter__()

            def teardown(self):
                self.override_settings.__exit__()
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.orig_values = dict()

    def __enter__(self):
        for key, value in self.kwargs.items():
            # Only update existing keys; discard non-existing keys.
            if not hasattr(settings, key):
                continue
            self.orig_values[key] = getattr(settings, key)
            setattr(settings, key, value)
        return self

    def __exit__(self, *exc):
        for key, value in self.orig_values.items():
            setattr(settings, key, value)
        return False
