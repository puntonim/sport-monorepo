import json
from pathlib import Path

from .base_strava_token_manager import (
    BaseStravaTokenManager,
    BaseStravaTokenManagerException,
)

__all__ = [
    "FileStravaTokenManager",
    "FileStravaTokenManagerException",
]


class FileStravaTokenManager(BaseStravaTokenManager):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_json_file_path: Path,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_json_file_path = token_json_file_path
        self._token = None

    def get_access_token(self) -> str:
        """
        Get the access token stored in the file.
        """
        if not self._token:
            self._load_token_from_file()

        if self._token and self._is_expired():
            print("Access token expired, refreshing...")
            self._refresh_token_from_strava()
            self._write_token_to_file()

        return self._token["access_token"]

    def _load_token_from_file(self):
        try:
            with open(self._token_json_file_path) as fin:
                content = fin.read()
        except FileNotFoundError as exc:
            raise FileStravaTokenManagerException(
                f"File not found: {self._token_json_file_path}"
            ) from exc

        try:
            self._token = json.loads(content)
        except json.JSONDecodeError as exc:
            raise FileStravaTokenManagerException(
                f"JSONDecodeError: {self._token_json_file_path}"
            ) from exc

        if not self._token.get("access_token"):
            raise FileStravaTokenManagerException(
                f"Missing 'access_token' in: {self._token_json_file_path}"
            )
        if not self._token.get("refresh_token"):
            raise FileStravaTokenManagerException(
                f"Missing 'refresh_token' in: {self._token_json_file_path}"
            )
        if not self._token.get("expires_at"):
            raise FileStravaTokenManagerException(
                f"Missing 'expires_at' in: {self._token_json_file_path}"
            )

    def _write_token_to_file(self) -> None:
        with open(self._token_json_file_path, "w") as fout:
            fout.write(json.dumps(self._token, indent=4))


class FileStravaTokenManagerException(BaseStravaTokenManagerException):
    pass
