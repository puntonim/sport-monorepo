from .base_strava_token_manager import BaseStravaTokenManager

__all__ = [
    "FakeTestStravaTokenManager",
]


class FakeTestStravaTokenManager(BaseStravaTokenManager):
    def __init__(self) -> None:
        self._token = "XXX"

    def get_access_token(self) -> str:
        return self._token
