import json
from pathlib import Path

from .base_token_manager import BaseTokenManager, BaseTokenManagerException

__all__ = [
    "FileTokenManager",
    "FileTokenManagerException",
]


class FileTokenManager(BaseTokenManager):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_json_file_path: Path,
        do_force_skip_refresh_token=False,  # Set to True when replaying test cassettes.
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_json_file_path = token_json_file_path
        self._token = None
        self._do_force_skip_refresh_token = do_force_skip_refresh_token

    def get_access_token(self) -> str:
        """
        Get the access token stored in the file.
        """
        if not self._token:
            self._load_token_from_file()

        if self._token and self._is_expired() and not self._do_force_skip_refresh_token:
            print("Access token expired, refreshing...")
            self._refresh_token_from_strava()
            self._write_token_to_file()

        return self._token["access_token"]

    def _load_token_from_file(self):
        try:
            with open(self._token_json_file_path) as fin:
                content = fin.read()
        except FileNotFoundError:
            raise FileTokenManagerException(
                f"File not found: {self._token_json_file_path}"
            )

        try:
            self._token = json.loads(content)
        except json.JSONDecodeError as exc:
            raise FileTokenManagerException(
                f"JSONDecodeError: {self._token_json_file_path}"
            ) from exc

        if not self._token.get("access_token"):
            raise FileTokenManagerException(
                f"Missing 'access_token' in: {self._token_json_file_path}"
            )
        if not self._token.get("refresh_token"):
            raise FileTokenManagerException(
                f"Missing 'refresh_token' in: {self._token_json_file_path}"
            )
        if not self._token.get("expires_at"):
            raise FileTokenManagerException(
                f"Missing 'expires_at' in: {self._token_json_file_path}"
            )

    def _write_token_to_file(self) -> None:
        with open(self._token_json_file_path, "w") as fout:
            fout.write(json.dumps(self._token, indent=4))


class FileTokenManagerException(BaseTokenManagerException):
    pass
