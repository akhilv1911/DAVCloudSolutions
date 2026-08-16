"""
DAV Cloud Solutions - Main Flask Application
Tech Stack: Python Flask, PyMongo, Werkzeug Security, Jinja2, Google GenAI
Founder: V Akhil
"""

import os
from datetime import datetime, timezone
from flask import (
    Flask, render_template, request, redirect, 
    url_for, flash, session, g, jsonify
)
from bson.objectid import ObjectId

from config import config_by_name
from utils.db import get_db, init_db, close_db_connection, init_admin
from utils.auth import (
    hash_password, check_password, 
    generate_verification_token, verify_token,
    login_required, role_required
)
from utils.mailer import send_verification_email, send_admin_inquiry_notification

# Initialize Flask Application
app = Flask(__name__)

# Load Configuration based on Environment
env_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config_by_name[env_name])

# Register Database Teardown Context
app.teardown_appcontext(close_db_connection)

# Initialize Database Indexes & Master Admin
init_db(app)
init_admin(app)


# ==============================================================================
# GLOBAL CONTEXT PROCESSORS & JINJA HELPERS
# ==============================================================================

@app.context_processor
def inject_global_vars():
    """Injects current year and app metadata into all Jinja2 templates."""
    return {
        'current_year': datetime.now().year,
        'app_name': app.config.get('APP_NAME', 'DAV Cloud Solutions'),
        'founder_name': app.config.get('FOUNDER_NAME', 'V Akhil')
    }


# ==============================================================================
# PUBLIC LANDING & PAGES ROUTES
# ==============================================================================

@app.route('/')
def home():
    """Home Landing Page - Aggregates hero, services, about preview, and featured projects."""
    db = get_db()
    featured_projects = list(db.projects.find().limit(6))
    return render_template('index.html', projects=featured_projects)


@app.route('/about')
def about_page():
    """Dedicated About Page - Founder V Akhil story, mission, and pillars."""
    return render_template('pages/about.html')


@app.route('/team')
def team_page():
    """Dedicated Team Page - Fetches active dynamic team members from MongoDB."""
    db = get_db()
    team_members = list(db.team.find().sort('created_at', 1))
    return render_template('pages/team.html', team=team_members)


@app.route('/projects')
def projects_page():
    """Dedicated Projects List Page - Full searchable catalog across domains."""
    db = get_db()
    db_projects = list(db.projects.find())
    return render_template('pages/projects.html', projects=db_projects)


@app.route('/business-directory')
def business_catalog():
    """Verified Business Directory Page - Shows real completed client deliverables."""
    real_projects = [
        {
            "title": "AgriSmart Naa Panta",
            "category": "Agriculture & ML",
            "description": "Comprehensive agricultural prediction and smart crop management platform built for regional farming needs.",
            "tech_stack": ["Python", "Flask", "MongoDB", "Machine Learning"],
            "amount_charged": 6000
        },
        {
            "title": "Streamlit E-Learning Platform",
            "category": "EdTech",
            "description": "Interactive learning management web application built using Streamlit for seamless course delivery and student engagement.",
            "tech_stack": ["Python", "Streamlit", "Data Processing"],
            "amount_charged": 3200
        },
        {
            "title": "Apple Stock Price Prediction & EDA",
            "category": "Data Science",
            "description": "In-depth Exploratory Data Analysis (EDA) and predictive machine learning models for Apple stock market forecasting.",
            "tech_stack": ["Python", "Pandas", "Scikit-Learn", "Matplotlib"],
            "amount_charged": 5000
        }
    ]
    return render_template('directory/business_catalog.html', projects=real_projects)


# ==============================================================================
# UNIVERSAL INQUIRY & LEAD CAPTURE ROUTE (DIRECT SMTP & MONGODB)
# ==============================================================================

