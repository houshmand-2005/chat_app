from sqlalchemy.orm import Session
from functools import lru_cache
from chat import models
from chat import schema
from chat.utils.jwt import get_password_hash


async def create_user_controller(
    db: Session,
    user: schema.CreateUser,
) -> models.User | None:
    existing_user = (
        db.query(models.User).filter(models.User.username == user.username).first()
    )
    if existing_user:
        return None
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        password=hashed_password,
        email=user.email,
        display_name=user.full_name,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


async def create_group_controller(
    db: Session, group: schema.GroupCreate
) -> models.Group:
    new_group = models.Group(address=group.address, name=group.name)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group


async def create_message_controller(
    db: Session, user: models.User, group_id: int, text: str
) -> models.Message:
    message = models.Message(
        text=text, sender_id=user.id, sender_name=user.username, group_id=group_id
    )
    db.add(message)
    db.commit()
    return message


async def create_unread_message_controller(
    db: Session,
    user: schema.CreateUser,
    message: models.Message,
    group_id: int,
) -> models.UnreadMessage:
    unread_message = models.UnreadMessage(
        user_id=user.id,
        user_name=user.username,
        message_id=message.id,
        group_id=group_id,
    )
    db.add(unread_message)
    db.commit()
    return unread_message


async def group_membership_check(
    group_id: int, db: Session, user: schema.User
) -> models.GroupMember | None:
    return (
        db.query(models.GroupMember)
        .filter(
            models.GroupMember.group_id == group_id,
            models.GroupMember.user_id == user.id,
        )
        .first()
    )


async def group_members_by_id(
    group_id: int,
    db: Session,
) -> list[models.User]:
    return (
        db.query(models.User)
        .join(models.GroupMember)
        .filter(models.GroupMember.group_id == group_id)
        .all()
    )


async def get_group_by_id(
    group_id: int,
    db: Session,
) -> models.Group:
    return db.query(models.Group).filter_by(id=group_id).first()


async def get_group_by_address(
    address: str,
    db: Session,
) -> models.Group:
    return db.query(models.Group).filter_by(address=address).first()


async def join_member_to_group(
    db: Session,
    user: schema.User,
    group: models.Group,
    role: schema.UserRole = schema.UserRole.member,
):
    group_member = models.GroupMember(
        user_id=user.id,
        group_id=group.id,
        role=role,
    )
    db.add(group_member)
    db.commit()


async def get_user_by_id(
    user_id: int,
    db: Session,
) -> models.User:
    return db.query(models.User).filter(models.User.id == user_id).first()


async def get_user_groups_by_id(
    user_id: int,
    db: Session,
) -> list[models.Group]:
    return (
        db.query(models.Group)
        .join(models.GroupMember)
        .filter(models.GroupMember.user_id == user_id)
        .all()
    )


async def get_message_by_id(
    message_id: int,
    user_id: int,
    db: Session,
) -> models.Message | None:
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if message and user_id == message.sender_id:
        return message
    return None


async def get_reads_messages(
    group_id: int,
    user: schema.User,
    db: Session,
) -> list[models.Message] | None:
    unread_message_ids = [
        unread_message.message_id for unread_message in user.unread_messages
    ]
    messages = (
        db.query(models.Message)
        .filter(models.Message.group_id == group_id)
        .filter(models.Message.id.notin_(unread_message_ids))
        .order_by(models.Message.id)
        .all()
    )
    return messages


async def get_first_unread_message_group(
    group_id: int,
    user: schema.User,
    db: Session,
) -> models.Message | None:
    first_unread_message = (
        db.query(models.Message)
        .join(models.UnreadMessage)
        .filter(
            models.Message.group_id == group_id,
            models.UnreadMessage.user_id == user.id,
        )
        .order_by(models.Message.id)
        .first()
    )
    return first_unread_message


async def create_change_controller(
    db: Session,
    new_text: str,
    original_text: str,
    changes_type: models.ChangeType,
    sender_id: int,
    group_id: int,
) -> models.Changes:
    change = models.Changes(
        new_text=new_text,
        original_text=original_text,
        changes_type=changes_type,
        sender_id=sender_id,
        group_id=group_id,
    )
    db.add(change)
    db.commit()
    return change


async def get_changes_by_group(
    db: Session,
    group_id: int,
) -> list[models.Changes] | None:
    change = db.query(models.Changes).filter(models.Changes.group_id == group_id).all()
    return change


async def delete_changes_by_group(
    db: Session,
    group_id: int,
) -> None:
    db.query(models.Changes).filter(models.Changes.group_id == group_id).delete()
