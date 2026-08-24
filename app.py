"""
DAV Cloud Solutions - Main Flask Application.

Tech Stack: Python Flask, PyMongo, Werkzeug Security, Jinja2, Google GenAI
Founder: V Akhil
File: app.py
"""

import os
import time
from datetime import datetime, timezone
from functools import wraps
from bson.objectid import ObjectId
from google import genai

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from config import config_by_name
from utils.auth import (
    check_password,
    generate_verification_token,
    hash_password,
    login_required,
    role_required,
    verify_token,
)
from utils.db import close_db_connection, get_db, init_admin, init_db
from utils.mailer import send_admin_inquiry_notification, send_verification_email

# Initialize Flask Application
app = Flask(__name__)

# Load Configuration based on Environment
env_name = os.environ.get("FLASK_ENV", "development")
app.config.from_object(config_by_name[env_name])

# Register Database Teardown Context
app.teardown_appcontext(close_db_connection)

# Initialize Database Indexes & Master Admin
init_db(app)
init_admin(app)


# ==============================================================================
# RBAC HELPER DECORATORS
# ==============================================================================


def admin_or_team_required(f):
    """Allows access to both Master Admin and verified Team specialists."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            if request.is_json or request.path.startswith("/api/"):
                return jsonify(
                    {"success": False, "error": "Authentication required."}
                ), 401
            flash("Please log in to access this workspace resource.", "warning")
            return redirect(url_for("login"))

        role = session.get("role")
        if role not in ["admin", "team"]:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify(
                    {"success": False, "error": "Unauthorized specialist resource."}
                ), 403
            flash("Unauthorized access level.", "danger")
            return redirect(url_for("dashboard"))

        return f(*args, **kwargs)

    return decorated_function


# ==============================================================================
# GLOBAL CONTEXT PROCESSORS & JINJA HELPERS
# ==============================================================================


@app.context_processor
def inject_global_vars():
    """Injects current year and app metadata into all Jinja2 templates."""
    return {
        "current_year": datetime.now(timezone.utc).year,
        "app_name": app.config.get("APP_NAME", "DAV Cloud Solutions"),
        "founder_name": app.config.get("FOUNDER_NAME", "V Akhil"),
    }


# ==============================================================================
# PUBLIC LANDING & PAGES ROUTES
# ==============================================================================


@app.route("/")
def home():
    """Home Landing Page - Shows only delivered projects registered by real users."""
    db = get_db()
    featured_projects = list(
        db.projects.find({
            "status": {"$in": ["Delivered", "Completed", "Production Verified"]}
        }).sort("created_at", -1).limit(6)
    )
    approved_reviews = list(
        db.reviews.find({"status": "approved"}).sort("created_at", -1).limit(12)
    )
    return render_template(
        "index.html", projects=featured_projects, reviews=approved_reviews
    )


@app.route("/submit-review", methods=["POST"])
def submit_review():
    """Client Review Submission Endpoint - Captures feedback into MongoDB."""
    db = get_db()
    name = request.form.get("client_name", "").strip()
    project_title = request.form.get("project_title", "").strip()
    rating = int(request.form.get("rating", 5))
    feedback = request.form.get("feedback", "").strip()

    if not name or not project_title or not feedback:
        flash(
            "Please fill in all required fields to submit your review.", "warning"
        )
        return redirect(url_for("home") + "#reviews-section")

    review_doc = {
        "name": name,
        "project_title": project_title,
        "rating": rating,
        "feedback": feedback,
        "status": "approved",
        "created_at": datetime.now(timezone.utc),
    }

    db.reviews.insert_one(review_doc)
    flash(
        "Thank you! Your verified review has been published successfully.",
        "success",
    )
    return redirect(url_for("home") + "#reviews-section")


@app.route("/about")
def about_page():
    """Dedicated About Page - Founder story, mission, and pillars."""
    return render_template("pages/about.html")


@app.route("/team")
def team_page():
    """Dedicated Team Page - Fetches active dynamic team members from MongoDB."""
    db = get_db()
    team_members = list(db.team.find().sort("created_at", 1))
    return render_template("pages/team.html", team=team_members)


@app.route("/projects")
def projects_page():
    """Dedicated Projects List Page - Full searchable catalog across all 40+ domains."""
    db = get_db()
    db_projects = list(db.projects.find())
    return render_template("pages/projects.html", projects=db_projects)


@app.route("/business-directory")
def business_catalog():
    """Verified Business Directory Page - Shows real completed client deliverables."""
    real_projects = [
        {
            "title": "AgriSmart Naa Panta",
            "category": "Agriculture & ML",
            "description": (
                "Comprehensive agricultural prediction and smart crop management"
                " platform built for regional farming needs."
            ),
            "tech_stack": [
                "Python Backend",
                "MongoDB Atlas",
                "Applied ML",
            ],
            "status": "Enterprise Deployed",
        },
        {
            "title": "Streamlit E-Learning Platform",
            "category": "EdTech",
            "description": (
                "Interactive learning management web application built for"
                " seamless course delivery, student quizzes, and progress analytics."
            ),
            "tech_stack": [
                "Python Architecture",
                "Streamlit",
                "Interactive UI",
            ],
            "status": "Enterprise Deployed",
        },
        {
            "title": "Apple Stock Price Prediction & EDA",
            "category": "Data Science",
            "description": (
                "In-depth Exploratory Data Analysis (EDA) and predictive machine"
                " learning models for financial market forecasting."
            ),
            "tech_stack": ["Python", "Data Science Pipeline", "Predictive ML"],
            "status": "Enterprise Deployed",
        },
    ]
    return render_template(
        "directory/business_catalog.html", projects=real_projects
    )


# ==============================================================================
# UNIVERSAL INQUIRY & LEAD CAPTURE ROUTE (DIRECT SMTP & MONGODB)
# ==============================================================================


@app.route("/api/submit-inquiry", methods=["POST"])
@app.route("/submit-inquiry", methods=["POST"])
def handle_inquiry():
    """Captures lead into MongoDB, links user session if logged in, and sends instant email notification."""
    db = get_db()

    name = request.form.get("name") or request.form.get(
        "from_name", "Guest Visitor"
    )
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    user_category = request.form.get("user_category", "General")
    project_name = (
        request.form.get("project_name")
        or request.form.get("topic")
        or f"Inquiry ({user_category})"
    )
    message = (
        request.form.get("message")
        or request.form.get("notes")
        or request.form.get("topics", "")
    )
    preferred_date = request.form.get("preferred_date", "")
    preferred_time = request.form.get("preferred_time", "")

    inquiry_doc = {
        "user_id": session.get("user_id"),
        "name": name,
        "email": email,
        "phone": phone,
        "user_category": user_category,
        "project_name": project_name,
        "message": message,
        "schedule": (
            f"{preferred_date} at {preferred_time}".strip()
            if (preferred_date or preferred_time)
            else None
        ),
        "status": "New Lead",
        "created_at": datetime.now(timezone.utc),
    }

    # 1. Save directly into MongoDB
    db.inquiries.insert_one(inquiry_doc)

    # 2. Dispatch instant email notification via SMTP
    send_admin_inquiry_notification(inquiry_doc)

    if (
        request.is_json
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.path.startswith("/api/")
    ):
        return jsonify({
            "success": True,
            "message": (
                "Your inquiry has been successfully received by the DAV Cloud Solutions engineering team."
            ),
        }), 200

    flash(
        "Your inquiry has been submitted! Our engineering team will reach out shortly.",
        "success",
    )
    return redirect(request.referrer or url_for("home"))


# ==============================================================================
# AUTHENTICATION & TWO-TIER VERIFICATION ROUTES
# ==============================================================================


@app.route("/register", methods=["GET", "POST"])
def register():
    """User Registration - Supports Student, Team & Business roles with email verification dispatch."""
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "student").lower()
        phone = request.form.get("phone", "").strip()
        institution = request.form.get("institution", "").strip()

        # Validation Checks
        if not full_name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        db = get_db()

        # Check if email exists
        existing_user = db.users.find_one({"email": email})
        if existing_user:
            flash(
                "An account with this email already exists. Please log in.", "warning"
            )
            return redirect(url_for("login"))

        # Build Business Specific Info
        business_info = None
        if role == "business":
            business_info = {
                "company_name": request.form.get("company_name", "").strip(),
                "industry": request.form.get("industry", "IT & Software"),
                "gst_number": request.form.get("gst_number", "").strip(),
                "website": request.form.get("website", "").strip(),
            }

        # Create New User Document
        user_document = {
            "full_name": full_name,
            "email": email,
            "password_hash": hash_password(password),
            "role": role,
            "phone": phone,
            "institution": institution if role == "student" else None,
            "business_info": business_info,
            "is_email_verified": False,
            "is_admin_approved": False,
            "is_verified": False,
            "created_at": datetime.now(timezone.utc),
        }

        # Insert into MongoDB
        db.users.insert_one(user_document)

        # Dispatch Verification Email
        token = generate_verification_token(email)
        send_verification_email(email, full_name, token)

        # Notify Admin inbox
        send_admin_inquiry_notification({
            "name": full_name,
            "email": email,
            "phone": phone,
            "user_category": f"New {role.capitalize()} Registration",
            "project_name": "Pending Approval",
            "message": (
                f"A new {role} registered ({email}). Awaiting email confirmation and Admin activation."
            ),
        })

        flash(
            "Registration successful! Please check your email inbox to verify your email address.",
            "success",
        )
        return redirect(url_for("verify_notice"))

    return render_template("auth/register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """User Login - Validates credentials, email confirmation, and admin approval."""
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        user = db.users.find_one({"email": email})

        if user and check_password(user["password_hash"], password):
            # 1. Master Admin bypasses verification
            if user.get("role") == "admin":
                session["user_id"] = str(user["_id"])
                session["full_name"] = user["full_name"]
                session["email"] = user["email"]
                session["role"] = user["role"]
                session["phone"] = user.get("phone", "")
                session["is_verified"] = True

                flash(f"Welcome back, Master Admin {user['full_name']}!", "success")
                return redirect(url_for("admin_dashboard"))

            # 2. Check Step 1: User Email Verification
            user_email_verified = user.get(
                "is_email_verified", user.get("is_verified", False)
            )
            if not user_email_verified:
                flash(
                    "Please verify your email address before logging in. Check your inbox or spam folder.",
                    "warning",
                )
                return redirect(url_for("verify_notice"))

            # 3. Check Step 2: Admin Approval
            if not user.get("is_admin_approved", False):
                flash(
                    "Your email is verified! Your account is currently in queue for review and activation by the DAV Cloud Solutions administration team.",
                    "info",
                )
                return redirect(url_for("login"))

            # 4. Authenticated Session Context
            session["user_id"] = str(user["_id"])
            session["full_name"] = user["full_name"]
            session["email"] = user["email"]
            session["role"] = user["role"]
            session["phone"] = user.get("phone", "")
            session["is_verified"] = True

            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email address or password.", "danger")
            return redirect(url_for("login"))

    return render_template("auth/login.html")


@app.route("/verify-notice")
def verify_notice():
    """Verification Pending Notice Page."""
    return render_template("auth/verify.html", status="notice")


@app.route("/resend-verification", methods=["POST"])
def resend_verification():
    """Allows users to request a fresh verification email."""
    email = request.form.get("email", "").strip().lower()
    if not email:
        flash("Please provide your registered email address.", "danger")
        return redirect(url_for("verify_notice"))

    db = get_db()
    user = db.users.find_one({"email": email})

    if user:
        if user.get("is_email_verified", user.get("is_verified", False)):
            flash(
                "Your email is already verified. If your account is pending approval, please wait for administrative activation.",
                "info",
            )
            return redirect(url_for("login"))

        token = generate_verification_token(email)
        send_verification_email(email, user["full_name"], token)
        flash(
            "A fresh verification link has been dispatched to your email.",
            "success",
        )
    else:
        flash("No account found with this email address.", "danger")

    return redirect(url_for("verify_notice"))


@app.route("/verify/<token>")
def verify_email(token):
    """Token Verification Endpoint - Validates link clicked from Gmail."""
    email = verify_token(token)

    if not email:
        return render_template("auth/verify.html", status="expired")

    db = get_db()
    result = db.users.update_one(
        {"email": email},
        {"$set": {"is_email_verified": True, "is_verified": True}},
    )

    if result.matched_count > 0:
        return render_template(
            "auth/verify.html", status="email_verified_waiting_admin"
        )
    else:
        return render_template("auth/verify.html", status="invalid")


@app.route("/logout")
def logout():
    """Clears user session and redirects to login."""
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))


# ==============================================================================
# DASHBOARD ROUTER & ROLE PORTALS
# ==============================================================================


@app.route("/dashboard")
@login_required
def dashboard():
    """Smart Dashboard Router - Directs user to their specific portal based on role."""
    role = session.get("role")

    if role == "admin":
        return redirect(url_for("admin_dashboard"))
    elif role == "team":
        return redirect(url_for("team_dashboard"))
    elif role == "business":
        return redirect(url_for("business_dashboard"))
    else:
        return redirect(url_for("student_dashboard"))


@app.route("/dashboard/student", methods=["GET", "POST"])
@login_required
def student_dashboard():
    """Student Dashboard - View academic projects, submit new proposal, access deliverables."""
    db = get_db()
    user_id = session.get("user_id")

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "Student Academic Project").strip()
        description = request.form.get("description", "").strip()
        tech_stack_raw = request.form.get("tech_stack", "").strip()

        if not title or not description:
            flash(
                "Project title and requirement description are required.", "danger"
            )
            return redirect(url_for("student_dashboard"))

        if tech_stack_raw:
            tech_stack = [t.strip() for t in tech_stack_raw.split(",") if t.strip()]
        else:
            tech_stack = ["Python", "Flask", "Cloud Storage"]

        new_project = {
            "user_id": user_id,
            "title": title,
            "category": category,
            "description": description,
            "tech_stack": tech_stack,
            "status": "Under Review",
            "amount_charged": 0,
            "deliverables_link": None,
            "assigned_to_id": None,
            "assigned_to_name": None,
            "dev_notes": None,
            "created_at": datetime.now(timezone.utc),
        }

        db.projects.insert_one(new_project)

        # Dispatch real-time email notification to company inbox
        send_admin_inquiry_notification({
            "name": session.get("full_name", "Student User"),
            "email": session.get("email", "N/A"),
            "phone": session.get("phone", "N/A"),
            "user_category": "Student Project Proposal",
            "project_name": title,
            "message": (
                f"Tech Stack: {', '.join(tech_stack)}\n\nRequirements:\n{description}"
            ),
        })

        flash(
            "Project proposal submitted successfully! Our engineering team will review the scope.",
            "success",
        )
        return redirect(url_for("student_dashboard"))

    user_projects = list(db.projects.find({"user_id": user_id}))
    user_inquiries = list(
        db.inquiries.find({"user_id": user_id}).sort("created_at", -1)
    )
    return render_template(
        "dashboards/student_dashboard.html",
        projects=user_projects,
        inquiries=user_inquiries,
    )


@app.route("/dashboard/business", methods=["GET", "POST"])
@login_required
def business_dashboard():
    """Business Dashboard - View MVP builds, access staging sandbox, check NDA status."""
    db = get_db()
    user_id = session.get("user_id")
    user = db.users.find_one({"_id": ObjectId(user_id)})

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "Startup MVP Build").strip()
        description = request.form.get("description", "").strip()
        tech_stack_raw = request.form.get("tech_stack", "").strip()

        if not title or not description:
            flash("Project title and requirements are required.", "danger")
            return redirect(url_for("business_dashboard"))

        if tech_stack_raw:
            tech_stack = [t.strip() for t in tech_stack_raw.split(",") if t.strip()]
        else:
            tech_stack = ["Full-Stack Web", "Python Architecture", "Cloud Database"]

        new_project = {
            "user_id": user_id,
            "title": title,
            "category": category,
            "description": description,
            "tech_stack": tech_stack,
            "status": "Under Review",
            "amount_charged": 0,
            "deliverables_link": None,
            "assigned_to_id": None,
            "assigned_to_name": None,
            "dev_notes": None,
            "created_at": datetime.now(timezone.utc),
        }

        db.projects.insert_one(new_project)

        # Dispatch real-time email notification to company inbox
        send_admin_inquiry_notification({
            "name": session.get("full_name", "Business Client"),
            "email": session.get("email", "N/A"),
            "phone": session.get("phone", "N/A"),
            "user_category": "Business MVP Proposal",
            "project_name": title,
            "message": (
                f"Tech Stack: {', '.join(tech_stack)}\n\nRequirements:\n{description}"
            ),
        })

        flash(
            "Business MVP requirement submitted successfully! We will prepare a detailed scope & quote.",
            "success",
        )
        return redirect(url_for("business_dashboard"))

    user_projects = list(db.projects.find({"user_id": user_id}))
    user_inquiries = list(
        db.inquiries.find({"user_id": user_id}).sort("created_at", -1)
    )
    return render_template(
        "dashboards/business_dashboard.html",
        user=user,
        projects=user_projects,
        inquiries=user_inquiries,
    )


# ==============================================================================
# TEAM SPECIALIST WORKSPACE ROUTES
# ==============================================================================


@app.route("/dashboard/team")
@login_required
@role_required("team")
def team_dashboard():
    """Team Dashboard - Role-adaptive workspace for engineers, designers, and specialists."""
    db = get_db()
    user_id = session.get("user_id")
    user_email = session.get("email")

    assigned_projects = list(
        db.projects.find({
            "$or": [
                {"assigned_to_id": user_id},
                {"assigned_to_email": user_email},
            ]
        }).sort("created_at", -1)
    )

    all_system_projects = list(db.projects.find().sort("created_at", -1))

    assigned_inquiries = list(
        db.inquiries.find({
            "$or": [
                {"assigned_to_id": user_id},
                {"assigned_to_email": user_email},
            ]
        }).sort("created_at", -1)
    )

    return render_template(
        "dashboards/team_dashboard.html",
        projects=assigned_projects,
        all_projects=all_system_projects,
        inquiries=assigned_inquiries,
    )


@app.route("/team/update-task/<project_id>", methods=["POST"])
@login_required
@role_required("team")
def team_update_task(project_id):
    """Allows a team specialist to update project build progress, deliverable links, and dev notes."""
    db = get_db()
    status = request.form.get("status")
    deliverables_link = request.form.get("deliverables_link", "").strip()
    dev_notes = request.form.get("dev_notes", "").strip()

    update_fields: dict = {}
    update_fields["updated_at"] = datetime.now(timezone.utc)

    if status:
        update_fields["status"] = status
    if deliverables_link:
        update_fields["deliverables_link"] = deliverables_link
    if dev_notes:
        update_fields["dev_notes"] = dev_notes

    db.projects.update_one(
        {"_id": ObjectId(project_id)}, {"$set": update_fields}
    )
    flash(
        "Task progress and deliverable records updated successfully.", "success"
    )
    return redirect(url_for("team_dashboard"))


# ==============================================================================
# ADMIN COMMAND CENTER & MANAGEMENT ROUTES
# ==============================================================================


@app.route("/dashboard/admin")
@login_required
@role_required("admin")
def admin_dashboard():
    """Admin Command Center - Master operational controls."""
    db = get_db()
    all_users = list(db.users.find())
    all_projects = list(db.projects.find().sort("created_at", -1))
    all_inquiries = list(db.inquiries.find().sort("created_at", -1))
    all_team = list(db.team.find().sort("created_at", 1))

    team_users = [u for u in all_users if u.get("role") == "team"]

    return render_template(
        "dashboards/admin_dashboard.html",
        users=all_users,
        projects=all_projects,
        inquiries=all_inquiries,
        team=all_team,
        team_users=team_users,
    )


@app.route("/admin/add-project", methods=["POST"])
@login_required
@role_required("admin")
def admin_add_project():
    """Allows Admin to manually create and dispatch project records."""
    db = get_db()
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "Student Academic Project").strip()
    status = request.form.get("status", "Under Review").strip()
    amount = request.form.get("amount_charged", 0)
    deliverables_link = request.form.get("deliverables_link", "").strip()

    if not title:
        flash("Project title is required.", "danger")
        return redirect(url_for("admin_dashboard"))

    try:
        amount_charged = int(amount)
    except (ValueError, TypeError):
        amount_charged = 0

    new_project = {
        "user_id": session.get("user_id"),
        "title": title,
        "category": category,
        "description": f"Engineered project build under {category}.",
        "tech_stack": ["Python Backend", "Cloud Storage"],
        "status": status,
        "amount_charged": amount_charged,
        "deliverables_link": deliverables_link if deliverables_link else None,
        "assigned_to_id": None,
        "assigned_to_name": None,
        "dev_notes": None,
        "created_at": datetime.now(timezone.utc),
    }

    db.projects.insert_one(new_project)
    flash(f"Project '{title}' created and dispatched successfully!", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/update-project/<project_id>", methods=["POST"])
@login_required
@role_required("admin")
def admin_update_project(project_id):
    """Allows Admin to update project status, pricing, deliverable links, and assigned specialist."""
    db = get_db()
    status = request.form.get("status")
    amount = request.form.get("amount_charged", 0)
    deliverables_link = request.form.get("deliverables_link", "").strip()
    assigned_to_id = request.form.get("assigned_to_id", "").strip()

    update_fields: dict = {}
    if status:
        update_fields["status"] = status
    if amount is not None:
        try:
            update_fields["amount_charged"] = int(amount)
        except (ValueError, TypeError):
            pass

    update_fields["deliverables_link"] = (
        deliverables_link if deliverables_link else None
    )

    # Handle specialist assignment
    if assigned_to_id:
        member = db.users.find_one({"_id": ObjectId(assigned_to_id)})
        if member:
            update_fields["assigned_to_id"] = str(member["_id"])
            update_fields["assigned_to_name"] = member["full_name"]
            update_fields["assigned_to_email"] = member["email"]
    elif assigned_to_id == "":
        update_fields["assigned_to_id"] = None
        update_fields["assigned_to_name"] = None
        update_fields["assigned_to_email"] = None

    db.projects.update_one(
        {"_id": ObjectId(project_id)}, {"$set": update_fields}
    )
    flash("Project record updated successfully.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete-project/<project_id>", methods=["POST"])
@login_required
@role_required("admin")
def admin_delete_project(project_id):
    """Allows Admin to permanently delete a project record from MongoDB."""
    db = get_db()
    db.projects.delete_one({"_id": ObjectId(project_id)})
    flash("Project record permanently deleted from system.", "info")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/update-user/<user_id>", methods=["POST"])
@login_required
@role_required("admin")
def admin_update_user(user_id):
    """Allows Admin to approve accounts, update email status, or edit roles."""
    db = get_db()
    role = request.form.get("role")
    is_admin_approved = (
        request.form.get("is_admin_approved", "false").lower() == "true"
    )
    is_email_verified = (
        request.form.get("is_email_verified", "false").lower() == "true"
    )

    update_fields: dict = {
        "is_admin_approved": is_admin_approved,
        "is_email_verified": is_email_verified,
        "is_verified": (is_email_verified and is_admin_approved),
    }
    if role:
        update_fields["role"] = role

    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})
    flash("User verification & approval status updated successfully.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete-inquiry/<inquiry_id>", methods=["POST"])
@login_required
@role_required("admin")
def admin_delete_inquiry(inquiry_id):
    """Allows Admin to remove an inquiry from the active log."""
    db = get_db()
    db.inquiries.delete_one({"_id": ObjectId(inquiry_id)})
    flash("Inquiry removed from active log.", "info")
    return redirect(url_for("admin_dashboard"))


# ==============================================================================
# DYNAMIC TEAM ROSTER MANAGEMENT ROUTES
# ==============================================================================


@app.route("/admin/add-team-member", methods=["POST"])
@login_required
@role_required("admin")
def admin_add_team_member():
    """Allows Admin to add a new team member dynamically into MongoDB."""
    db = get_db()

    name = request.form.get("name", "").strip()
    role = request.form.get("role", "").strip()
    description = request.form.get("description", "").strip()
    responsibilities_raw = request.form.get("responsibilities", "").strip()
    linkedin_url = request.form.get("linkedin_url", "").strip()
    image_filename = request.form.get("image_filename", "").strip()

    if not name or not role:
        flash("Team member name and role are required.", "danger")
        return redirect(url_for("admin_dashboard"))

    responsibilities = [
        r.strip()
        for r in responsibilities_raw.replace("\r", "").split("\n")
        if r.strip()
    ]

    new_member = {
        "name": name,
        "role": role,
        "description": description,
        "responsibilities": responsibilities,
        "linkedin_url": linkedin_url if linkedin_url else None,
        "image_filename": image_filename if image_filename else None,
        "created_at": datetime.now(timezone.utc),
    }

    db.team.insert_one(new_member)
    flash(
        f"Team member '{name}' added successfully to the core roster!", "success"
    )
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete-team-member/<member_id>", methods=["POST"])
@login_required
@role_required("admin")
def admin_delete_team_member(member_id):
    """Allows Admin to remove a member from the dynamic team roster."""
    db = get_db()
    db.team.delete_one({"_id": ObjectId(member_id)})
    flash("Team member removed from active directory.", "info")
    return redirect(url_for("admin_dashboard"))


# ==============================================================================
# LIVE DAV AI INTERNAL AGENT ENDPOINTS (GEMINI POWERED WITH FALLBACK)
# ==============================================================================

def call_gemini_with_fallback(client, prompt):
    """Helper to safely call Gemini with fallback models if 503 unavailable occurs."""
    models_to_try = ["gemini-3.7-flash", "gemini-3.5-flash", "gemini-3.6-flash"]
    
    last_error = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            text_output = getattr(response, "text", None) or str(response)
            if text_output:
                return text_output
        except Exception as e:
            last_error = e
            time.sleep(1)
            continue
            
    raise Exception(f"All Gemini models busy. Last error: {str(last_error)}")


@app.route("/api/dav-ai/analyze-lead", methods=["POST"])
@admin_or_team_required
def api_dav_ai_analyze_lead():
    """Live AI endpoint: Lead scoring, tech feasibility, and scope assessment."""
    data = request.get_json() or {}
    inquiry_id = data.get("inquiry_id")

    lead_name = data.get("name", "Guest Lead")
    category = data.get("user_category", "Student Project")
    message = data.get("message", "")

    if inquiry_id:
        db = get_db()
        inquiry = db.inquiries.find_one({"_id": ObjectId(inquiry_id)})
        if inquiry:
            lead_name = inquiry.get("name", lead_name)
            category = inquiry.get("user_category", category)
            message = inquiry.get("message", message)

    user_role = session.get("role", "team")

    prompt = f"""
    You are the Senior Technical Architect at DAV Cloud Solutions assisting the Core Engineering Team.
    Analyze this incoming client/student inquiry (Requested by: {user_role.upper()} Specialist):

    Client Name: {lead_name}
    Track: {category}
    Scope/Requirements: {message}

    Provide a concise technical assessment formatted in clean Markdown with:
    1. **Lead Score & Feasibility**: (High / Medium / Low) with 1-line justification.
    2. **Recommended Tech Architecture**: (e.g. Scalable Microservices, Cloud Data, React, Applied ML).
    3. **Estimated Delivery Timeline**: (e.g. 3-5 days, 1 week).
    4. **Suggested Price Quote (₹)**: (e.g. ₹3,500 - ₹6,000).
    5. **Next Technical Actions**: Concrete engineering steps and response draft for the client.
    """

    try:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return jsonify({
                "success": False,
                "error": "GEMINI_API_KEY is not configured in environment.",
            }), 500

        client = genai.Client(api_key=api_key)
        analysis_text = call_gemini_with_fallback(client, prompt)
        return jsonify({"success": True, "analysis": analysis_text})
    except Exception as e:
        return jsonify(
            {"success": False, "error": f"DAV AI Engine Error: {str(e)}"}
        ), 500


@app.route("/api/dav-ai/generate-scope", methods=["POST"])
@admin_or_team_required
def api_dav_ai_generate_scope():
    """Live AI endpoint: System architecture blueprint, schema design, and viva defense questions."""
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    category = data.get("category", "Student Academic Project").strip()
    
    requirements = (
        data.get("requirements")
        or data.get("message")
        or data.get("description")
        or data.get("req")
        or "Standard production architecture with authentication, API routes, and cloud database integration."
    ).strip()

    if not title:
        return jsonify({"success": False, "error": "Project title is required."}), 400

    prompt = f"""
    You are the Lead Systems Architect at DAV Cloud Solutions.
    Generate a complete technical project scope and delivery blueprint for:

    - Project Title: {title}
    - Domain Track: {category}
    - Scope Requirements: {requirements}

    Provide a structured technical blueprint in clean Markdown:
    1. **System Architecture Overview** (Frontend, Backend API layer, Cloud Database)
    2. **Core Functional Modules** (4-6 key features)
    3. **Suggested Data Schema & Document Structure** (Collections/Tables and fields)
    4. **Top 5 Viva Defense / Technical Interview Questions** (with complete technical answers for university examiners)
    """

    try:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return jsonify({
                "success": False,
                "error": "GEMINI_API_KEY is not configured in environment.",
            }), 500

        client = genai.Client(api_key=api_key)
        scope_text = call_gemini_with_fallback(client, prompt)
        return jsonify({
            "success": True,
            "scope": scope_text,
            "analysis": scope_text
        })
    except Exception as e:
        return jsonify(
            {"success": False, "error": f"DAV AI Engine Error: {str(e)}"}
        ), 500


@app.route("/api/dav-ai/code-audit", methods=["POST"])
@admin_or_team_required
def api_dav_ai_code_audit():
    """Live AI endpoint: Security and optimization audit on code snippets."""
    data = request.get_json() or {}
    code_snippet = data.get("code", "").strip()

    if not code_snippet:
        return jsonify(
            {"success": False, "error": "Code snippet is required for audit."}
        ), 400

    prompt = f"""
    You are the Lead Code Reviewer at DAV Cloud Solutions.
    Perform an automated security, efficiency, and cleanliness audit on the following code snippet:

    ```python
    {code_snippet}
    ```

    Evaluate and return in clean Markdown:
    1. **Security Vulnerabilities** (Injection risks, auth flaws, exposed secrets)
    2. **Performance Bottlenecks** (Redundant data queries, execution load)
    3. **Production Recommendations** (API structuring, robust error handlers, modularity)
    """

    try:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return jsonify({
                "success": False,
                "error": "GEMINI_API_KEY is not configured in environment.",
            }), 500

        client = genai.Client(api_key=api_key)
        audit_text = call_gemini_with_fallback(client, prompt)
        return jsonify({"success": True, "audit": audit_text})
    except Exception as e:
        return jsonify(
            {"success": False, "error": f"DAV AI Engine Error: {str(e)}"}
        ), 500


# ==============================================================================
# APPLICATION RUNNER
# ==============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0", 
        port=port, 
        debug=app.config.get("DEBUG", True),
        use_reloader=False
    )