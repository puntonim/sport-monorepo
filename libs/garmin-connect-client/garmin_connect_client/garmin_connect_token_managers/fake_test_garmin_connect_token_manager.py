from .base_garmin_connect_token_manager import BaseGarminConnectTokenManager

__all__ = ["FakeTestGarminConnectTokenManager"]


class FakeTestGarminConnectTokenManager(BaseGarminConnectTokenManager):
    def __init__(self) -> None:
        # This is just a fake token with expiration date in year 3999.
        # It's meant to be used in vcrpy tests where the token is ignored.
        # It won't work with the real Garmin Connect backend.
        self._token_base64 = "W3sib2F1dGhfdG9rZW4iOiAieHh4IiwgIm9hdXRoX3Rva2VuX3NlY3JldCI6ICJ4eHgiLCAibWZhX3Rva2VuIjogInh4eCIsICJtZmFfZXhwaXJhdGlvbl90aW1lc3RhbXAiOiA2NDAzODUxMzAwMSwgImRvbWFpbiI6ICJnYXJtaW4uY29tIn0sIHsic2NvcGUiOiAiQ09NTVVOSVRZX0NPVVJTRV9SRUFEIEdBUk1JTlBBWV9XUklURSBHT0xGX0FQSV9SRUFEIEFUUF9SRUFEIEdIU19TQU1EIEdIU19VUExPQUQgSU5TSUdIVFNfUkVBRCBESVZFX0FQSV9SRUFEIENPTU1VTklUWV9DT1VSU0VfV1JJVEUgQ09OTkVDVF9XUklURSBHQ09GRkVSX1dSSVRFIERJX09BVVRIXzJfQVVUSE9SSVpBVElPTl9DT0RFX0NSRUFURSBHQVJNSU5QQVlfUkVBRCBEVF9DTElFTlRfQU5BTFlUSUNTX1dSSVRFIEdPTEZfQVBJX1dSSVRFIElOU0lHSFRTX1dSSVRFIFBST0RVQ1RfU0VBUkNIX1JFQUQgT01UX0NBTVBBSUdOX1JFQUQgT01UX1NVQlNDUklQVElPTl9SRUFEIEdDT0ZGRVJfUkVBRCBDT05ORUNUX1JFQUQgQVRQX1dSSVRFIiwgImp0aSI6ICJ4eHgiLCAidG9rZW5fdHlwZSI6ICJiZWFyZXIiLCAiYWNjZXNzX3Rva2VuIjogInh4eCIsICJyZWZyZXNoX3Rva2VuIjogInh4eCIsICJleHBpcmVzX2luIjogNjQwMzg1MTMwMDEsICJleHBpcmVzX2F0IjogNjQwMzg1MTMwMDEsICJyZWZyZXNoX3Rva2VuX2V4cGlyZXNfaW4iOiA2NDAzODUxMzAwMSwgInJlZnJlc2hfdG9rZW5fZXhwaXJlc19hdCI6IDY0MDM4NTEzMDAxfV0="

    def get_access_token(self) -> str:
        return self._token_base64

    def store_access_token(self, token_base64: str):
        pass
