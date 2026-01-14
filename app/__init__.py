import os
from flask import Flask, render_template
from app.models import User
from .config import Config, BASE_DIR
from .extensions import db
from flask_login import LoginManager, login_required, current_user

login_manager = LoginManager()

def create_app(config_class: type = Config):
    app = Flask(__name__, instance_relative_config=True, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_class)
    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    @app.get("/health")
    def health():
        return "ok", 200
    
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.route("/dashboard")
    @login_required
    def dashboard():
        from .models import Topic
        all_topics = Topic.query.filter_by(user_id=current_user.id, parent_topic_id=None).order_by(Topic.created_at.desc()).all()
        return render_template("dashboard.html", all_topics=all_topics, current_topic=None, active_panel='topics')
        
    from .routes import bp
    app.register_blueprint(bp)

    from .auth import bp as auth
    app.register_blueprint(auth)
    
    from .topic import bp as topics
    app.register_blueprint(topics)

    return app