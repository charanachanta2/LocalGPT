from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


# ============================================================
# USER
# ============================================================

class User(db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    chats = db.relationship(
        "Chat",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    api_keys = db.relationship(
        "APIKey",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )


# ============================================================
# CHAT
# ============================================================

class Chat(db.Model):

    __tablename__ = "chats"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    title = db.Column(
        db.String(200),
        nullable=False,
        default="New Chat"
    )

    model = db.Column(
        db.String(100),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    messages = db.relationship(
        "Message",
        backref="chat",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="Message.id"
    )


# ============================================================
# MESSAGE
# ============================================================

class Message(db.Model):

    __tablename__ = "messages"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    chat_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "chats.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    model = db.Column(
        db.String(100),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )


# ============================================================
# API KEY
# ============================================================

class APIKey(db.Model):

    __tablename__ = "api_keys"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    key_prefix = db.Column(
        db.String(20),
        nullable=False
    )

    key_hash = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
        index=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    last_used_at = db.Column(
        db.DateTime,
        nullable=True
    )

    revoked = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )