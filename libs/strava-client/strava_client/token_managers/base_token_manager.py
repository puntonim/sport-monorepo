from time import time

import requests

__all__ = [
    "BaseTokenManagerException",
]


class BaseTokenManager:
    def _is_expired(self) -> bool:
        # `expires_at` is in seconds since the epoch.
        # Eg. 1691977531 for Monday, August 14, 2023 1:45:31 AM at GMT timezone.
        expires_at = self._token.get("expires_at")
        return expires_at <= time()

    def _refresh_token_from_strava(self):
        url = "https://www.strava.com/oauth/token"
        payload = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "refresh_token": self._token["refresh_token"],
            "grant_type": "refresh_token",
        }
        response = requests.post(url, data=payload)
        response.raise_for_status()
        if not self._token.get("access_token"):
            raise BaseTokenManagerException(
                "Missing 'access_token' in JSON response to Strava refresh token request"
            )
        if not self._token.get("refresh_token"):
            raise BaseTokenManagerException(
                "Missing 'refresh_token' in JSON response to Strava refresh token request"
            )
        if not self._token.get("expires_at"):
            raise BaseTokenManagerException(
                "Missing 'expires_at' in JSON response to Strava refresh token request"
            )
        self._token = response.json()


class BaseTokenManagerException(Exception):
    pass
