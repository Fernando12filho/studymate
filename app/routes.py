from flask import Blueprint, render_template
from .extensions import db
from .models import User

bp = Blueprint("main", __name__)

@bp.get("/dev/seed")
def dev_seed():
    c = User(name="TPM", email="fgmelofilho@gmail.com", phone="000-000-0000")
    db.session.add(c)
    db.session.commit()
    return f"Inserted contact id={c.id}"


@bp.get("/")
def home():
    return render_template("index.html")