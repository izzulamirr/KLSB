from flask import Blueprint, render_template, jsonify, redirect, url_for, request, current_app
import os, secrets
from werkzeug.utils import secure_filename
from sqlalchemy import inspect, insert
from datetime import datetime

from app import db
from app.models import Applicant

# ---------------- BLUEPRINT ----------------
main_bp = Blueprint("main", __name__)

# ---------------- BASIC PAGES ----------------
@main_bp.route("/")
def index():
    return render_template("index.html", page_class="home-page center-content")

@main_bp.route("/profile")
def profile():
    return redirect(url_for('main.about_overview'))

@main_bp.route("/projects")
def projects():
    return render_template("projects.html", page_class="home-page center-content")

@main_bp.route("/services", endpoint="services_page")
def services_page():
    return render_template("services.html", page_class="home-page center-content")


# ------------------- SEND CV -------------------
@main_bp.route("/services/manpower/send-cv", methods=["GET", "POST"])
def services_manpower_send_cv():
    if request.method == "GET":
        return render_template("services/send_cv.html", form=None, errors=None)

    errors = []
    full_name    = (request.form.get("full_name") or "").strip()
    email        = (request.form.get("email") or "").strip()
    position     = (request.form.get("position") or "").strip()
    availability = (request.form.get("availability") or "").strip()
    file         = request.files.get("cv_file")

    # --- Validation ---
    for label, val in [("Full name", full_name), ("Email", email),
                       ("Position", position), ("Availability date", availability)]:
        if not val:
            errors.append(f"{label} is required.")
    if not file or file.filename == "":
        errors.append("Please attach a CV file.")
    else:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in {".pdf", ".doc", ".docx"}:
            errors.append("Only PDF, DOC, or DOCX are allowed.")

    if errors:
        return render_template("services/send_cv.html", errors=errors, form=request.form), 400

    # --- Handle Upload Folder ---
    upload_folder = current_app.config.get("UPLOAD_FOLDER") or os.path.join(current_app.root_path, "uploads", "cv")
    try:
        os.makedirs(upload_folder, exist_ok=True)
    except Exception:
        current_app.logger.exception("Failed to create upload folder, fallback to tmp")
        import tempfile
        upload_folder = tempfile.gettempdir()

    safe_orig = secure_filename(file.filename)
    rand = secrets.token_hex(8)
    _, ext = os.path.splitext(safe_orig)
    saved_name = f"{rand}{ext.lower()}"
    saved_path = os.path.join(upload_folder, saved_name)
    try:
        file.save(saved_path)
    except Exception:
        current_app.logger.exception("Failed to save uploaded file")
        return render_template("services/send_cv.html",
                               errors=["Unable to save uploaded file. Please try again or contact support."],
                               form=request.form), 500

    # --- Insert into DB ---
    try:
        insp = inspect(db.engine)
        db_url = str(db.engine.url)

        if not insp.has_table("applicants"):
            return render_template("services/send_cv.html",
                                   errors=[f"DB ERROR: table 'applicants' does not exist on {db_url}"],
                                   form=request.form), 500

        db_cols = {c["name"] for c in insp.get_columns("applicants")}
        rel_path = os.path.relpath(saved_path, start=current_app.root_path).replace("\\", "/")

        candidate_row = {
            "full_name": full_name,
            "email": email,
            "position": position,
            "availability": availability,
            "filename": safe_orig,
            "file_path": rel_path,
            "created_at": datetime.utcnow(),
        }
        row = {k: v for k, v in candidate_row.items() if k in db_cols}

        stmt = insert(Applicant.__table__).values(**row)
        db.session.execute(stmt)
        db.session.commit()
    except Exception as e:
        current_app.logger.exception("Failed to persist applicant to database")
        err = str(getattr(e, "__cause__", None) or e)
        # TEMP: surface DB error to the user for debugging
        return render_template("services/send_cv.html",
                               errors=[f"DB ERROR: {err}"],
                               form=request.form), 500

    # --- Success Page ---
    return render_template("services/send_cv_success.html", name=full_name, position=position)


# ------------------- OTHER SERVICE PAGES -------------------
@main_bp.route("/services/manpower")
def services_manpower():
    return render_template("services/manpower.html", page_class="home-page center-content")

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


# ------------------- CONTACT / ABOUT -------------------
@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    return render_template("contact.html", page_class="home-page center-content")

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

@main_bp.route('/about/license-registration')
def about_license_registration():
    return render_template('About Us/about_license.html', page_class="home-page center-content")


# ------------------- ADMIN / DEBUG -------------------
@main_bp.route('/admin/applicants')
def admin_applicants():
    if not current_app.debug:
        return ("Not Found", 404)
    try:
        applicants = Applicant.query.order_by(Applicant.created_at.desc()).all()
    except Exception:
        current_app.logger.exception('Failed to load applicants')
        applicants = []
    return render_template('admin_applicants.html', applicants=applicants)

@main_bp.route("/debug/db")
def debug_db():
    """Temporary diagnostic route to verify DB connectivity and schema."""
    try:
        insp = inspect(db.engine)
        return jsonify(
            ok=True,
            url=str(db.engine.url),
            has_applicants=insp.has_table("applicants"),
            columns=[c["name"] for c in insp.get_columns("applicants")] if insp.has_table("applicants") else [],
        )
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


# ------------------- HEALTH -------------------
@main_bp.route("/healthz")
def healthz():
    return jsonify(status="ok")

# ------------------- REQUEST PROPOSAL PAGE -------------------
@main_bp.route("/proposal", methods=["GET", "POST"])
def submit_proposal():
    from app.models import Proposal
    from app import db

    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip()
        client_email = request.form.get("client_email", "").strip()
        proposal_details = request.form.get("proposal_details", "").strip()
        service = request.form.get("service", "").strip()

        errors = []
        if not company_name:
            errors.append("Company name is required.")
        if not client_email:
            errors.append("Email is required.")
        if not proposal_details:
            errors.append("Proposal details are required.")
        if not service:
            errors.append("Service selection is required.")

        if errors:
            return render_template("Proposal.html", errors=errors, form=request.form)

        # ✅ Save to database
        try:
            new_proposal = Proposal(
                company_name=company_name,
                client_email=client_email,
                proposal_details=proposal_details,
                service=service
            )
            db.session.add(new_proposal)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Failed to save proposal to database")
            return render_template(
                "Proposal.html",
                errors=["An error occurred while saving your proposal. Please try again later."],
                form=request.form
            )

        return render_template("proposal_success.html", name=company_name)

    # GET — show form
    return render_template("Proposal.html")



