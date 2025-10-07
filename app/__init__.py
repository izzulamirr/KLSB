from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from config import ProdConfig

db = SQLAlchemy()  # Create SQLAlchemy instance

def create_app():
    app = Flask(__name__)

    # Load production config
    app.config.from_object(ProdConfig)

    # Initialize database
    db.init_app(app)

    # (Optional but helpful)
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    # Uploads config (saving to project-level uploads/ folder)
    project_root = os.path.abspath(os.path.join(app.root_path, ".."))
    upload_folder = os.path.join(project_root, "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB limit

    # Register routes blueprint
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
