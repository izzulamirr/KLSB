# app/__init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import ProdConfig  # switch to DevConfig for local testing

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Load config (Prod for live; use DevConfig during local tests)
    app.config.from_object(ProdConfig)

    # Init DB
    db.init_app(app)

    # Helpful defaults
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    # Uploads (project-level /uploads)
    project_root = os.path.abspath(os.path.join(app.root_path, ".."))
    upload_folder = os.path.join(project_root, "uploads", "cv")
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

    # Register routes
    from .routes import main_bp
    app.register_blueprint(main_bp)

    # Ensure models are registered
    try:
        from . import models  # noqa: F401
    except Exception as e:
        app.logger.warning(f"Model import warning: {e}")

    return app
