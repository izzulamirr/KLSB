from flask import Flask


def create_app(config_object: str | None = None):
    app = Flask(__name__)

    if config_object:
        app.config.from_object(config_object)

    # Simple configuration default
    app.config.setdefault("APP_NAME", "KLSB Draft Site")

    # Register blueprints / routes
    from .routes import main_bp
    app.register_blueprint(main_bp)

    @app.errorhandler(404)
    def not_found(e):  # pragma: no cover - simple handler
        return ("Page not found", 404)

    return app
