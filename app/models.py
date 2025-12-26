from .extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # change to password_hash later
    password = db.Column(db.String(200), nullable=False) 

    def __repr__(self) -> str:
        return f"<User {self.id} {self.username}>"
    
     
    
