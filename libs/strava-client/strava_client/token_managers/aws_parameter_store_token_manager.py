import importlib
import json

from .base_token_manager import BaseTokenManager, BaseTokenManagerException

__all__ = [
    "AwsParameterStoreTokenManager",
    "AwsParameterStoreTokenManagerException",
]


class AwsParameterStoreTokenManager(BaseTokenManager):
    def __init__(
        self,
        token_json_parameter_store_key_path: str,  # Eg: "/strava-facade-api/production/strava-api-token-json"
        client_id_parameter_store_key_path: str,  # Eg: "/strava-facade-api/production/strava-api-client-id"
        client_secret_parameter_store_key_path: str,  # Eg: "/strava-facade-api/production/strava-api-client-secret"
        do_force_skip_refresh_token=False,  # Set to True when replaying test cassettes.
    ) -> None:
        self._token_json_parameter_store_key_path = token_json_parameter_store_key_path
        self._client_id_parameter_store_key_path = client_id_parameter_store_key_path
        self._client_secret_parameter_store_key_path = (
            client_secret_parameter_store_key_path
        )
        self._token = None
        self._do_force_skip_refresh_token = do_force_skip_refresh_token
        # Dynamic import, since Rich is an optional extra.
        self.AwsParameterStoreClient = importlib.import_module(
            "aws_parameter_store_client.aws_parameter_store_client"
        ).AwsParameterStoreClient
        self.ParameterNotFound = importlib.import_module(
            "aws_parameter_store_client.aws_parameter_store_client"
        ).ParameterNotFound

    @property
    def _client_id(self):
        path = self._client_id_parameter_store_key_path
        try:
            content = self.AwsParameterStoreClient().get_secret(path)
        except self.ParameterNotFound as exc:
            raise AwsParameterStoreTokenManagerException() from exc
        return content

    @property
    def _client_secret(self):
        path = self._client_secret_parameter_store_key_path
        try:
            content = self.AwsParameterStoreClient().get_secret(path)
        except self.ParameterNotFound as exc:
            raise AwsParameterStoreTokenManagerException() from exc
        return content

    def get_access_token(self) -> str:
        """
        Get the access token stored in AWS Parameter Store.
        """
        if not self._token:
            self._load_token_from_parameter_store()

        if self._token and self._is_expired() and not self._do_force_skip_refresh_token:
            print("Access token expired, refreshing...")
            self._refresh_token_from_strava()
            self._write_token_to_parameter_store()

        return self._token["access_token"]

    def _load_token_from_parameter_store(self):
        path = self._token_json_parameter_store_key_path
        try:
            content = self.AwsParameterStoreClient().get_secret(path)
        except self.ParameterNotFound as exc:
            raise AwsParameterStoreTokenManagerException() from exc

        try:
            self._token = json.loads(content)
        except json.JSONDecodeError:
            raise AwsParameterStoreTokenManagerException(
                f"JSONDecodeError in SSM: {path}"
            )

        if not self._token.get("access_token"):
            raise AwsParameterStoreTokenManagerException(
                f"Missing 'access_token' in SSM: {path}"
            )
        if not self._token.get("refresh_token"):
            raise AwsParameterStoreTokenManagerException(
                f"Missing 'refresh_token' in SSM: {path}"
            )
        if not self._token.get("expires_at"):
            raise AwsParameterStoreTokenManagerException(
                f"Missing 'expires_at' in SSM: {path}"
            )

    def _write_token_to_parameter_store(self) -> None:
        path = self._token_json_parameter_store_key_path
        self.AwsParameterStoreClient().put_secret(
            path,
            json.dumps(self._token, indent=4),
            do_overwrite=True,
        )


class AwsParameterStoreTokenManagerException(BaseTokenManagerException):
    pass
