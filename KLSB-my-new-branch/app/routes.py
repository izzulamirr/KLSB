from flask import Blueprint, render_template, jsonify

# Use a Blueprint (factory-friendly)
main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("index.html", page_class="home-page center-content")

@main_bp.route("/profile")
def profile():
    return render_template("profile.html", page_class="home-page center-content")

@main_bp.route("/projects")
def projects():
    return render_template("projects.html", page_class="home-page center-content")

@main_bp.route("/services")
def services():
    return render_template("services.html", page_class="home-page center-content")

# New routes to satisfy tests
@main_bp.route("/about")
def about():
    return render_template("about.html", page_class="home-page center-content")

@main_bp.route("/healthz")
def healthz():
    return jsonify(status="ok")
