import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from config import ProdConfig  # switch to DevConfig for local testing

db = SQLAlchemy()
mail = Mail()

def create_app():
    app = Flask(__name__)

    # Load config (Prod for live; use DevConfig during local tests)
    app.config.from_object(ProdConfig)

    # Init DB
    db.init_app(app)
    
    # Init Mail
    mail.init_app(app)

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

    # Global template context: open jobs count for floating badge
    @app.context_processor
    def inject_open_jobs_count():
        from flask import has_request_context
        if not has_request_context():
            return {"open_jobs_count": 0}
        try:
            # Local import to avoid circular dependency at import time
            from .models import JobListing
            count = JobListing.query.filter_by(is_active=True).count()
        except Exception:
            # On DB errors, fail gracefully
            count = 0
        return {"open_jobs_count": count}

    return app
