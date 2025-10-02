from flask import Flask
import os


def create_app():
    app = Flask(__name__)  # factory pattern

    # (Optional but helpful in dev)
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
