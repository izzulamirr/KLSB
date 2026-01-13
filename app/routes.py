from flask import Blueprint, render_template, jsonify, redirect, url_for, request, current_app
import os, secrets
from werkzeug.utils import secure_filename
from sqlalchemy import inspect, insert
from datetime import datetime
from io import StringIO, BytesIO
import csv
from flask import Response, send_file, abort
from app import db
from app.models import Applicant, JobListing
from app.cv_converter import convert_cv_to_klsb_ocr
from functools import wraps
from flask import session, flash
import time
import json
import urllib.parse
import urllib.request

# Rate limiting storage (in-memory for simplicity; use Redis in production)
login_attempts = {}  # {ip: [timestamp1, timestamp2, ...]}
cv_submissions = {}  # {ip: [timestamp1, timestamp2, ...]}
proposal_submissions = {}  # {ip: [timestamp1, timestamp2, ...]}

def verify_recaptcha(response_token, secret_key, remote_ip):
    """Verify reCAPTCHA response with Google using urllib (no dependencies)."""
    if not response_token or not secret_key:
        return False, "Missing reCAPTCHA data"
    
    verify_url = 'https://www.google.com/recaptcha/api/siteverify'
    data = urllib.parse.urlencode({
        'secret': secret_key,
        'response': response_token,
        'remoteip': remote_ip
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(verify_url, data=data)
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('success', False), result.get('error-codes', [])
    except Exception as e:
        return False, str(e)

def check_rate_limit(storage_dict, ip, max_attempts, duration):
    """Check if IP has exceeded rate limit. Returns (allowed: bool, remaining: int, wait_time: int)"""
    now = time.time()
    if ip in storage_dict:
        # Remove old attempts outside the time window
        storage_dict[ip] = [t for t in storage_dict[ip] if now - t < duration]
        
        if len(storage_dict[ip]) >= max_attempts:
            oldest = storage_dict[ip][0]
            wait_time = int(duration - (now - oldest))
            return False, 0, wait_time
    
    # Calculate remaining attempts
    attempts_used = len(storage_dict.get(ip, []))
    remaining = max_attempts - attempts_used
    return True, remaining, 0

def record_attempt(storage_dict, ip):
    """Record an attempt timestamp for the given IP"""
    if ip not in storage_dict:
        storage_dict[ip] = []
    storage_dict[ip].append(time.time())

def clear_attempts(storage_dict, ip):
    """Clear attempts for the given IP (on success)"""
    storage_dict.pop(ip, None)

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
    client_ip = request.remote_addr or 'unknown'

    if request.method == "POST":
        # Check rate limiting
        max_attempts = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
        lockout_duration = current_app.config.get('LOGIN_LOCKOUT_DURATION', 900)
        
        allowed, remaining, wait_time = check_rate_limit(
            login_attempts, client_ip, max_attempts, lockout_duration
        )
        
        if not allowed:
            flash(f"Too many failed attempts. Please try again in {wait_time // 60} minutes.", "error")
            current_app.logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return render_template("admin_login.html"), 429
        
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        next_url = request.args.get("next") or url_for("main.admin_applicants")
        
        # Verify reCAPTCHA if enabled
        if current_app.config.get('RECAPTCHA_ENABLED'):
            recaptcha_response = request.form.get('g-recaptcha-response')
            if not recaptcha_response:
                flash("Please complete the reCAPTCHA verification.", "error")
                return render_template("admin_login.html")
            
            recaptcha_secret = current_app.config.get('RECAPTCHA_SECRET_KEY')
            success, error_info = verify_recaptcha(recaptcha_response, recaptcha_secret, client_ip)
            
            if not success:
                current_app.logger.warning(f"reCAPTCHA failed for {client_ip}: {error_info}")
                flash("reCAPTCHA verification failed. Please try again.", "error")
                return render_template("admin_login.html")

        if username == admin_user and password == admin_pass:
            clear_attempts(login_attempts, client_ip)  # Clear on success
            session["is_admin"] = True
            # ✅ ADD THIS LINE
            session.permanent = False  # Session will expire when browser is closed
            flash("Login successful.", "success")
            current_app.logger.info(f"Admin login from IP: {client_ip}")
            return redirect(next_url)
        
        # Record failed attempt
        record_attempt(login_attempts, client_ip)
        attempts_left = max_attempts - len(login_attempts.get(client_ip, []))
        if attempts_left > 0:
            flash(f"Invalid credentials. {attempts_left} attempts remaining.", "error")
        current_app.logger.warning(f"Failed login from IP: {client_ip}")

    return render_template("admin_login.html")

@main_bp.route("/admin/logout", endpoint="admin_logout")
def admin_logout_view():
    session.pop("is_admin", None)
    flash("Logged out.", "info")
    return redirect(url_for("main.admin_login"))

@main_bp.route("/admin/smtp-diagnose", methods=["GET"], endpoint="admin_smtp_diagnose")
@admin_required
def admin_smtp_diagnose():
    # Delegate to shared utility so we can also reuse this check before sending emails
    from .smtp_utils import run_smtp_diagnose
    report, code = run_smtp_diagnose(current_app)
    return jsonify(report), code

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


@main_bp.route("/admin/cv-converter", methods=["GET"], endpoint="admin_cv_converter_view")
@admin_required
def admin_cv_converter_view():
    """Simple page to trigger OCR-based CV conversion."""
    return render_template("admin_cv_converter.html")

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


@main_bp.route("/admin/cv/convert-ocr", methods=["POST"], endpoint="admin_cv_convert_ocr")
@admin_required
def admin_cv_convert_ocr():
    """Convert an applicant CV into KLSB_877 format using OCR/text extraction."""
    from openai import RateLimitError as OpenAIRateLimitError
    from openai import APIError as OpenAIAPIError
    
    data = {}
    if request.is_json:
        data.update(request.get_json(silent=True) or {})
    data.update(request.form.to_dict())

    applicant_id = data.get("applicant_id")
    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip()
    position = (data.get("position") or "").strip()
    phone = (data.get("phone") or "").strip()
    dob = (data.get("dob") or "").strip()
    nationality = (data.get("nationality") or "").strip()
    marital_status = (data.get("marital_status") or "").strip()
    address = (data.get("address") or "").strip()
    cv_file = request.files.get("cv_file")

    project_root = os.path.abspath(os.path.join(current_app.root_path, ".."))
    upload_folder = current_app.config.get("UPLOAD_FOLDER") or os.path.join(current_app.root_path, "uploads", "cv")
    klsb_folder = os.path.join(upload_folder, "klsb_formatted")
    os.makedirs(klsb_folder, exist_ok=True)

    source_path = None
    temp_path = None

    if applicant_id:
        try:
            applicant = Applicant.query.get_or_404(int(applicant_id))
            source_path = applicant.file_path or ""
            if not os.path.isabs(source_path):
                candidate = os.path.join(project_root, source_path)
                if os.path.exists(candidate):
                    source_path = candidate
                else:
                    source_path = os.path.join(current_app.root_path, source_path)
            if not os.path.exists(source_path):
                return jsonify({"status": "error", "errors": [f"CV file not found: {source_path}"]}), 404

            full_name = full_name or applicant.full_name
            position = position or applicant.position
            email = email or applicant.email
        except Exception as exc:
            current_app.logger.exception("Failed to load applicant for OCR conversion")
            return jsonify({"status": "error", "errors": [str(exc)]}), 400

    else:
        if not cv_file or cv_file.filename == "":
            return jsonify({"status": "error", "errors": ["Provide applicant_id or upload cv_file."]}), 400
        safe_orig = secure_filename(cv_file.filename or "cv.pdf")
        rand = secrets.token_hex(6)
        ext = os.path.splitext(safe_orig)[1] or ".pdf"
        temp_name = f"ocr_{rand}{ext}"
        temp_path = os.path.join(klsb_folder, temp_name)
        try:
            cv_file.save(temp_path)
            source_path = temp_path
        except Exception:
            current_app.logger.exception("Failed to save uploaded CV for OCR conversion")
            return jsonify({"status": "error", "errors": ["Unable to save uploaded file."]}), 500

    # Get output format preference (default to docx)
    output_format = data.get("output_format", "docx")
    
    # Get OCR method preference (default to traditional tesseract)
    use_chatgpt = data.get("use_chatgpt", "false").lower() == "true"

    try:
        converted_path, detected_fields = convert_cv_to_klsb_ocr(
            source_path,
            klsb_folder,
            overrides={
                "name": full_name,
                "position": position,
                "email": email,
                "phone": phone,
                "dob": dob,
                "nationality": nationality,
                "marital_status": marital_status,
                "address": address,
            },
            output_format=output_format,
            use_chatgpt=use_chatgpt
        )
    except OpenAIRateLimitError as exc:
        # ChatGPT quota exceeded - suggest using blue button (tesseract)
        error_msg = "ChatGPT quota exceeded. Please use the blue button (free Tesseract OCR) instead, or add API credits at https://platform.openai.com/settings/organization/billing"
        current_app.logger.warning(f"ChatGPT quota exceeded: {exc}")
        return jsonify({"status": "error", "errors": [error_msg]}), 429
    except OpenAIAPIError as exc:
        # Other OpenAI API errors
        error_msg = f"ChatGPT API error: {str(exc)}. Try the blue button (Tesseract OCR)."
        current_app.logger.warning(f"OpenAI API error: {exc}")
        return jsonify({"status": "error", "errors": [error_msg]}), 500
    except Exception as exc:
        current_app.logger.exception("CV OCR conversion failed")
        return jsonify({"status": "error", "errors": [str(exc)]}), 500
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

    rel_path = os.path.relpath(converted_path, start=current_app.root_path).replace("\\", "/")
    final_name = os.path.basename(converted_path)

    if applicant_id:
        applicant.filename = final_name
        applicant.file_path = rel_path
        db.session.add(applicant)
        db.session.commit()

    return jsonify(
        {
            "status": "success",
            "filename": final_name,
            "stored_at": rel_path,
            "detected_fields": detected_fields,
        }
    ), 201

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

# ------------------- ADMIN: JOB LISTINGS -------------------
@main_bp.route("/admin/jobs", endpoint="admin_jobs")
@admin_required
def admin_jobs():
    """Admin page to view all job listings."""
    jobs = JobListing.query.order_by(JobListing.created_at.desc()).all()
    return render_template("admin_jobs.html", jobs=jobs)

@main_bp.route("/admin/jobs/add", methods=["GET", "POST"], endpoint="admin_add_job")
@admin_required
def admin_add_job():
    """Admin page to add a new job listing."""
    print(f"DEBUG: admin_add_job called with method: {request.method}")
    if request.method == "POST":
        print(f"DEBUG: Form data: {dict(request.form)}")
        title = request.form.get("title", "").strip()
        department = request.form.get("department", "").strip()
        job_type = request.form.get("type", "").strip()
        location = request.form.get("location", "").strip()
        summary = request.form.get("summary", "").strip()
        points = request.form.get("points", "").strip()
        posted_date = request.form.get("posted_date", "").strip()
        is_active = request.form.get("is_active") == "on"

        # Validation
        errors = []
        if not title:
            errors.append("Job Title is required")
        if not department:
            errors.append("Department is required")
        if not job_type:
            errors.append("Employment Type is required")
        if not location:
            errors.append("Location is required")

        if errors:
            for error in errors:
                flash(error, "error")
            # Create a temporary object to preserve form data
            temp_job = type('obj', (object,), {
                'title': title,
                'department': department,
                'type': job_type,
                'location': location,
                'summary': summary,
                'points': points,
                'posted_date': posted_date,
                'is_active': is_active
            })()
            return render_template("admin_job_form.html", job=temp_job, mode="add")

        new_job = JobListing(
            title=title,
            department=department,
            type=job_type,
            location=location,
            summary=summary,
            points=points,
            posted_date=posted_date or "Recently posted",
            is_active=is_active
        )
        # Persist to database
        try:
            print(f"DEBUG: About to add job to database: {new_job.title}")
            db.session.add(new_job)
            print("DEBUG: Job added to session, committing...")
            db.session.commit()
            print(f"DEBUG: Commit successful! Job ID: {new_job.id}")
            flash(f"Job listing '{title}' added successfully.", "success")
            return redirect(url_for("main.admin_jobs"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Failed to add job listing")
            flash(f"Failed to add job listing: {e}", "error")
            # Preserve entered data on error
            return render_template("admin_job_form.html", job=new_job, mode="add")
    

    return render_template("admin_job_form.html", job=None, mode="add")

@main_bp.route("/admin/jobs/<int:job_id>/edit", methods=["GET", "POST"], endpoint="admin_edit_job")
@admin_required
def admin_edit_job(job_id):
    """Admin page to edit an existing job listing."""
    job = JobListing.query.get_or_404(job_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        department = request.form.get("department", "").strip()
        job_type = request.form.get("type", "").strip()
        location = request.form.get("location", "").strip()
        summary = request.form.get("summary", "").strip()
        points = request.form.get("points", "").strip()
        posted_date = request.form.get("posted_date", "").strip()
        is_active = request.form.get("is_active") == "on"

        # Validation
        errors = []
        if not title:
            errors.append("Job Title is required")
        if not department:
            errors.append("Department is required")
        if not job_type:
            errors.append("Employment Type is required")
        if not location:
            errors.append("Location is required")

        if errors:
            for error in errors:
                flash(error, "error")
            # Preserve form data in the job object temporarily
            job.title = title
            job.department = department
            job.type = job_type
            job.location = location
            job.summary = summary
            job.points = points
            job.posted_date = posted_date
            job.is_active = is_active
            return render_template("admin_job_form.html", job=job, mode="edit")

        # Update job
        job.title = title
        job.department = department
        job.type = job_type
        job.location = location
        job.summary = summary
        job.points = points
        job.posted_date = posted_date
        job.is_active = is_active

        db.session.commit()
        flash(f"Job listing '{job.title}' updated successfully.", "success")
        return redirect(url_for("main.admin_jobs"))

    return render_template("admin_job_form.html", job=job, mode="edit")

@main_bp.route("/admin/jobs/<int:job_id>/delete", methods=["POST"], endpoint="admin_delete_job")
@admin_required
def admin_delete_job(job_id):
    """Admin endpoint to delete a job listing."""
    job = JobListing.query.get_or_404(job_id)
    job_title = job.title
    db.session.delete(job)
    db.session.commit()
    flash(f"Job listing '{job_title}' deleted successfully.", "success")
    return redirect(url_for("main.admin_jobs"))

@main_bp.route("/admin/jobs/<int:job_id>/toggle", methods=["POST"], endpoint="admin_toggle_job")
@admin_required
def admin_toggle_job(job_id):
    """Admin endpoint to toggle job active status."""
    job = JobListing.query.get_or_404(job_id)
    job.is_active = not job.is_active
    db.session.commit()
    status = "activated" if job.is_active else "deactivated"
    flash(f"Job listing '{job.title}' {status}.", "success")
    return redirect(url_for("main.admin_jobs"))

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

# ------------------- JOB VACANCIES -------------------
@main_bp.route("/jobs")
def jobs():
    """Public page listing open vacancies from the database."""
    # Fetch active job listings from database
    job_listings = JobListing.query.filter_by(is_active=True).order_by(JobListing.created_at.desc()).all()
    
    # Transform to dict format for template compatibility
    openings = []
    for job in job_listings:
        openings.append({
            "id": job.id,
            "title": job.title,
            "dept": job.department,
            "type": job.type,
            "location": job.location,
            "description": job.summary or job.points or "",
            "posted": job.posted_date or (job.created_at.strftime("%Y-%m-%d") if job.created_at else "N/A"),
        })

    return render_template("jobs.html", jobs=openings, page_class="home-page center-content")

@main_bp.route("/services", endpoint="services_page")
def services_page():
    return render_template("services.html", page_class="home-page center-content")


# ------------------- SEND CV -------------------
@main_bp.route("/services/manpower/send-cv", methods=["GET", "POST"])
def services_manpower_send_cv():
    client_ip = request.remote_addr or 'unknown'
    
    if request.method == "GET":
        # Allow pre-filling the position from query string, e.g. /send-cv?position=HSE%20Officer
        prefill = {
            "full_name": "",
            "email": "",
            "position": request.args.get("position", ""),
            "availability": "",
        }
        return render_template("services/send_cv.html", form=prefill, errors=None)

    errors = []
    
    # Check rate limiting
    max_submissions = current_app.config.get('MAX_CV_SUBMISSIONS_PER_HOUR', 3)
    allowed, remaining, wait_time = check_rate_limit(
        cv_submissions, client_ip, max_submissions, 3600  # 1 hour
    )
    
    if not allowed:
        errors.append(f"Too many submissions. Please try again in {wait_time // 60} minutes.")
        return render_template("services/send_cv.html", errors=errors, form=request.form), 429
    
    # Verify reCAPTCHA if enabled
    if current_app.config.get('RECAPTCHA_ENABLED'):
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not recaptcha_response:
            errors.append("Please complete the reCAPTCHA verification.")
            return render_template("services/send_cv.html", errors=errors, form=request.form), 400
        
        recaptcha_secret = current_app.config.get('RECAPTCHA_SECRET_KEY')
        success, error_info = verify_recaptcha(recaptcha_response, recaptcha_secret, client_ip)
        
        if not success:
            current_app.logger.warning(f"reCAPTCHA failed for CV submission from {client_ip}: {error_info}")
            errors.append("reCAPTCHA verification failed. Please try again.")
            return render_template("services/send_cv.html", errors=errors, form=request.form), 400
    
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
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset pointer
        max_size = current_app.config.get('MAX_FILE_SIZE_MB', 10) * 1024 * 1024
        if file_size > max_size:
            errors.append(f"File size exceeds {current_app.config.get('MAX_FILE_SIZE_MB', 10)}MB limit.")

    if errors:
        return render_template("services/send_cv.html", errors=errors, form=request.form), 400
    
    # Record successful submission for rate limiting
    record_attempt(cv_submissions, client_ip)

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
        
        # Send email notification to admin
        try:
            from app.email_utils import notify_cv_submission
            notify_cv_submission(full_name, position, email, availability)
        except Exception as e:
            current_app.logger.error(f"Failed to send notification email: {str(e)}")
            # Don't fail the request if email fails
        
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
    client_ip = request.remote_addr or 'unknown'

    if request.method == "POST":
        errors = []
        
        # Check rate limiting
        max_submissions = current_app.config.get('MAX_PROPOSAL_SUBMISSIONS_PER_HOUR', 3)
        allowed, remaining, wait_time = check_rate_limit(
            proposal_submissions, client_ip, max_submissions, 3600  # 1 hour
        )
        
        if not allowed:
            errors.append(f"Too many submissions. Please try again in {wait_time // 60} minutes.")
            return render_template("Proposal.html", errors=errors, form=request.form), 429
        
        # Verify reCAPTCHA if enabled
        if current_app.config.get('RECAPTCHA_ENABLED'):
            recaptcha_response = request.form.get('g-recaptcha-response')
            if not recaptcha_response:
                errors.append("Please complete the reCAPTCHA verification.")
                return render_template("Proposal.html", errors=errors, form=request.form), 400
            
            recaptcha_secret = current_app.config.get('RECAPTCHA_SECRET_KEY')
            success, error_info = verify_recaptcha(recaptcha_response, recaptcha_secret, client_ip)
            
            if not success:
                current_app.logger.warning(f"reCAPTCHA failed for proposal from {client_ip}: {error_info}")
                errors.append("reCAPTCHA verification failed. Please try again.")
                return render_template("Proposal.html", errors=errors, form=request.form), 400
        
        company_name = request.form.get("company_name", "").strip()
        client_email = request.form.get("client_email", "").strip()
        proposal_details = request.form.get("proposal_details", "").strip()
        service = request.form.get("service", "").strip()

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
        
        # Record successful submission for rate limiting
        record_attempt(proposal_submissions, client_ip)

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
            
            # Send email notification to admin
            try:
                from app.email_utils import notify_proposal_submission
                notify_proposal_submission(company_name, service, client_email, proposal_details)
            except Exception as e:
                current_app.logger.error(f"Failed to send notification email: {str(e)}")
                # Don't fail the request if email fails
                
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



# ------------------- ADMIN TEST EMAIL -------------------
@main_bp.route("/admin/test-email")
@admin_required
def admin_test_email():
    """Send test CV and Proposal notification emails to ADMIN_EMAIL.
    Use this to verify SMTP settings on localhost or production.
    """
    try:
        from app.email_utils import notify_cv_submission, notify_proposal_submission

        # Send a sample CV notification
        notify_cv_submission(
            applicant_name="Test Applicant",
            position="Test Position",   
            email="test.applicant@example.com",
            availability="Immediate",
        )

        # Send a sample Proposal notification
        notify_proposal_submission(
            company_name="Test Company",
            service="Engineering",
            email="client@example.com",
            proposal_details="This is a test proposal submission to verify email delivery.",
        )

        flash("Test notifications queued. Please check your ADMIN inbox.", "success")
    except Exception as e:
        current_app.logger.exception("Test email failed")
        flash(f"Test email failed: {e}", "error")

    return redirect(url_for("main.admin_applicants"))



