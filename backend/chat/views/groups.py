from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from chat import app, models, schema
from chat.crud import (
    create_group_controller,
    get_group_by_address,
    get_reads_messages,
    group_members_by_id,
    group_membership_check,
    join_member_to_group,
)
from chat.database import get_db
from chat.utils.exception import (
    AlreadyExistsException,
    ForbiddenException,
    NotFoundException,
)
from chat.utils.jwt import (
    get_current_active_user,
)


@app.post("/group/create/", tags=["Groups"])
async def create_group(
    address: str,
    name: str,
    current_user: schema.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create Group
    - address [str]
    - name [str]

    output:
    - id [int]
    - name [str]
    - members [relationship "GroupMember"]
    - messages [relationship "Message"]
    """
    # TODO: ADD A VALIDATION TO ALL OD THESE
    print(address, name)
    existing_group = await get_group_by_address(address=address, db=db)
    if existing_group:
        raise AlreadyExistsException
    # TODO:add other things to group like user name and ..
    new_group = await create_group_controller(
        db=db, group=schema.GroupCreate(address=address, name=name)
    )
    await join_member_to_group(
        db=db,
        group=new_group,
        user=current_user,
        role=models.UserRole.admin,
    )
    return new_group


@app.get(
    "/group/{group_id}/members",
    tags=["Groups"],
    response_model=schema.GroupMembersResponse,
)
async def get_group_members(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(get_current_active_user),
):
    """
    get group members
    - group_id [int]

    output:
    - GroupMembersResponse
        - group_id: int
        - members: list[str]
    """
    group_member = await group_membership_check(
        group_id=group_id,
        db=db,
        user=current_user,
    )

    if not group_member:
        raise ForbiddenException
    members = await group_members_by_id(
        group_id=group_id,
        db=db,
    )
    member_usernames = [str(member.username) for member in members]
    return schema.GroupMembersResponse(
        group_id=group_id,
        members=member_usernames,
    )


@app.post("/group/join", response_model=bool, tags=["Groups"])
async def join_group(
    address: str,
    db: Session = Depends(get_db),
    current_user: schema.User = Depends(get_current_active_user),
):
    """
    Join user to selected Group
    - address [str]

    output:
    - true [bool]
    """
    group_add = await get_group_by_address(address=address, db=db)
    if not group_add:
        raise NotFoundException
    existing_member = await group_membership_check(
        db=db, group_id=group_add.id, user=current_user  # type: ignore
    )
    if existing_member:
        raise AlreadyExistsException
    await join_member_to_group(
        db=db,
        group=group_add,
        user=current_user,
        role=models.UserRole.member,
    )
    return True


@app.get("/group/{group_id}/messages", tags=["Groups"])
async def get_group_messages(
    group_id: int,
    current_user: Annotated[schema.User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    """
    Get Group reads messages
    - group_id [int]

    output:
    - username [str]
    - message_id [int]
    - time [str]
    - message_text [str]
    """
    group = await group_membership_check(
        group_id=group_id,
        user=current_user,
        db=db,
    )
    if not group:
        raise NotFoundException  # TODO: raise errors better like if group exists but if user is not user of that group raise another error
    messages = await get_reads_messages(
        user=current_user,
        group_id=group_id,
        db=db,
    )
    if messages:
        messages_data = [
            {
                "username": message.sender_name,
                "message_id": message.id,
                "datetime": str(message.created_at),
                "message_text": message.text,
            }
            for message in messages
        ]
        return messages_data
