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

# Services (list page) — endpoint is services_page so url_for('main.services_page') works
@main_bp.route("/services", endpoint="services_page")
def services_page():
    return render_template("services.html", page_class="home-page center-content")

# --- Service detail pages (UNIQUE function names + lowercase template folders) ---

@main_bp.route("/services/manpower")
def services_manpower():
    return render_template("services/manpower.html", page_class="home-page center-content")


# Send CV form (GET shows form, POST handles submission and file upload)
@main_bp.route("/services/manpower/send-cv", methods=["GET", "POST"])
def services_manpower_send_cv():
    from flask import request, current_app, redirect, url_for, flash
    import os
    from werkzeug.utils import secure_filename

    if request.method == "POST":
        # Basic form validation
        full_name = request.form.get("full_name", "").strip()
        position = request.form.get("position", "").strip()
        availability = request.form.get("availability", "").strip()
        file = request.files.get("cv_file")

        errors = []
        if not full_name:
            errors.append("Full name is required")
        if not position:
            errors.append("Position is required")
        if not availability:
            errors.append("Availability date is required")
        if not file or file.filename == "":
            errors.append("Please attach a CV file")

        if errors:
            # Re-render form with errors
            return render_template("services/send_cv.html", errors=errors, form=request.form)

        # Save the uploaded file
        filename = secure_filename(file.filename)
        save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)

        # In a real app you'd persist applicant data, send an email, etc.
        return render_template("services/send_cv_success.html", name=full_name, position=position)

    # GET
    return render_template("services/send_cv.html")

@main_bp.route("/services/inspection")
def services_inspection():
    return render_template("services/inspection.html", page_class="home-page center-content")

@main_bp.route("/services/construction")
def services_construction():
    return render_template("services/construction.html", page_class="home-page center-content")

@main_bp.route("/services/supply")
def services_supply():
    return render_template("services/supply.html", page_class="home-page center-content")

@main_bp.route("/services/engineering")
def services_engineering():
    return render_template("services/engineering.html", page_class="home-page center-content")

@main_bp.route("/services/digital")
def services_digital():
    return render_template("services/digital.html", page_class="home-page center-content")

# Contact
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

@main_bp.route('/about/license-registration')
def about_license_registration():
    return render_template('About Us/about_license.html', page_class="home-page center-content")

@main_bp.route("/healthz")
def healthz():
    return jsonify(status="ok")