@app.route('/api/submit-inquiry', methods=['POST'])
@app.route('/submit-inquiry', methods=['POST'])
def handle_inquiry():
    """Captures lead into MongoDB, links user session if logged in, and sends instant email notification to the company."""
    db = get_db()

    name = request.form.get('name') or request.form.get('from_name', 'Guest Visitor')
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    user_category = request.form.get('user_category', 'General')
    project_name = request.form.get('project_name') or request.form.get('topic') or f"Inquiry ({user_category})"
    message = request.form.get('message') or request.form.get('notes') or request.form.get('topics', '')
    preferred_date = request.form.get('preferred_date', '')
    preferred_time = request.form.get('preferred_time', '')

    inquiry_doc = {
        'user_id': session.get('user_id'),
        'name': name,
        'email': email,
        'phone': phone,
        'user_category': user_category,
        'project_name': project_name,
        'message': message,
        'schedule': f"{preferred_date} at {preferred_time}".strip() if (preferred_date or preferred_time) else None,
        'status': 'New Lead',
        'created_at': datetime.now(timezone.utc)
    }

    # 1. Save directly into MongoDB
    db.inquiries.insert_one(inquiry_doc)

    # 2. Dispatch instant email notification to company inbox via SMTP
    send_admin_inquiry_notification(inquiry_doc)

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.path.startswith('/api/'):
        return jsonify({
            'success': True, 
            'message': 'Your inquiry has been successfully received by Founder V Akhil.'
        }), 200

    flash('Your inquiry has been submitted! Founder V Akhil will reach out shortly.', 'success')
    return redirect(request.referrer or url_for('home'))


# ==============================================================================
# AUTHENTICATION ROUTES (REGISTER, LOGIN, VERIFY, LOGOUT)
# ==============================================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User Registration - Supports Student, Team & Business roles with email verification dispatch."""
    if session.get('user_id'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'student').lower()
        phone = request.form.get('phone', '').strip()
        institution = request.form.get('institution', '').strip()

        # Validation Checks
        if not full_name or not email or not password:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        db = get_db()

        # Check if email exists
        existing_user = db.users.find_one({'email': email})
        if existing_user:
            flash('An account with this email already exists. Please log in.', 'warning')
            return redirect(url_for('login'))

        # Build Business Specific Info
        business_info = None
        if role == 'business':
            business_info = {
                'company_name': request.form.get('company_name', '').strip(),
                'industry': request.form.get('industry', 'IT & Software'),
                'gst_number': request.form.get('gst_number', '').strip(),
                'website': request.form.get('website', '').strip()
            }

        # Create New User Document
        user_document = {
            'full_name': full_name,
            'email': email,
            'password_hash': hash_password(password),
            'role': role,
            'phone': phone,
            'institution': institution if role == 'student' else None,
            'business_info': business_info,
            'is_verified': False,
            'created_at': datetime.now(timezone.utc)
        }

        # Insert into MongoDB
        db.users.insert_one(user_document)

        # Dispatch Verification Email
        token = generate_verification_token(email)
        send_verification_email(email, full_name, token)

        flash('Registration successful! Check your email inbox to verify your account.', 'success')
        return redirect(url_for('verify_notice'))

    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User Login - Validates credentials against MongoDB and sets session variables."""
    if session.get('user_id'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        db = get_db()
        user = db.users.find_one({'email': email})

        if user and check_password(user['password_hash'], password):
            session['user_id'] = str(user['_id'])
            session['full_name'] = user['full_name']
            session['email'] = user['email']
            session['role'] = user['role']
            session['phone'] = user.get('phone', '')
            session['is_verified'] = user.get('is_verified', False)

            flash(f"Welcome back, {user['full_name']}!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email address or password.', 'danger')
            return redirect(url_for('login'))

    return render_template('auth/login.html')


@app.route('/verify-notice')
def verify_notice():
    """Verification Pending Notice Page."""
    return render_template('auth/verify.html', status='notice')


@app.route('/verify/<token>')
def verify_email(token):
    """Token Verification Endpoint - Validates email verification link."""
    email = verify_token(token)

    if not email:
        return render_template('auth/verify.html', status='expired')

    db = get_db()
    result = db.users.update_one({'email': email}, {'$set': {'is_verified': True}})

    if result.matched_count > 0:
        if session.get('email') == email:
            session['is_verified'] = True
        return render_template('auth/verify.html', status='success')
    else:
        return render_template('auth/verify.html', status='invalid')


@app.route('/logout')
def logout():
    """Clears user session and redirects to login."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


