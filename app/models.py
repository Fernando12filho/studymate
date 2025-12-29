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
    subtopics = relationship("Topic", backref=db.backref('parent_topic', remote_side=[id]), cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Topic {self.id} {self.name}>"
    
    def is_subtopic(self):
        """Check if this topic is a subtopic"""
        return self.parent_topic_id is not None

    

