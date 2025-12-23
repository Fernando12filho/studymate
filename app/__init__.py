from flask import Flask 
from .config import Config
from .extensions import db
import os

def create_app(config_class: type = Config):
    app = Flask(__name__, instance_relative_config=True, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_class)
    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    @app.get("/health")
    def health():
        return "ok", 200
    
    @app.get("/")
    def home():
        return "It works", 200
    
    return app