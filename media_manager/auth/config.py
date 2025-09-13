from pydantic_settings import BaseSettings
from pydantic import Field
import secrets


class OpenIdConfig(BaseSettings):
    client_id: str = ""
    client_secret: str = ""
    configuration_endpoint: str = ""
    enabled: bool = False
    name: str = "OAuth2"


class AuthConfig(BaseSettings):
    # to get a signing key run:
    # openssl rand -hex 32
    token_secret: str = Field(default_factory=secrets.token_hex)
    session_lifetime: int = 60 * 60 * 24
    admin_emails: list[str] = []
    email_password_resets: bool = False
    openid_connect: OpenIdConfig = OpenIdConfig()

    @property
    def jwt_signing_key(self):
        return self._jwt_signing_key
