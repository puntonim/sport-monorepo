"""
A very basic settings manager. I chose this because this app requires only a few
 settings and no special features.

A better alternative, in case the app requires more settings and advanced features,
 is Dynaconf.
"""

from pathlib import Path

CURR_DIR = Path(__file__).parent
ROOT_DIR = CURR_DIR.parent.parent


# TODO note that these settings are currently unused.
class settings:
    """
    Usage:
        from conf import settings
        print(setting.APP_NAME)
    """

    APP_NAME = "STRAVA-CLIENT"
    IS_TEST = False


class test_settings:
    IS_TEST = True
