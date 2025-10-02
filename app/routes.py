from flask import Blueprint, render_template, jsonify, redirect, url_for

# Use a Blueprint (factory-friendly)
main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("index.html", page_class="home-page center-content")

@main_bp.route("/profile")
def profile():
    # Legacy redirect to About overview
    return redirect(url_for('main.about_overview'))

@main_bp.route("/projects")
def projects():
    return render_template("projects.html", page_class="home-page center-content")

@main_bp.route("/services")
def services():
    return render_template("services.html", page_class="home-page center-content")

@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    # Placeholder: on POST you could process form data / send email
    return render_template("contact.html", page_class="home-page center-content")

# New routes to satisfy tests
@main_bp.route("/about/overview")
def about_overview():
    return render_template("about_overview.html", page_class="home-page center-content")

@main_bp.route("/about/history")
def about_history():
    return render_template("About Us/about_history.html", page_class="home-page center-content")

@main_bp.route("/about/board")
def about_board():
    return render_template("About Us/about_board.html", page_class="home-page center-content")

@main_bp.route("/about/affiliations")
def about_affiliations():
    return render_template("About Us/about_affiliations.html", page_class="home-page center-content")

@main_bp.route('/about/focus')
def about_focus():
    return render_template('About Us/about_focus.html', page_class="home-page center-content")

@main_bp.route("/healthz")
def healthz():
    return jsonify(status="ok")

@main_bp.route('/services/manpower')
def services_manpower():
    return render_template('Services/manpower.html')

@main_bp.route('/services/engineering')
def services_engineering():
    return render_template('Services/engineering.html')

@main_bp.route('/services/digital')
def services_digital():
    return render_template('Services/digital.html')

@main_bp.route('/services/inspection')
def services_inspection():
    return render_template('Services/inspection.html')

@main_bp.route('/services/construction')
def services_construction():
    return render_template('Services/construction.html')

@main_bp.route('/services/supply')
def services_supply():
    return render_template('Services/supply.html')