# ==============================================================================
# DASHBOARD ROUTER & ROLE PORTALS
# ==============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Smart Dashboard Router - Directs user to their specific portal based on role."""
    role = session.get('role')

    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'team':
        return redirect(url_for('team_dashboard'))
    elif role == 'business':
        return redirect(url_for('business_dashboard'))
    else:
        return redirect(url_for('student_dashboard'))


@app.route('/dashboard/student', methods=['GET', 'POST'])
@login_required
def student_dashboard():
    """Student Dashboard - View academic projects, submit new proposal, access deliverables."""
    db = get_db()
    user_id = session.get('user_id')

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'Student Academic Project').strip()
        description = request.form.get('description', '').strip()
        tech_stack_raw = request.form.get('tech_stack', '').strip()

        if not title or not description:
            flash('Project title and requirement description are required.', 'danger')
            return redirect(url_for('student_dashboard'))

        if tech_stack_raw:
            tech_stack = [t.strip() for t in tech_stack_raw.split(',') if t.strip()]
        else:
            tech_stack = ['Python', 'Flask', 'MongoDB']

        new_project = {
            'user_id': user_id,
            'title': title,
            'category': category,
            'description': description,
            'tech_stack': tech_stack,
            'status': 'Under Review',
            'amount_charged': 0,
            'deliverables_link': None,
            'assigned_to_id': None,
            'assigned_to_name': None,
            'dev_notes': None,
            'created_at': datetime.now(timezone.utc)
        }

        db.projects.insert_one(new_project)

        # Dispatch real-time email notification to company inbox
        send_admin_inquiry_notification({
            'name': session.get('full_name', 'Student User'),
            'email': session.get('email', 'N/A'),
            'phone': session.get('phone', 'N/A'),
            'user_category': 'Student Project Proposal',
            'project_name': title,
            'message': f"Tech Stack: {', '.join(tech_stack)}\n\nRequirements:\n{description}"
        })

        flash('Project proposal submitted successfully! Founder V Akhil will review the scope.', 'success')
        return redirect(url_for('student_dashboard'))

    user_projects = list(db.projects.find({'user_id': user_id}))
    user_inquiries = list(db.inquiries.find({'user_id': user_id}).sort('created_at', -1))
    return render_template(
        'dashboards/student_dashboard.html', 
        projects=user_projects,
        inquiries=user_inquiries
    )


@app.route('/dashboard/business', methods=['GET', 'POST'])
@login_required
def business_dashboard():
    """Business Dashboard - View MVP builds, access staging sandbox, check NDA status."""
    db = get_db()
    user_id = session.get('user_id')
    user = db.users.find_one({'_id': ObjectId(user_id)})

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'Startup MVP Build').strip()
        description = request.form.get('description', '').strip()
        tech_stack_raw = request.form.get('tech_stack', '').strip()

        if not title or not description:
            flash('Project title and requirements are required.', 'danger')
            return redirect(url_for('business_dashboard'))

        if tech_stack_raw:
            tech_stack = [t.strip() for t in tech_stack_raw.split(',') if t.strip()]
        else:
            tech_stack = ['Full-Stack Web', 'Flask', 'MongoDB']

        new_project = {
            'user_id': user_id,
            'title': title,
            'category': category,
            'description': description,
            'tech_stack': tech_stack,
            'status': 'Under Review',
            'amount_charged': 0,
            'deliverables_link': None,
            'assigned_to_id': None,
            'assigned_to_name': None,
            'dev_notes': None,
            'created_at': datetime.now(timezone.utc)
        }

        db.projects.insert_one(new_project)

        # Dispatch real-time email notification to company inbox
        send_admin_inquiry_notification({
            'name': session.get('full_name', 'Business Client'),
            'email': session.get('email', 'N/A'),
            'phone': session.get('phone', 'N/A'),
            'user_category': 'Business MVP Proposal',
            'project_name': title,
            'message': f"Tech Stack: {', '.join(tech_stack)}\n\nRequirements:\n{description}"
        })

        flash('Business MVP requirement submitted successfully! We will prepare a detailed scope & quote.', 'success')
        return redirect(url_for('business_dashboard'))

    user_projects = list(db.projects.find({'user_id': user_id}))
    user_inquiries = list(db.inquiries.find({'user_id': user_id}).sort('created_at', -1))
    return render_template(
        'dashboards/business_dashboard.html', 
        user=user, 
        projects=user_projects,
        inquiries=user_inquiries
    )


