import functools
import re
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User
from sqlalchemy.exc import IntegrityError
from .extensions import db
from sqlalchemy import text
from flask_login import login_user

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route("/register", methods=['GET', 'POST'])
def register():

    errors = []
    if request.method == 'GET':
        return render_template("register.html")
    
    # POST requests
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")
    confirm_password = request.form.get("confirm_password")
    
    # Add validation and user creation logic here
    if not (3 <= len(username) <= 80):
        errors.append("Username must be between 3 and 80 characters")

    # Regular expression
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        errors.append("Enter a valid email address")
    if len(password) < 6:
        errors.append("Password needs to be at least 6 characters")

    if password != confirm_password:
        errors.append("Passwords do not match")

    if not errors:
        try:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('main.home'))
        except IntegrityError:
            db.session.rollback()
            errors.append("That username or email is already registered")
    
    return render_template("register.html", errors=errors)


# Finish login and correct register route
@bp.route("/login", methods=['GET', 'POST'])
def login():
     errors = []
     if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        
        if not email:
            errors.append("Email is required")
        if not password:
            errors.append("Password is required")
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            errors.append("Enter a valid email address")      
        if not errors:
            user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            errors.append("Invalid email or password")
        else:
            login_user(user)
            return redirect(url_for("dashboard"))
        return render_template("index.html", errors=errors)

@bp.route("/logout")
def logout():
    return redirect(url_for("main.home"))

@bp.route("/health/db")
def health_db():
    try:
        db.session.execute(text("SELECT 1"))
        return {"db": "ok"}, 200
    except Exception as e:
        return {"db": "error", "detail": str(e)}, 500