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
        do_use_fake_test_token: bool = False,
    ) -> None:
        self._email = email
        self._password = password
        self._token_file_path = token_file_path
        self._token_base64 = token_base64
        if do_use_fake_test_token:
            # This is just a fake token with expiration date in year 3999.
            # It's meant to be used in vcrpy tests where the token is ignored.
            # It won't work with the real Garmin Connect backend.
            self._token_base64 = "W3sib2F1dGhfdG9rZW4iOiAieHh4IiwgIm9hdXRoX3Rva2VuX3NlY3JldCI6ICJ4eHgiLCAibWZhX3Rva2VuIjogInh4eCIsICJtZmFfZXhwaXJhdGlvbl90aW1lc3RhbXAiOiA2NDAzODUxMzAwMSwgImRvbWFpbiI6ICJnYXJtaW4uY29tIn0sIHsic2NvcGUiOiAiQ09NTVVOSVRZX0NPVVJTRV9SRUFEIEdBUk1JTlBBWV9XUklURSBHT0xGX0FQSV9SRUFEIEFUUF9SRUFEIEdIU19TQU1EIEdIU19VUExPQUQgSU5TSUdIVFNfUkVBRCBESVZFX0FQSV9SRUFEIENPTU1VTklUWV9DT1VSU0VfV1JJVEUgQ09OTkVDVF9XUklURSBHQ09GRkVSX1dSSVRFIERJX09BVVRIXzJfQVVUSE9SSVpBVElPTl9DT0RFX0NSRUFURSBHQVJNSU5QQVlfUkVBRCBEVF9DTElFTlRfQU5BTFlUSUNTX1dSSVRFIEdPTEZfQVBJX1dSSVRFIElOU0lHSFRTX1dSSVRFIFBST0RVQ1RfU0VBUkNIX1JFQUQgT01UX0NBTVBBSUdOX1JFQUQgT01UX1NVQlNDUklQVElPTl9SRUFEIEdDT0ZGRVJfUkVBRCBDT05ORUNUX1JFQUQgQVRQX1dSSVRFIiwgImp0aSI6ICJ4eHgiLCAidG9rZW5fdHlwZSI6ICJiZWFyZXIiLCAiYWNjZXNzX3Rva2VuIjogInh4eCIsICJyZWZyZXNoX3Rva2VuIjogInh4eCIsICJleHBpcmVzX2luIjogNjQwMzg1MTMwMDEsICJleHBpcmVzX2F0IjogNjQwMzg1MTMwMDEsICJyZWZyZXNoX3Rva2VuX2V4cGlyZXNfaW4iOiA2NDAzODUxMzAwMSwgInJlZnJlc2hfdG9rZW5fZXhwaXJlc19hdCI6IDY0MDM4NTEzMDAxfV0="

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
