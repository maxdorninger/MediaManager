import contextlib
import logging
import uuid
from typing import Optional, Any

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, models
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from httpx_oauth.clients.openid import OpenID
from fastapi.responses import RedirectResponse, Response
from starlette import status
from sqlalchemy import select, func

import media_manager.notification.utils
from media_manager.auth.db import User, get_user_db, get_async_session
from media_manager.auth.schemas import UserUpdate, UserCreate
from media_manager.config import AllEncompassingConfig

log = logging.getLogger(__name__)

config = AllEncompassingConfig().auth
SECRET = config.token_secret
LIFETIME = config.session_lifetime

openid_client: OpenID | None = None
if config.openid_connect.enabled:
    log.info(f"Configured OIDC provider: {config.openid_connect.name}")
    openid_client = OpenID(
        base_scopes=["openid", "email", "profile"],
        client_id=config.openid_connect.client_id,
        client_secret=config.openid_connect.client_secret,
        name=config.openid_connect.name,
        openid_configuration_endpoint=config.openid_connect.configuration_endpoint,
    )


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_update(
        self,
        user: models.UP,
        update_dict: dict[str, Any],
        request: Optional[Request] = None,
    ) -> None:
        log.info(f"User {user.id} has been updated.")
        if "is_superuser" in update_dict and update_dict["is_superuser"]:
            log.info(f"User {user.id} has been granted superuser privileges.")
        if "email" in update_dict:
            updated_user = UserUpdate(is_verified=True)
            await self.update(user=user, user_update=updated_user)

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        log.info(f"User {user.id} has registered.")
        if user.email in config.admin_emails:
            updated_user = UserUpdate(is_superuser=True, is_verified=True)
            await self.update(user=user, user_update=updated_user)

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        link = f"{AllEncompassingConfig().misc.frontend_url}login/reset-password?token={token}"
        log.info(f"User {user.id} has forgot their password. Reset Link: {link}")

        if not config.email_password_resets:
            log.info("Email password resets are disabled, not sending email.")
            return

        subject = "MediaManager - Password Reset Request"
        html = f"""\
        <html>
          <body>
            <p>Hi {user.email},
            <br>
            <br>
            if you forgot your password, <a href="{link}">reset you password here</a>.<br>
            If you did not request a password reset, you can ignore this email.</p>
            <br>
            <br>
            If the link does not work, copy the following link into your browser: {link}<br>
          </body>
        </html>
        """
        media_manager.notification.utils.send_email(
            subject=subject, html=html, addressee=user.email
        )
        log.info(f"Sent password reset email to {user.email}")

    async def on_after_reset_password(
        self, user: User, request: Optional[Request] = None
    ):
        log.info(f"User {user.id} has reset their password.")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        log.info(
            f"Verification requested for user {user.id}. Verification token: {token}"
        )

    async def on_after_verify(self, user: User, request: Optional[Request] = None):
        log.info(f"User {user.id} has been verified")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def create_default_admin_user():
    """Create a default admin user if no users exist in the database"""
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    # Check if any users exist
                    stmt = select(func.count(User.id))
                    result = await session.execute(stmt)
                    user_count = result.scalar()
                    config = AllEncompassingConfig()
                    if user_count == 0:
                        log.info(
                            "No users found in database. Creating default admin user..."
                        )

                        # Use the first admin email from config, or default
                        admin_email = (
                            config.auth.admin_emails[0]
                            if config.auth.admin_emails
                            else "admin@example.com"
                        )
                        default_password = "admin"  # Simple default password

                        user_create = UserCreate(
                            email=admin_email,
                            password=default_password,
                            is_superuser=True,
                            is_verified=True,
                        )

                        user = await user_manager.create(user_create)
                        log.info("=" * 60)
                        log.info("DEFAULT ADMIN USER CREATED!")
                        log.info(f"    Email: {admin_email}")
                        log.info(f"    Password: {default_password}")
                        log.info(f"    User ID: {user.id}")
                        log.info(
                            "IMPORTANT: Please change this password after first login!"
                        )
                        log.info("=" * 60)

                    else:
                        log.info(
                            f"Found {user_count} existing users. Skipping default user creation."
                        )
    except Exception as e:
        log.error(f"Failed to create default admin user: {e}")
        log.info(
            "You can create an admin user manually by registering with an email from the admin_emails list in your config."
        )


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


def get_jwt_strategy() -> JWTStrategy[models.UP, models.ID]:
    return JWTStrategy(secret=SECRET, lifetime_seconds=LIFETIME)


# needed because the default CookieTransport does not redirect after login,
# thus the user would be stuck on the OAuth Providers "redirecting" page
class RedirectingCookieTransport(CookieTransport):
    async def get_login_response(self, token: str) -> Response:
        response = RedirectResponse(
            str(AllEncompassingConfig().misc.frontend_url) + "dashboard",
            status_code=status.HTTP_302_FOUND,
        )
        return self._set_login_cookie(response, token)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
cookie_transport = CookieTransport(
    cookie_max_age=LIFETIME, cookie_samesite="lax", cookie_secure=False
)
openid_cookie_transport = RedirectingCookieTransport(
    cookie_max_age=LIFETIME, cookie_samesite="lax", cookie_secure=False
)

bearer_auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
cookie_auth_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)
openid_cookie_auth_backend = AuthenticationBackend(
    name="cookie",
    transport=openid_cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager, [bearer_auth_backend, cookie_auth_backend]
)

current_active_user = fastapi_users.current_user(active=True, verified=True)
current_superuser = fastapi_users.current_user(
    active=True, verified=True, superuser=True
)
