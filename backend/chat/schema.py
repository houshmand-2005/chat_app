from datetime import datetime

from pydantic import BaseModel

from chat.models import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    id: int | None = None


class User(BaseModel):
    id: int | None = None  # may create some bug check it later TODO
    username: str
    password: str
    display_name: str
    email: str | None = None
    role: UserRole
    bio: str | None = None
    profile_pic: str | None = None
    disabled: bool | bool = False


class CreateUser(BaseModel):
    username: str
    password: str
    email: str | None = None
    full_name: str | None = None


class GroupCreate(BaseModel):
    address: str
    name: str = ""


class GroupMembersResponse(BaseModel):
    group_id: int
    members: list[str]


class GroupMessageResponse(BaseModel):
    username: str
    message_id: int
    time: datetime
    message_text: str


class GetGroupMessagesResponse(BaseModel):
    messages: list[GroupMessageResponse]
