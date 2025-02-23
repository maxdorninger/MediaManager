import logging
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

import config
import database
import database.users
from database.users import UserInternal


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    uid: str | None = None


log = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token")

router = APIRouter()


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInternal:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    log.debug("token: " + token)
    try:
        payload = jwt.decode(token, config.auth.jwt_signing_key, algorithms=[config.auth.jwt_signing_algorithm])
        log.debug("jwt payload: " + payload.__str__())
        user_uid: str = payload.get("sub")
        log.debug("jwt payload sub (user uid): " + user_uid)
        if user_uid is None:
            raise credentials_exception
        token_data = TokenData(uid=user_uid)
    except InvalidTokenError:
        log.warning("received invalid token: " + token)
        raise credentials_exception
    user = database.users.get_user(uid=token_data.uid)
    if user is None:
        log.debug("user not found")
        raise credentials_exception
    log.debug("received user: " + user.__str__())
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=config.auth.jwt_access_token_lifetime)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.auth.jwt_signing_key, algorithm=config.auth.jwt_signing_algorithm)
    return encoded_jwt
