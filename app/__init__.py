import os
from flask import Flask, render_template
from .config import Config, BASE_DIR
from .extensions import db
from flask_login import LoginManager, login_required, current_user

login_manager = LoginManager()

def create_app(config_class: type = Config):
    # Debug BEFORE creating app
    print(f"\n=== BEFORE APP CREATION ===")
    print(f"Config class DB URI: {config_class.SQLALCHEMY_DATABASE_URI}")
    print(f"Config class _db_path: {config_class._db_path}")
    
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_class)
    
    # Debug: Print database configuration AFTER loading config
    print(f"\n=== AFTER APP INITIALIZATION ===")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '').replace('sqlite:////', '/')
    print(f"Database Path: {db_path}")
    print(f"DB exists: {os.path.exists(db_path)}")
    if os.path.exists(db_path):
        print(f"DB readable: {os.access(db_path, os.R_OK)}")
        print(f"DB writable: {os.access(db_path, os.W_OK)}")
    print(f"=== END DEBUG ===\n")
    
    # Create necessary directories
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    db.init_app(app)
    @app.get("/health")
    def health():
        return "ok", 200
    
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    @app.route("/dashboard")
    @login_required
    def dashboard():
        from .models import Topic
        all_topic = Topic.query.filter_by(user_id=current_user.id, parent_topic_id=None).order_by(Topic.created_at.desc()).all()
        return render_template("dashboard.html", all_topic=all_topic, current_topic=None, active_panel='topic')
        
    from .routes import bp
    app.register_blueprint(bp)

    from .auth import bp as auth
    app.register_blueprint(auth)
    
    from .topic import bp as topic
    app.register_blueprint(topic)

    from .note import bp as note
    app.register_blueprint(note)

    from .resource import bp as resource
    app.register_blueprint(resource)

    from .chat import bp as chat
    app.register_blueprint(chat)

    return app