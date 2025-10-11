from flask import Blueprint, render_template, jsonify, redirect, url_for, request, current_app
import os, secrets
from werkzeug.utils import secure_filename
from sqlalchemy import inspect, insert
from datetime import datetime
from io import StringIO, BytesIO
import csv
from flask import Response, send_file, abort
from app import db
from app.models import Applicant
from functools import wraps
from flask import session, flash

# ---------------- BLUEPRINT ----------------
main_bp = Blueprint("main", __name__)

# --- Admin guard decorator ---
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Please log in to access the admin area.", "warning")
            return redirect(url_for("main.admin_login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper

@main_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    admin_user = current_app.config.get("ADMIN_USER")
    admin_pass = current_app.config.get("ADMIN_PASS")

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        next_url = request.args.get("next") or url_for("main.admin_applicants")

        if username == admin_user and password == admin_pass:
            session["is_admin"] = True
            # ✅ ADD THIS LINE
            session.permanent = False  # Session will expire when browser is closed
            flash("Login successful.", "success")
            return redirect(next_url)
        flash("Invalid username or password.", "error")

    return render_template("admin_login.html")

@main_bp.route("/admin/logout", endpoint="admin_logout")
def admin_logout_view():
    session.pop("is_admin", None)
    flash("Logged out.", "info")
    return redirect(url_for("main.admin_login"))

# --- Applicants list (Admin) ---
@main_bp.route("/admin/applicants", endpoint="admin_applicants")
@admin_required
def admin_applicants_view():
    # ✅ Import both Applicant and Proposal models
    from app.models import Applicant, Proposal
    try:
        applicants = Applicant.query.order_by(Applicant.created_at.desc()).all()
        # ✅ Add a query to get all proposals
        proposals = Proposal.query.order_by(Proposal.created_at.desc()).all()
    except Exception:
        current_app.logger.exception("Failed to load applicants or proposals")
        applicants = []
        # ✅ Initialize proposals as an empty list on error
        proposals = []
        
    # ✅ Pass both applicants and proposals to the template
    return render_template("admin_applicants.html", applicants=applicants, proposals=proposals)

# --- Download uploaded CV ---
@main_bp.route("/admin/applicants/<int:applicant_id>/download", endpoint="admin_download_applicant_file")
@admin_required
def admin_download_applicant_file_view(applicant_id):
    from app.models import Applicant
    a = Applicant.query.get_or_404(applicant_id)
    if not a.file_path:
        return ("No file for this applicant.", 404)

    path = a.file_path
    if not os.path.isabs(path):
        path = os.path.join(current_app.root_path, path)
    if not os.path.exists(path):
        return ("File not found on server.", 404)

    download_name = a.filename or os.path.basename(path)
    return send_file(path, as_attachment=True, download_name=download_name)

# --- CSV export ---
@main_bp.route("/admin/applicants/export/csv", endpoint="admin_export_applicants_csv")
@admin_required
def admin_export_applicants_csv_view():
    """Exports applicants as a CSV compatible with Excel (UTF-8 + BOM)."""
    from app.models import Applicant
    from io import StringIO, BytesIO
    import csv
    from datetime import datetime

    # Query applicants newest-first
    rows = Applicant.query.order_by(Applicant.created_at.desc()).all()

    # Use StringIO for CSV writing
    buf = StringIO()
    writer = csv.writer(
        buf,
        quoting=csv.QUOTE_ALL,   # wrap all fields in quotes
        lineterminator="\n"      # consistent newlines for Windows
    )

    # Header row
    writer.writerow([
        "ID", "Full Name", "Email", "Position",
        "Availability", "Filename", "File Path", "Created At (Local Time)"
    ])

    # Convert UTC → Malaysia time (UTC+8)
    from datetime import timedelta
    for a in rows:
        local_time = (
            a.created_at + timedelta(hours=8)
        ).strftime("%Y-%m-%d %H:%M:%S") if a.created_at else ""
        writer.writerow([
            a.id or "",
            a.full_name or "",
            a.email or "",
            a.position or "",
            a.availability or "",
            a.filename or "",
            a.file_path or "",
            local_time
        ])

    # Convert to bytes, add UTF-8 BOM for Excel
    data = ("\ufeff" + buf.getvalue()).encode("utf-8-sig")

    # File name with timestamp
    filename = f"applicants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    # Send response
    from flask import Response
    return Response(
        data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
# --- XLSX export ---
@main_bp.route("/admin/applicants/export/xlsx", endpoint="admin_export_applicants_xlsx")
@admin_required
def admin_export_applicants_xlsx_view():
    from app.models import Applicant
    from flask import Response
    from datetime import datetime, timedelta

    rows = Applicant.query.order_by(Applicant.created_at.desc()).all()

    # Build HTML that Excel opens as a sheet. We can control widths via <colgroup>.
    html_parts = []
    html_parts.append("""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Applicants</title>
  <style>
    table { border-collapse: collapse; }
    th, td { border: 1px solid #ddd; padding: 6px; font-family: Arial, sans-serif; font-size: 12px; }
    th { background: #030C69; color: #fff; }
    td.wrap { white-space: normal; }
    td.center { text-align: center; }
    /* Make Excel treat everything as text by default to avoid auto reformat. */
    td, th { mso-number-format: "\\@"; }
  </style>
</head>
<body>
<table>
  <colgroup>
    <col style="width:60px">
    <col style="width:200px">
    <col style="width:220px">
    <col style="width:160px">
    <col style="width:140px">
    <col style="width:200px">
    <col style="width:360px">
    <col style="width:160px">
  </colgroup>
  <thead>
    <tr>
      <th>ID</th>
      <th>Full Name</th>
      <th>Email</th>
      <th>Position</th>
      <th>Availability</th>
      <th>Filename</th>
      <th>File Path</th>
      <th>Created At (UTC+8)</th>
    </tr>
  </thead>
  <tbody>
""")

    for a in rows:
        created_local = (a.created_at + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S") if a.created_at else ""
        html_parts.append(
            f"<tr>"
            f"<td class='center'>{a.id or ''}</td>"
            f"<td>{(a.full_name or '').replace('&','&amp;').replace('<','&lt;')}</td>"
            f"<td>{(a.email or '').replace('&','&amp;').replace('<','&lt;')}</td>"
            f"<td>{(a.position or '').replace('&','&amp;').replace('<','&lt;')}</td>"
            f"<td>{(a.availability or '').replace('&','&amp;').replace('<','&lt;')}</td>"
            f"<td class='wrap'>{(a.filename or '').replace('&','&amp;').replace('<','&lt;')}</td>"
            f"<td class='wrap'>{(a.file_path or '').replace('&','&amp;').replace('<','&lt;')}</td>"
            f"<td class='center'>{created_local}</td>"
            f"</tr>"
        )

    html_parts.append("""
  </tbody>
</table>
</body>
</html>""")

    html = "".join(html_parts).encode("utf-8")
    filename = f"applicants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xls"
    return Response(
        html,
        mimetype="application/vnd.ms-excel; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# --- Proposal CSV export ---
@main_bp.route("/admin/proposals/export/csv", endpoint="admin_export_proposals_csv")
@admin_required
def admin_export_proposals_csv_view():
    """Exports proposals as a CSV compatible with Excel (UTF-8 + BOM)."""
    from app.models import Proposal
    from io import StringIO
    import csv
    from datetime import datetime, timedelta

    # Query proposals newest-first
    rows = Proposal.query.order_by(Proposal.created_at.desc()).all()

    buf = StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL, lineterminator="\n")

    # Header row
    writer.writerow([
        "ID", "Company Name", "Client Email", "Service", 
        "Proposal Details", "Created At (Local Time)"
    ])

    # Data rows
    for p in rows:
        local_time = (
            (p.created_at + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S") 
            if p.created_at else ""
        )
        writer.writerow([
            p.id or "",
            p.company_name or "",
            p.client_email or "",
            p.service or "",
            p.proposal_details or "",
            local_time
        ])

    # Convert to bytes, add UTF-8 BOM for Excel
    data = ("\ufeff" + buf.getvalue()).encode("utf-8-sig")

    # File name with timestamp
    filename = f"proposals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    # Send response
    from flask import Response
    return Response(
        data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# --- Proposal XLSX export ---
@main_bp.route("/admin/proposals/export/xlsx", endpoint="admin_export_proposals_xlsx")
@admin_required
def admin_export_proposals_xlsx_view():
    from app.models import Proposal
    from flask import Response
    from datetime import datetime, timedelta

    rows = Proposal.query.order_by(Proposal.created_at.desc()).all()

    # Build an HTML table that Excel can open and format correctly
    html_parts = ["""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Proposals</title>
  <style>
    table { border-collapse: collapse; }
    th, td { border: 1px solid #ddd; padding: 6px; font-family: Arial, sans-serif; font-size: 12px; vertical-align: top; }
    th { background: #1f2937; color: #fff; }
    td.wrap { white-space: normal; } /* This makes long text wrap */
    /* Make Excel treat everything as text by default */
    td, th { mso-number-format: "\\@"; }
  </style>
</head>
<body>
<table>
  <colgroup>
    <col style="width:60px">
    <col style="width:200px">
    <col style="width:220px">
    <col style="width:160px">
    <col style="width:400px">
    <col style="width:160px">
  </colgroup>
  <thead>
    <tr>
      <th>ID</th>
      <th>Company Name</th>
      <th>Client Email</th>
      <th>Service</th>
      <th>Details</th>
      <th>Created At (UTC+8)</th>
    </tr>
  </thead>
  <tbody>
"""]

    for p in rows:
        created_local = (p.created_at + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S") if p.created_at else ""
        # Sanitize data to prevent breaking the HTML structure
        company = (p.company_name or '').replace('&','&amp;').replace('<','&lt;')
        email = (p.client_email or '').replace('&','&amp;').replace('<','&lt;')
        service = (p.service or '').replace('&','&amp;').replace('<','&lt;')
        details = (p.proposal_details or '').replace('&','&amp;').replace('<','&lt;')

        html_parts.append(
            f"<tr>"
            f"<td>{p.id or ''}</td>"
            f"<td>{company}</td>"
            f"<td>{email}</td>"
            f"<td>{service}</td>"
            f"<td class='wrap'>{details}</td>"
            f"<td>{created_local}</td>"
            f"</tr>"
        )

    html_parts.append("</tbody></table></body></html>")

    html = "".join(html_parts).encode("utf-8")
    filename = f"proposals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xls" # Use .xls for compatibility
    return Response(
        html,
        mimetype="application/vnd.ms-excel; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
# ===================== /ADMIN SECTION =====================


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



