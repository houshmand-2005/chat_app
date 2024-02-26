from datetime import datetime, timedelta
from typing import Annotated

import bcrypt
from chat import models
from chat.database import get_db
from chat.schema import TokenData, User
from chat.setting import setting
from chat.utils.exception import CredentialsException
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies if the provided plain text password matches the stored hashed password.

    Args:
        plain_password: The plain text password entered by the user.
        hashed_password: The stored hashed password from the database.

    Returns:
        True if the passwords match, False otherwise.
    """
    encoded_hashed_password = hashed_password.encode("utf-8")
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        encoded_hashed_password,
    )


def get_password_hash(password: str) -> str:
    """
    Generates a bcrypt hash for the provided password.

    Args:
        password: The plain text password to hash.

    Returns:
        The generated password hash.
    """
    hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed_bytes.decode("utf-8")


def get_user(user_db: Session, username: str) -> models.User:
    """
    Retrieve a user from the database based on the username.

    Args:
        user_db (Session): The database session.
        username (str): The username of the user to retrieve.

    Returns:
        Optional[models.User]: The user object if found, None otherwise.
    """
    user = user_db.query(models.User).filter(models.User.username == username).first()
    return user


def authenticate_user(
    user_db: Session, username: str, password: str
) -> models.User | None:
    """
    Authenticate a user based on the provided username and password.

    Args:
        user_db (Session): The database session.
        username (str): The username of the user to authenticate.
        password (str): The password of the user to authenticate.

    Returns:
        Optional[models.User]: The authenticated user object if successful, None otherwise.
    """
    user = get_user(user_db, username)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create an access token with the provided data.

    Args:
        data (dict): The data to include in the token payload.
        expires_delta (timedelta, optional): The expiration time delta for the token. Defaults to None.

    Returns:
        str: The generated access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    to_encode["id"] = int(to_encode.get("id"))
    encoded_jwt = jwt.encode(
        to_encode,
        setting.SECRET_KEY,
        algorithm=setting.ALGORITHM,
    )
    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_db: Session = Depends(
        get_db,
    ),
) -> User:
    """
    Get the current authenticated user from the provided token.

    Args:
        token (str): The JWT token representing the user.
        user_db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        models.User: The current authenticated user.
    """
    token_data = decode_jwt(token)
    user = get_user(user_db, username=token_data.username)
    if user is None:
        raise CredentialsException
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get the current active authenticated user.

    Args:
        current_user (User): The current authenticated user.

    Raises:
        HTTPException: If the user is inactive.

    Returns:
        models.User: The current active authenticated user.
    """
    if current_user.disabled:
        raise HTTPException(
            status_code=400, detail="Inactive user"
        )  # TODO Add this to Exceptions
    return current_user


def get_admin_payload(token: str) -> dict | None:
    """
    Decode the payload of the provided JWT token for admin user.

    Args:
        token (str): The JWT token to decode.

    Returns:
        Optional[dict]: The payload data containing username and id if the token is valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, setting.SECRET_KEY, setting.ALGORITHM)
        username: str = payload.get("username")
        id: int = int(payload.get("id"))
        return {"username": username, "id": id}
    except JWTError:
        return


def decode_jwt(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> TokenData | CredentialsException:
    """
    Decode the provided JWT token and extract the token data.

    Args:
        token (str): The JWT token to decode.

    Returns:
        TokenData: The token data containing username and id.
    """
    try:
        payload = jwt.decode(
            token,
            setting.SECRET_KEY,
            algorithms=[setting.ALGORITHM],
        )
        username: str = payload.get("username")
        user_id: int = int(payload.get("id"))
        if username is None or user_id is None:
            raise CredentialsException
        token_data = TokenData(username=username, id=user_id)
    except JWTError:
        raise CredentialsException
    return token_data
