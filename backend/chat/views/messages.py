from fastapi import Depends
from sqlalchemy.orm import Session
from chat import app
from chat import models
from chat.database import get_db
from chat.utils.jwt import (
    get_current_active_user,
)
from chat.crud import (
    get_message_by_id,
    group_membership_check,
    get_first_unread_message_group,
    create_change_controller,
)
from chat.utils.exception import (
    ForbiddenException,
    NotFoundException,
)
from chat.views.websocket import broadcast_changes


@app.get("/message/{group_id}/first-unread-message", tags=["Messages"])
async def get_first_unread_message(
    group_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> int | None:
    """
    Send first unread message id
    - group_id [int]

    output:
    - id [int]
    """
    group = await group_membership_check(group_id=group_id, user=current_user, db=db)
    if not group:
        raise NotFoundException
    first_unread_message = await get_first_unread_message_group(
        group_id=group_id,
        user=current_user,
        db=db,
    )
    if not first_unread_message:
        raise NotFoundException
    return first_unread_message.id  # TODO: change model to schema to solve this error


@app.put("/message/{message_id}", tags=["Messages"])
async def edit_message_by_id(
    message_id: int,
    changed_message: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> str | None:
    """
    Edit text of the message by message id
    - message_id [int]
    - changed_message [str]

    output:
    - changed message [str]
    """
    message = await get_message_by_id(
        db=db,
        message_id=message_id,
        user_id=current_user.id,
    )
    if message:
        await create_change_controller(
            db=db,
            new_text=changed_message,
            original_text=message.text,
            group_id=message.group_id,
            sender_id=current_user.id,
            changes_type=models.ChangeType.Edit,
        )
        message.text = changed_message
        db.commit()  ## TODO MOVE THIS TO CRUD
        await broadcast_changes(
            db=db,
            group_id=message.group_id,
            change_type=models.ChangeType.Edit,
            message_id=message_id,
            new_text=changed_message,
        )
        return message.text
    raise ForbiddenException


@app.delete("/message/{message_id}", tags=["Messages"])
async def delete_message_by_id(
    message_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> str | None:
    """
    Delete text of the message by message id
    - message_id [int]

    output:
    - deleted message text [str]
    """
    message = await get_message_by_id(
        db=db,
        message_id=message_id,
        user_id=current_user.id,
    )
    if message:
        unread_messages = (
            db.query(models.UnreadMessage).filter_by(message_id=message.id).first()
        )
        if unread_messages:
            db.delete(unread_messages)
        await create_change_controller(
            db=db,
            new_text="",
            original_text=message.text,
            group_id=message.group_id,
            sender_id=current_user.id,
            changes_type=models.ChangeType.Delete,
        )
        db.delete(message)
        db.commit()

        await broadcast_changes(
            db=db,
            group_id=message.group_id,
            change_type=models.ChangeType.Delete,
            message_id=message_id,
            new_text="",
        )
        return message.text
    raise ForbiddenException
