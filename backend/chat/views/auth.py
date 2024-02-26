from datetime import timedelta
from typing import Annotated

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from chat import app
from chat.database import get_db
from chat.schema import Token
from chat.setting import setting
from chat.utils.exception import (
    CredentialsException,
)
from chat.utils.jwt import (
    authenticate_user,
    create_access_token,
)


@app.get("/health")
async def health_check():
    """Health Check View"""
    return status.HTTP_200_OK


@app.post("/token", response_model=Token)
async def create_jwt_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_db: Session = Depends(get_db),
):
    """
    Create token for user
    - id [int]
    - username [str]

    output:
    - access_token
    - token_type
    """
    user = authenticate_user(
        user_db,
        form_data.username,
        form_data.password,
    )
    if not user:
        raise CredentialsException
    access_token_expires = timedelta(
        minutes=setting.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    access_token = create_access_token(
        data={"id": user.id, "username": user.username},
        expires_delta=access_token_expires,
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
