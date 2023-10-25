import asyncio
import json
from fastapi import WebSocket, Depends, WebSocketDisconnect
from sqlalchemy.orm import Session

from chat import models
from chat.utils.jwt import get_current_user
from chat.database import get_db
from chat.models import Message, User
from chat.crud import (
    group_membership_check,
    create_message_controller,
    create_unread_message_controller,
    get_group_by_id,
)
from chat import app, logger

websocket_connections = {}


@app.websocket("/send-message")
async def send_messages_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db),
) -> None:
    """
    User send message api
    - token [str]
    - group_id [int]

    [in websocket]
    - text

    output:
     - None
    """
    token = websocket.query_params.get("token")
    group_id = websocket.query_params.get("group_id")
    if token and group_id:
        user = await get_current_user(user_db=db, token=token)
        group_id = int(group_id)
    else:
        return await websocket.close(reason="You're not allowed", code=4403)
    is_group_member = await group_membership_check(
        group_id=group_id,
        db=db,
        user=user,
    )
    if not is_group_member:
        logger.error(
            "User %s Connect to Send Messages But not allowed with group id : %s",
            user.username,
            group_id,
        )
        return await websocket.close(reason="You're not allowed", code=4403)
    if user:
        logger.info(
            "User %s Connect to Send Messages endpoint group id : %s",
            user.username,
            group_id,
        )
        user.websocket = websocket
        await websocket.accept()
        while True:
            try:
                data = await websocket.receive_text()
            except WebSocketDisconnect as error_message:
                logger.info(
                    "User %s Disconnect from Send Messages endpoint group id : %s, %s",
                    user.username,
                    group_id,
                    error_message,
                )
                break
            if data is None:
                break
            message = await create_message_controller(
                db=db, user=user, group_id=group_id, text=data
            )
            # Broadcast the message to all users in the group
            asyncio.create_task(broadcast_message(group_id, message, db))


async def broadcast_message(group_id: int, message: Message, db) -> None:
    """
    send message to online users and save unread message for other users
    - group_id [int]
    - message [Message]

    output:
    - None
    """
    group = await get_group_by_id(db=db, group_id=group_id)
    if group:
        for member in group.members:
            await create_unread_message_controller(
                db=db,
                message=message,
                user=member.user,
                group_id=group_id,
            )
            if member.user.websocket:
                asyncio.create_task(member.user.websocket.send_text(message.text))


@app.websocket("/get-unread-messages")
async def send_unread_messages_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db),
) -> None:
    """
    Send unread messages
    - token [str]
    - group_id [int]

    [in websocket]
    - message

    output:
     - None
    """
    token = websocket.query_params.get("token")
    group_id = websocket.query_params.get("group_id")
    if token and group_id:
        user = await get_current_user(user_db=db, token=token)
        group_id = int(group_id)
    else:
        return await websocket.close(reason="You're not allowed", code=4403)
    is_group_member = await group_membership_check(
        group_id=group_id,
        db=db,
        user=user,
    )
    if not is_group_member:
        return await websocket.close(reason="You're not allowed", code=4403)
    if user:
        if user.id in websocket_connections:
            logger.error(
                "User %s Has More Than 1 Websocket With Group id : %s",
                user.username,
                group_id,
            )
            return await websocket.close(reason="You're not allowed", code=4403)
        websocket_connections[user.id] = websocket
        await websocket.accept()
        try:
            await send_unread_messages(websocket, user, group_id, db)
        except (WebSocketDisconnect, RuntimeError):
            pass
    else:
        return await websocket.close()


async def send_unread_messages(
    websocket: WebSocket,
    user: User,
    group_id: int,
    db: Session = Depends(get_db),
):
    """send unread messages to client"""
    while True:
        db.refresh(user)
        all_unread_messages = user.unread_messages
        unread_messages_group = []
        if all_unread_messages:
            unread_messages_group = [
                un_mes
                for un_mes in all_unread_messages
                if str(un_mes.group_id) == str(group_id)
            ]
        if unread_messages_group:
            for unread_message in unread_messages_group:
                message = unread_message.message
                message = {
                    "text": message.text,
                    "sender_name": message.sender_name,
                    "id": message.id,
                    "type": "Text",
                    "datetime": str(message.created_at),
                }
                await websocket.send_text(json.dumps(message))
                db.delete(unread_message)
            db.commit()
        else:
            try:
                await asyncio.wait_for(websocket.receive(), timeout=0.7)
                continue
            except asyncio.TimeoutError:
                continue
            except (WebSocketDisconnect, RuntimeError):
                if websocket_connections[user.id]:
                    websocket_connections.pop(user.id)
                break


async def broadcast_changes(
    group_id: int,
    change_type: models.ChangeType,
    db: Session,
    message_id: int | None = None,
    new_text: str | None = None,
) -> None:
    """
    broadcast changes to all online users on that group
    - group_id [int]
    - change_type [str]
    - message_id [int]
    - new_text [str]

    output:
    - None
    """
    group = await get_group_by_id(db=db, group_id=group_id)
    if group:
        changed_value = {
            "type": change_type,
            "id": message_id,
            "new_text": new_text,
        }
        online_users = set(websocket_connections.keys())
        await asyncio.gather(
            *[
                send_change_to_user(
                    member.user.id, changed_value, online_users=online_users
                )
                for member in group.members
            ]
        )


async def send_change_to_user(
    user_id: int, change_data: dict, online_users: set
) -> None:
    """
    send changes for online users
    - user_id [int]
    - change_data [dict]
    - online_users [set]

    output:
    - None
    """
    if user_id in online_users:
        connection = websocket_connections[
            user_id
        ]  # TODO this thing send changes to all users and this isn't good
        await connection.send_text(json.dumps(change_data))
