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
        # examples: "pdf", "link", "video", "image"
    )

    url: Mapped[str | None] = mapped_column(db.Text)
    file_path: Mapped[str | None] = mapped_column(db.Text)

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
    topic = relationship("Topic", backref="resources")

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


