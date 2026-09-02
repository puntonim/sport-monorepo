"""
A very basic settings manager. I chose this because this app requires only a few
 settings and no special features.

A better alternative, in case the app requires more settings and advanced features,
 is Dynaconf.
"""

from pathlib import Path

import settings_utils

CURR_DIR = Path(__file__).parent
ROOT_DIR = CURR_DIR.parent.parent


class settings:
    """
    Usage:
        from conf import settings
        print(setting.APP_NAME)
    """

    APP_NAME = "strava-analysis-notebook"
    IS_TEST = False
    ARE_CONSOLE_LOGS_ENABLED = True
    ARE_CONSOLE_PRINTS_ENABLED = True
    DB_PATH = settings_utils.get_string_from_env(
        "DB_PATH", str((ROOT_DIR / "db.sqlite3").absolute())
    )
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

    HR_MIN = 46
    HR_MAX_EVER_RIDE = 157
    # Run For Life Monza (PR HM: 1:32:49 🏆)
    # https://www.strava.com/activities/17644996304
    # https://connect.garmin.com/modern/activity/22100401605
    # 2026-03-08T09:10:15Z
    # HR: 148.6 (max 174)
    # HR band: Yes
    HR_MAX_EVER_RUN = 174


class test_settings:
    IS_TEST = True
    DB_PATH = settings_utils.get_string_from_env(
        "TEST_DB_PATH", str((ROOT_DIR / "db-pytest.sqlite3").absolute())
    )
    # DB_PATH = ":memory:"
