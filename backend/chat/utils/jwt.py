from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from chat.setting import setting
from chat.utils.exception import CredentialsException
from chat.database import SessionLocal, engine
import chat.models as models
from chat.schema import TokenData, User

models.Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(user_db: Session, username: str):
    user = user_db.query(models.User).filter(models.User.username == username).first()
    return user


def authenticate_user(user_db: Session, username: str, password: str):
    user = get_user(user_db, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
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
):
    token_data = decode_jwt(token)
    user = get_user(user_db, username=token_data.username)
    if user is None:
        raise CredentialsException
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_admin_payload(token: str):
    try:
        payload = jwt.decode(token, setting.SECRET_KEY, setting.ALGORITHM)
        username: str = payload.get("username")
        id: int = int(payload.get("id"))
        return {"username": username, "id": id}
    except JWTError:
        return


def decode_jwt(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenData:
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
