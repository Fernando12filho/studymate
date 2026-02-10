import functools
import re
import os
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
)
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User
from sqlalchemy.exc import IntegrityError
from .extensions import db
from sqlalchemy import text
from flask_login import login_user, logout_user

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
     print(f"\n=== LOGIN ROUTE HIT === Method: {request.method}")
     print(f"Current working directory: {os.getcwd()}")
     print(f"DB URI: {current_app.config['SQLALCHEMY_DATABASE_URI']}")
     
     errors = []
     if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        
        if not email:
            errors.append("Email is required")
        if not password:
            errors.append("Password is required")
        if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            errors.append("Enter a valid email address")      
        
        if not errors:
            try:
                user = User.query.filter_by(email=email).first()
                if not user or not check_password_hash(user.password, password):
                    errors.append("Invalid email or password")
                else:
                    login_user(user)
                    return redirect(url_for("dashboard"))
            except Exception as e:
                current_app.logger.error(f"Login error: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                errors.append("An error occurred. Please try again.")

        
        return render_template("index.html", errors=errors)
     
     if request.method == "GET":
         return render_template("index.html")

@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.home"))

@bp.route("/health/db")
def health_db():
    try:
        db.session.execute(text("SELECT 1"))
        return {"db": "ok"}, 200
    except Exception as e:
        return {"db": "error", "detail": str(e)}, 500
    
