from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Annotated
from chat import app
from chat.schema import CreateUser, User
from chat.utils.jwt import (
    get_current_active_user,
)
from chat.utils.exception import (
    AlreadyExistsException,
)
from chat.crud import (
    create_user_controller,
    get_user_groups_by_id,
)

from chat.database import get_db


@app.get("/user/me", tags=["User"], response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Get user information

    output:
    - id [int]
    - username [str]
    - password(hashed) [str]
    - display_name [str]
    - role [str]
    - disabled [bool]
    - email [str]
    - bio [str]
    - profile_pic [str]
    """
    return current_user


@app.get("/user/unread_messages", tags=["User"])
async def unread_messages(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Send unread messages detail

    output:
    - id [int]
    - user_id [int]
    - user_name [str]
    - group_id [int]
    - message_id [int]
    """
    return current_user.unread_messages


@app.post("/user/create", response_model=User, tags=["User"])
async def create_user(user: CreateUser, db: Session = Depends(get_db)):
    """
    Create User
    - username [str]
    - password [str]
    - email [str]
    - full_name [str]

    output:
    - id [int]
    - username [str]
    - password [str]
    - display_name [str]
    - email [str]
    - role [str]
    - bio [str]
    - profile_pic [str]
    - disabled [bool]
    """
    created_user = await create_user_controller(db=db, user=user)
    if created_user:
        return created_user
    raise AlreadyExistsException


@app.get("/user/groups", tags=["User"])
async def get_user_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Groups in which the user is a member

    output:
    - id [int]
    - name [str]
    - address
    """
    user_groups = await get_user_groups_by_id(user_id=current_user.id, db=db)
    groups_with_ids = [
        {
            "id": group.id,
            "name": group.name,
            "address": group.address,
        }
        for group in user_groups
    ]
    return {
        "user_id": current_user.id,
        "groups": groups_with_ids,
    }
