from flask import Flask

def create_app():
    app = Flask(__name__)  # factory pattern

    # (Optional but helpful in dev)
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    # Register routes blueprint
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
