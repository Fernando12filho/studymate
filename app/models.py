from .extensions import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(db.Model, UserMixin):
    __tablename__ = "user_table"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    
    # Relationships
    topics = relationship("Topic", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User {self.id} {self.username}>"
       
class Topic(db.Model):
    __tablename__ = "topic"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # User relationship (owner of the topic)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_table.id"), nullable=False)
    user = relationship("User", back_populates="topics")
    
    # Parent topic relationship (for subtopics)
    parent_topic_id: Mapped[int | None] = mapped_column(ForeignKey("topic.id"), nullable=True)
    subtopics: Mapped[list["Topic"]] = relationship(
        cascade="all, delete-orphan",
        backref=db.backref("parent_topic", remote_side=[id])
    )
    def __repr__(self) -> str:
        return f"<Topic {self.id} {self.name}>"
    
    def is_subtopic(self):
        """Check if this topic is a subtopic"""
        return self.parent_topic_id is not None
    
class Resource(db.Model):
    __tablename__ = "resource"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(db.String(200), nullable=False)

    resource_type: Mapped[str] = mapped_column(
        db.String(50),
        nullable=False
        # "pdf" or "link"
    )

    # For links
    url: Mapped[str | None] = mapped_column(db.Text)
    
    # For PDF files
    file_path: Mapped[str | None] = mapped_column(db.Text)
    file_size: Mapped[int | None] = mapped_column(db.Integer)
    original_filename: Mapped[str | None] = mapped_column(db.String(255))

    status: Mapped[str] = mapped_column(db.String(20), default="active")

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Ownership
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_table.id"),
        nullable=False,
        index=True
    )

    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topic.id"),
        nullable=False,
        index=True
    )

    user = relationship("User")
    topic = relationship("Topic", backref="resources")

    def is_pdf(self) -> bool:
        """Check if resource is a PDF file"""
        return self.resource_type == "pdf" and self.file_path is not None
    
    def is_link(self) -> bool:
        """Check if resource is a URL link"""
        return self.resource_type == "link" and self.url is not None

class Note(db.Model):
    __tablename__ = "note"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    content: Mapped[str] = mapped_column(db.Text, nullable=False)

    is_ai_generated: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now,
        onupdate=datetime.now
    )

    # Ownership
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_table.id"),
        nullable=False,
        index=True
    )

    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topic.id"),
        nullable=False,
        index=True
    )

    user = relationship("User")
    topic = relationship("Topic", backref="notes")

class Flashcard(db.Model):
    __tablename__ = "flashcard"

    id: Mapped[int] = mapped_column(primary_key=True)

    question: Mapped[str] = mapped_column(db.Text, nullable=False)
    answer: Mapped[str] = mapped_column(db.Text, nullable=False)

    difficulty: Mapped[int] = mapped_column(default=1)
    # 1 = easy, 5 = hard

    last_reviewed_at: Mapped[datetime | None]
    next_review_at: Mapped[datetime | None]

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Ownership
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_table.id"),
        nullable=False,
        index=True
    )

    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topic.id"),
        nullable=False,
        index=True
    )

    user = relationship("User")
    topic = relationship("Topic", backref="flashcards")


# ===== CHAT MODELS =====

# Association tables for many-to-many relationships
message_notes = db.Table('message_notes',
    db.Column('message_id', db.Integer, db.ForeignKey('chat_message.id'), primary_key=True),
    db.Column('note_id', db.Integer, db.ForeignKey('note.id'), primary_key=True)
)

message_resources = db.Table('message_resources',
    db.Column('message_id', db.Integer, db.ForeignKey('chat_message.id'), primary_key=True),
    db.Column('resource_id', db.Integer, db.ForeignKey('resource.id'), primary_key=True)
)

class Conversation(db.Model):
    __tablename__ = "conversation"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    title: Mapped[str | None] = mapped_column(db.String(200))
    # Auto-generated from first message or manually set

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Ownership
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_table.id"),
        nullable=False,
        index=True
    )

    # Optional: Link conversation to a specific topic
    topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("topic.id"),
        nullable=True,
        index=True
    )

    user = relationship("User")
    topic = relationship("Topic", backref="conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Conversation {self.id} {self.title or 'Untitled'}>"


class ChatMessage(db.Model):
    __tablename__ = "chat_message"

    id: Mapped[int] = mapped_column(primary_key=True)

    role: Mapped[str] = mapped_column(db.String(20), nullable=False)
    # "user", "assistant", or "system"

    content: Mapped[str] = mapped_column(db.Text, nullable=False)

    # Token tracking for cost management
    input_tokens: Mapped[int | None] = mapped_column(db.Integer)
    output_tokens: Mapped[int | None] = mapped_column(db.Integer)
    total_tokens: Mapped[int | None] = mapped_column(db.Integer)

    # Model used for this message (assistant only)
    model_used: Mapped[str | None] = mapped_column(db.String(50))

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Foreign keys
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversation.id"),
        nullable=False,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_table.id"),
        nullable=False,
        index=True
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    user = relationship("User")
    
    # Many-to-many relationships for attachments
    attached_notes = relationship("Note", secondary=message_notes, backref="chat_messages")
    attached_resources = relationship("Resource", secondary=message_resources, backref="chat_messages")

    def __repr__(self) -> str:
        return f"<ChatMessage {self.id} {self.role}: {self.content[:30]}...>"
    
    def to_dict(self):
        """Convert message to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'attached_notes': [{'id': n.id, 'title': n.title} for n in self.attached_notes],
            'attached_resources': [{'id': r.id, 'title': r.title} for r in self.attached_resources],
            'tokens': {
                'input': self.input_tokens,
                'output': self.output_tokens,
                'total': self.total_tokens
            } if self.total_tokens else None
        }
