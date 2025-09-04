from media_manager.auth.users import (
    SECRET,
    openid_cookie_auth_backend as backend,
    get_user_manager,
    openid_clients as oauth_clients,
)
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from httpx_oauth.integrations.fastapi import OAuth2AuthorizeCallback
from httpx_oauth.oauth2 import OAuth2Token
from pydantic import BaseModel

from fastapi_users import models
from fastapi_users.authentication import Strategy
from fastapi_users.exceptions import UserAlreadyExists
from fastapi_users.jwt import SecretType, decode_jwt, generate_jwt
from fastapi_users.manager import BaseUserManager
from fastapi_users.router.common import ErrorCode, ErrorModel

STATE_TOKEN_AUDIENCE = "fastapi-users:oauth-state"


class OAuth2AuthorizeResponse(BaseModel):
    authorization_url: str


def generate_state_token(
    data: dict[str, str], secret: SecretType, lifetime_seconds: int = 3600
) -> str:
    data["aud"] = STATE_TOKEN_AUDIENCE
    return generate_jwt(data, secret, lifetime_seconds)


router = APIRouter(prefix="/auth/oauth")


def get_authorize_callback(provider_name: str):
    if provider_name not in oauth_clients:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return OAuth2AuthorizeCallback(
        oauth_clients[provider_name],
        route_name="oauth:callback",
        redirect_url=str(router.url_path_for("oauth:callback")),
    )


@router.get(
    "/{openid_provider_name}/authorize",
    response_model=OAuth2AuthorizeResponse,
)
async def authorize(
    request: Request,
    openid_provider_name: str,
) -> OAuth2AuthorizeResponse:
    if openid_provider_name not in oauth_clients:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    oauth_client = oauth_clients[openid_provider_name]

    authorize_redirect_url = str(request.url_for("oauth:callback"))
    state = generate_state_token({"provider_name": openid_provider_name}, SECRET)
    authorization_url = await oauth_client.get_authorization_url(
        authorize_redirect_url,
        state,
        ["openid", "profile", "email"],
    )

    return OAuth2AuthorizeResponse(authorization_url=authorization_url)


@router.get(
    "/callback",
    name="oauth:callback",
)
async def callback(
    request: Request,
    user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
    strategy: Strategy[models.UP, models.ID] = Depends(backend.get_strategy),
    access_token_state = None,
) -> None:
    state_from_query = request.query_params.get("state")
    if not state_from_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing state token"
        )

    try:
        state_data = decode_jwt(state_from_query, SECRET, [STATE_TOKEN_AUDIENCE])
    except jwt.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state token"
        )

    openid_provider_name = state_data.get("provider_name")
    if not openid_provider_name or openid_provider_name not in oauth_clients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider name in state token",
        )

    authorize_callback = get_authorize_callback(openid_provider_name)
    token, state = await authorize_callback(request)

    oauth_client = oauth_clients[openid_provider_name]

    account_id, account_email = await oauth_client.get_id_email(token["access_token"])

    if account_email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.OAUTH_NOT_AVAILABLE_EMAIL,
        )

    try:
        user = await user_manager.oauth_callback(
            oauth_client.name,
            token["access_token"],
            account_id,
            account_email,
            token.get("expires_at"),
            token.get("refresh_token"),
            request,
            associate_by_email=True,
            is_verified_by_default=True,
        )
    except UserAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.OAUTH_USER_ALREADY_EXISTS,
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
        )

    # Authenticate
    response = await backend.login(strategy, user)
    await user_manager.on_after_login(user, request, response)
    return response
