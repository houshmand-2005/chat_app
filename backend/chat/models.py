from enum import Enum
from datetime import datetime
from fastapi import WebSocket
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import relationship
from chat.database import Base


class UserRole(str, Enum):
    admin = "admin"
    member = "member"


class ChangeType(str, Enum):
    Edit = "Edit"
    Delete = "Delete"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    display_name = Column(String)
    email = Column(String, unique=True, index=True)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.member, nullable=False)
    bio = Column(String, default="")
    disabled = Column(Boolean, default=False)
    profile_pic = Column(String, default="")
    groups = relationship("GroupMember", back_populates="user")
    messages = relationship("Message", back_populates="sender")
    unread_messages = relationship("UnreadMessage", back_populates="user")
    websocket = None


class UnreadMessage(Base):
    __tablename__ = "unread_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_name = Column(String)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)

    user = relationship("User", back_populates="unread_messages")
    message = relationship("Message", back_populates="unread_for")


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    members = relationship("GroupMember", back_populates="group")
    messages = relationship("Message", back_populates="group")


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.member, nullable=False)

    user = relationship("User", back_populates="groups")
    group = relationship("Group", back_populates="members")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    sender_id = Column(Integer, ForeignKey("users.id"))
    sender_name = Column(String)
    group_id = Column(Integer, ForeignKey("groups.id"))

    sender = relationship("User", back_populates="messages")
    group = relationship("Group", back_populates="messages")
    unread_for = relationship("UnreadMessage", back_populates="message")


class Changes(Base):
    __tablename__ = "changes"

    id = Column(Integer, primary_key=True, index=True)
    new_text = Column(String)
    original_text = Column(String)
    changes_type = Column(
        SQLAlchemyEnum(ChangeType), default=ChangeType.Edit, nullable=False
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    sender_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
