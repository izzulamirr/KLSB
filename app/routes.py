from flask import Blueprint, render_template, current_app

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("index.html", title="Home")

@main_bp.route("/about")
def about():
    return render_template("about.html", title="About")

@main_bp.route("/services")
def services():
    return render_template("Services.html", title="Services")

@main_bp.route("/healthz")
def healthz():
    return {"status": "ok", "app": current_app.config.get("APP_NAME", "site")}