# ==============================================================================
# TEAM SPECIALIST WORKSPACE ROUTES
# ==============================================================================

@app.route('/dashboard/team')
@login_required
@role_required('team')
def team_dashboard():
    """Team Dashboard - Role-adaptive workspace for engineers, designers, and specialists."""
    db = get_db()
    user_id = session.get('user_id')
    user_email = session.get('email')

    # Fetch projects assigned to this team member
    assigned_projects = list(db.projects.find({
        '$or': [
            {'assigned_to_id': user_id},
            {'assigned_to_email': user_email}
        ]
    }).sort('created_at', -1))

    # Fetch assigned student walkthroughs / inquiries
    assigned_inquiries = list(db.inquiries.find({
        '$or': [
            {'assigned_to_id': user_id},
            {'assigned_to_email': user_email}
        ]
    }).sort('created_at', -1))

    return render_template(
        'dashboards/team_dashboard.html', 
        projects=assigned_projects,
        inquiries=assigned_inquiries
    )


@app.route('/team/update-task/<project_id>', methods=['POST'])
@login_required
@role_required('team')
def team_update_task(project_id):
    """Allows a team specialist to update project build progress, deliverable links, and dev notes."""
    db = get_db()
    status = request.form.get('status')
    deliverables_link = request.form.get('deliverables_link', '').strip()
    dev_notes = request.form.get('dev_notes', '').strip()

    update_fields: dict = {}
    update_fields['updated_at'] = datetime.now(timezone.utc)
    
    if status:
        update_fields['status'] = status
    if deliverables_link:
        update_fields['deliverables_link'] = deliverables_link
    if dev_notes:
        update_fields['dev_notes'] = dev_notes

    db.projects.update_one({'_id': ObjectId(project_id)}, {'$set': update_fields})
    flash('Task progress and deliverable records updated successfully.', 'success')
    return redirect(url_for('team_dashboard'))


# ==============================================================================
# ADMIN COMMAND CENTER & MANAGEMENT ROUTES
# ==============================================================================

