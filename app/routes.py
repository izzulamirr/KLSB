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
        try:
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

            # Ensure upload folder exists and is writable
            upload_folder = current_app.config.get("UPLOAD_FOLDER")
            try:
                os.makedirs(upload_folder, exist_ok=True)
            except Exception:
                current_app.logger.exception("Failed to create upload folder, will try system tempdir as fallback")
                # fall back to system temp dir
                import tempfile
                upload_folder = tempfile.gettempdir()

            # Save the uploaded file
            filename = secure_filename(file.filename)
            save_path = os.path.join(upload_folder, filename)
            try:
                # check write permission; if not writable, fall back to tempdir
                if not os.access(upload_folder, os.W_OK):
                    import tempfile
                    fallback = tempfile.gettempdir()
                    current_app.logger.warning("Configured upload folder not writable, using tempdir: %s", fallback)
                    upload_folder = fallback
                    save_path = os.path.join(upload_folder, filename)
                file.save(save_path)
            except Exception:
                current_app.logger.exception("Failed to save uploaded file even after fallback")
                # Show a friendly error message to the user
                return render_template("services/send_cv.html", errors=["Unable to save uploaded file. Please try again or contact support."])

            # Persist to database (if configured)
            try:
                from . import db
                from .models import Applicant
                from datetime import datetime
                # Parse availability date if provided
                avail_date = None
                if availability:
                    try:
                        avail_date = datetime.strptime(availability, "%Y-%m-%d").date()
                    except Exception:
                        avail_date = None

                applicant = Applicant(
                    full_name=full_name,
                    email=request.form.get('email','').strip(),
                    position=position,
                    availability=avail_date,
                    filename=filename
                )
                db.session.add(applicant)
                db.session.commit()
            except Exception:
                # If DB isn't available or commit fails, continue without blocking the UX
                current_app.logger.exception("Failed to persist applicant to database")

            return render_template("services/send_cv_success.html", name=full_name, position=position)
        except Exception as e:
            # Log unexpected exceptions and show a friendly error message instead of a 500
            current_app.logger.exception("Unhandled exception in send-cv handler")
            return render_template("services/send_cv.html", errors=["An internal server error occurred. Please try again later."])

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

@main_bp.route("/about/management")
def about_management():
    return render_template("About Us/about_board.html", page_class="home-page center-content")

@main_bp.route("/about/affiliations")
def about_affiliations():
    return render_template("About Us/about_affiliations.html", page_class="home-page center-content")

@main_bp.route('/about/focus')
def about_focus():
    return render_template('About Us/about_focus.html', page_class="home-page center-content")


# Dev-only: list applicants saved to the database so you can verify persistence
@main_bp.route('/admin/applicants')
def admin_applicants():
    from flask import current_app
    # Only enable this page in debug mode to avoid exposing data in production
    if not current_app.debug:
        return ("Not Found", 404)
    try:
        from .models import Applicant
        applicants = Applicant.query.order_by(Applicant.created_at.desc()).all()
    except Exception:
        current_app.logger.exception('Failed to load applicants')
        applicants = []
    return render_template('admin_applicants.html', applicants=applicants)

@main_bp.route('/about/license-registration')
def about_license_registration():
    return render_template('About Us/about_license.html', page_class="home-page center-content")

@main_bp.route("/healthz")
def healthz():
    return jsonify(status="ok")

@main_bp.route("/get-in-touch", methods=["GET", "POST"])
def get_in_touch():
    from flask import request, flash
    errors = []
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        company = request.form.get("company", "").strip()
        services = request.form.getlist("services")
        remarks = request.form.get("remarks", "").strip()
        if not email:
            errors.append("Email is required.")
        if not company:
            errors.append("Company name is required.")
        if not services:
            errors.append("Please select at least one core service.")
        if errors:
            return render_template("get_in_touch.html", errors=errors, form=request.form)
        # In a real app, save or send the data here
        return render_template("get_in_touch.html", success=True)
    return render_template("get_in_touch.html")
