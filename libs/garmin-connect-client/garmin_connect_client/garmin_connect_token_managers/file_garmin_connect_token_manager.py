import base64
import json
from getpass import getpass
from pathlib import Path

from .base_garmin_connect_token_manager import (
    BaseGarminConnectTokenManager,
    BaseGarminConnectTokenManagerException,
)

__all__ = [
    "FileGarminConnectTokenManager",
    "FileGarminConnectTokenManagerException",
]

ROOT_DIR = Path(__file__).parent.parent.parent
DEFAULT_TOKEN_FILE = ROOT_DIR / "garmin-connect-token.json"


class FileGarminConnectTokenManager(BaseGarminConnectTokenManager):
    def __init__(
        self,
        email: str | None = None,
        password: str | None = None,
        token_file_path: Path = DEFAULT_TOKEN_FILE,
        token_base64: str | None = None,
    ) -> None:
        self._email = email
        self._password = password
        self._token_file_path = token_file_path
        self._token_base64 = token_base64

    def get_email(self) -> str:
        if not self._email:
            self._email = input("Garmin Connect login email: ")
        return self._email

    def get_password(self) -> str:
        if not self._password:
            self._password = getpass("Garmin Connect login password: ")
        return self._password

    def get_access_token(self) -> str:
        """
        Get the access token stored in the file.
        """
        if not self._token_base64:
            try:
                with open(self._token_file_path, "r") as fin:
                    token_plain = fin.read()
            except FileNotFoundError as exc:
                raise FileGarminConnectTokenManagerException(
                    f"File not found: {self._token_file_path}"
                ) from exc

            try:
                self._token_base64 = base64.b64encode(token_plain.encode()).decode()
            except TypeError as exc:
                raise FileGarminConnectTokenManagerException(
                    "Token not encoded as base64"
                ) from exc
        return self._token_base64

    def store_access_token(self, token_base64: str):
        """
        Store the access token in the file.
        """
        self._token_base64 = token_base64
        token = base64.b64decode(token_base64).decode()
        token_json = json.dumps(json.loads(token), indent=2)

        with open(self._token_file_path, "w") as fout:
            fout.write(token_json)


class FileGarminConnectTokenManagerException(BaseGarminConnectTokenManagerException):
    pass
