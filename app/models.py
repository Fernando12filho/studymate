from .extensions import db

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) 
    phone = db.Column(db.String(120), nullable=False)  

    def __repr__(self) -> str:
        return f"<Contect {self.id} {self.name}>"