@app.route('/dashboard/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    """Admin Command Center - Master controls for Founder V Akhil."""
    db = get_db()
    all_users = list(db.users.find())
    all_projects = list(db.projects.find())
    all_inquiries = list(db.inquiries.find().sort('created_at', -1))
    all_team = list(db.team.find().sort('created_at', 1))
    
    # Filter registered team accounts for easy project assignment dropdowns
    team_users = [u for u in all_users if u.get('role') == 'team']

    return render_template(
        'dashboards/admin_dashboard.html', 
        users=all_users, 
        projects=all_projects, 
        inquiries=all_inquiries,
        team=all_team,
        team_users=team_users
    )


@app.route('/admin/add-project', methods=['POST'])
@login_required
@role_required('admin')
def admin_add_project():
    """Allows Founder to manually create and dispatch project records."""
    db = get_db()
    title = request.form.get('title', '').strip()
    category = request.form.get('category', 'Student Academic Project').strip()
    status = request.form.get('status', 'Under Review').strip()
    amount = request.form.get('amount_charged', 0)
    deliverables_link = request.form.get('deliverables_link', '').strip()

    if not title:
        flash('Project title is required.', 'danger')
        return redirect(url_for('admin_dashboard'))

    try:
        amount_charged = int(amount)
    except (ValueError, TypeError):
        amount_charged = 0

    new_project = {
        'user_id': session.get('user_id'),
        'title': title,
        'category': category,
        'description': f"Admin dispatched project record under {category}.",
        'tech_stack': ['Flask', 'MongoDB', 'Python'],
        'status': status,
        'amount_charged': amount_charged,
        'deliverables_link': deliverables_link if deliverables_link else None,
        'assigned_to_id': None,
        'assigned_to_name': None,
        'dev_notes': None,
        'created_at': datetime.now(timezone.utc)
    }

    db.projects.insert_one(new_project)
    flash(f"Project '{title}' created and dispatched successfully!", 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/update-project/<project_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_update_project(project_id):
    """Allows Founder to update project status, pricing, deliverable links, and assigned specialist."""
    db = get_db()
    status = request.form.get('status')
    amount = request.form.get('amount_charged', 0)
    deliverables_link = request.form.get('deliverables_link', '').strip()
    assigned_to_id = request.form.get('assigned_to_id', '').strip()

    update_fields: dict = {}
    if status:
        update_fields['status'] = status
    if amount is not None:
        try:
            update_fields['amount_charged'] = int(amount)
        except (ValueError, TypeError):
            pass
    
    update_fields['deliverables_link'] = deliverables_link if deliverables_link else None

    # Handle specialist assignment
    if assigned_to_id:
        member = db.users.find_one({'_id': ObjectId(assigned_to_id)})
        if member:
            update_fields['assigned_to_id'] = str(member['_id'])
            update_fields['assigned_to_name'] = member['full_name']
            update_fields['assigned_to_email'] = member['email']
    elif assigned_to_id == "":
        update_fields['assigned_to_id'] = None
        update_fields['assigned_to_name'] = None
        update_fields['assigned_to_email'] = None

    db.projects.update_one({'_id': ObjectId(project_id)}, {'$set': update_fields})
    flash('Project record updated successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/update-user/<user_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_update_user(user_id):
    """Allows Founder to manually verify users or update role permissions."""
    db = get_db()
    role = request.form.get('role')
    is_verified_str = request.form.get('is_verified', 'false')
    is_verified = (is_verified_str.lower() == 'true')

    update_fields: dict = {}
    if role:
        update_fields['role'] = role
    update_fields['is_verified'] = is_verified

    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': update_fields})
    flash('User account status updated successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete-inquiry/<inquiry_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_inquiry(inquiry_id):
    """Allows Founder to remove an inquiry once addressed."""
    db = get_db()
    db.inquiries.delete_one({'_id': ObjectId(inquiry_id)})
    flash('Inquiry removed from active log.', 'info')
    return redirect(url_for('admin_dashboard'))


# ==============================================================================
# DYNAMIC TEAM ROSTER MANAGEMENT ROUTES
# ==============================================================================

@app.route('/admin/add-team-member', methods=['POST'])
@login_required
@role_required('admin')
def admin_add_team_member():
    """Allows Founder V Akhil to add a new team member dynamically into MongoDB."""
    db = get_db()
    
    name = request.form.get('name', '').strip()
    role = request.form.get('role', '').strip()
    description = request.form.get('description', '').strip()
    responsibilities_raw = request.form.get('responsibilities', '').strip()
    linkedin_url = request.form.get('linkedin_url', '').strip()
    image_filename = request.form.get('image_filename', '').strip()

    if not name or not role:
        flash('Team member name and role are required.', 'danger')
        return redirect(url_for('admin_dashboard'))

    # Parse newline-separated responsibilities into a list
    responsibilities = [r.strip() for r in responsibilities_raw.replace('\r', '').split('\n') if r.strip()]

    new_member = {
        'name': name,
        'role': role,
        'description': description,
        'responsibilities': responsibilities,
        'linkedin_url': linkedin_url if linkedin_url else None,
        'image_filename': image_filename if image_filename else None,
        'created_at': datetime.now(timezone.utc)
    }

    db.team.insert_one(new_member)
    flash(f"Team member '{name}' added successfully to the core roster!", 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete-team-member/<member_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_team_member(member_id):
    """Allows Founder to remove a member from the dynamic team roster."""
    db = get_db()
    db.team.delete_one({'_id': ObjectId(member_id)})
    flash('Team member removed from active directory.', 'info')
    return redirect(url_for('admin_dashboard'))


# ==============================================================================
# LIVE DAV AI INTERNAL AGENT ENDPOINTS (GEMINI POWERED)
# ==============================================================================

@app.route('/api/dav-ai/analyze-lead', methods=['POST'])
@login_required
@role_required('admin')
def api_dav_ai_analyze_lead():
    """Live AI endpoint: Lead scoring, tech feasibility, and pricing suggestions."""
    data = request.get_json() or {}
    inquiry_id = data.get('inquiry_id')
    
    lead_name = data.get('name', 'Guest Lead')
    category = data.get('user_category', 'Student Project')
    message = data.get('message', '')

    if inquiry_id:
        db = get_db()
        inquiry = db.inquiries.find_one({'_id': ObjectId(inquiry_id)})
        if inquiry:
            lead_name = inquiry.get('name', lead_name)
            category = inquiry.get('user_category', category)
            message = inquiry.get('message', message)

    prompt = f"""
    You are the Senior Technical Architect at DAV Cloud Solutions assisting Founder V Akhil.
    Analyze this incoming client/student inquiry:

    Client Name: {lead_name}
    Track: {category}
    Scope/Requirements: {message}

    Provide a concise technical assessment formatted in clean Markdown with:
    1. **Lead Score & Feasibility**: (High / Medium / Low) with 1-line justification.
    2. **Recommended Tech Architecture**: (e.g. Flask, MongoDB, Scikit-Learn, React, Tailwind).
    3. **Estimated Delivery Timeline**: (e.g. 3-5 days, 1 week).
    4. **Suggested Price Quote (₹)**: (e.g. ₹3,500 - ₹6,000).
    5. **Founder Action**: Exact response draft to send the client on WhatsApp or Email.
    """

    try:
        from google import genai
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return jsonify({'success': False, 'error': 'GEMINI_API_KEY is not configured in environment.'}), 500
        
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return jsonify({'success': True, 'analysis': response.text})
    except Exception as e:
        return jsonify({'success': False, 'error': f"DAV AI Engine Error: {str(e)}"}), 500


@app.route('/api/dav-ai/generate-scope', methods=['POST'])
@login_required
@role_required('admin')
def api_dav_ai_generate_scope():
    """Live AI endpoint: System architecture blueprint, schema design, and viva defense questions."""
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    category = data.get('category', 'Student Academic Project').strip()
    requirements = data.get('requirements', '').strip()

    if not title:
        return jsonify({'success': False, 'error': 'Project title is required.'}), 400

    prompt = f"""
    You are the Lead Systems Architect at DAV Cloud Solutions.
    Generate a complete technical project scope and delivery blueprint for:

    - Project Title: {title}
    - Domain Track: {category}
    - Scope Requirements: {requirements}

    Provide a structured technical blueprint in clean Markdown:
    1. **System Architecture Overview** (Frontend, Backend, Database layer)
    2. **Core Functional Modules** (4-6 key features)
    3. **Suggested MongoDB Collections & Schema structure**
    4. **Top 3 Viva Defense / Seminar Questions** that evaluators will ask the student.
    """

    try:
        from google import genai
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return jsonify({'success': False, 'error': 'GEMINI_API_KEY is not configured in environment.'}), 500

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return jsonify({'success': True, 'scope': response.text})
    except Exception as e:
        return jsonify({'success': False, 'error': f"DAV AI Engine Error: {str(e)}"}), 500


@app.route('/api/dav-ai/code-audit', methods=['POST'])
@login_required
@role_required('admin')
def api_dav_ai_code_audit():
    """Live AI endpoint: Security and optimization audit on code snippets."""
    data = request.get_json() or {}
    code_snippet = data.get('code', '').strip()

    if not code_snippet:
        return jsonify({'success': False, 'error': 'Code snippet is required for audit.'}), 400

    prompt = f"""
    You are the Lead Code Reviewer at DAV Cloud Solutions.
    Perform an automated security, efficiency, and cleanliness audit on the following code snippet:

    ```python
    {code_snippet}
    ```

    Evaluate and return in clean Markdown:
    1. **Security Vulnerabilities** (Injection, authentication issues, secret exposures)
    2. **Performance Bottlenecks** (Redundant DB calls, unoptimized queries)
    3. **Production Recommendations** (Cleaner Flask routes, error handlers, modularity)
    """

    try:
        from google import genai
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return jsonify({'success': False, 'error': 'GEMINI_API_KEY is not configured in environment.'}), 500

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return jsonify({'success': True, 'audit': response.text})
    except Exception as e:
        return jsonify({'success': False, 'error': f"DAV AI Engine Error: {str(e)}"}), 500


# ==============================================================================
# APPLICATION RUNNER
# ==============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', True))