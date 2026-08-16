"""
DAV Cloud Solutions - Mailer & Email Dispatcher Module
Tech Stack: Python Flask, SMTP (Direct SSL & Background Threading), MIME
Founder: V Akhil
"""

import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, url_for


def _dispatch_smtp_background(msg: MIMEMultipart, recipient: str, mail_server: str, mail_port: int, mail_username: str, mail_password: str, mail_sender: str):
    """Background worker that transmits email over SMTP without blocking the Flask worker."""
    try:
        if mail_port == 465:
            # Direct SSL connection (recommended for cloud hosts like Render)
            with smtplib.SMTP_SSL(mail_server, mail_port, timeout=12) as server:
                server.login(mail_username, mail_password)
                server.sendmail(mail_sender, [recipient], msg.as_string())
        else:
            # STARTTLS connection (Port 587)
            with smtplib.SMTP(mail_server, mail_port, timeout=12) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(mail_username, mail_password)
                server.sendmail(mail_sender, [recipient], msg.as_string())

        print(f"[MAILER SUCCESS] Email delivered to: {recipient}")
    except Exception as e:
        print(f"[MAILER ERROR] Failed to send email to {recipient}: {e}")


def send_verification_email(to_email: str, full_name: str, token: str) -> bool:
    """
    Dispatches an automated email verification link to a newly registered user.
    Uses SMTP settings defined in Flask config or environment variables.
    """
    mail_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
    mail_port = int(current_app.config.get('MAIL_PORT', 465))
    mail_username = current_app.config.get('MAIL_USERNAME')
    mail_password = (current_app.config.get('MAIL_PASSWORD') or '').replace(' ', '').strip()
    mail_sender = (
        current_app.config.get('MAIL_DEFAULT_SENDER') 
        or mail_username 
        or "contactdavcloudsolutions@gmail.com"
    )

    # Build absolute verification URL
    verification_url = url_for('verify_email', token=token, _external=True)

    # Email Subject and Header Setup
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Verify Your Account | DAV Cloud Solutions"
    msg['From'] = f"DAV Cloud Solutions <{mail_sender}>"
    msg['To'] = to_email

    # Plain-Text Email Fallback
    text_content = f"""
Hello {full_name},

Thank you for registering with DAV Cloud Solutions!

To activate your account and access your dashboard, please visit:
{verification_url}

This verification link will expire in 24 hours.

If you did not create an account on DAV Cloud Solutions, please ignore this email.

Best regards,
V Akhil & The DAV Cloud Solutions Team
contactdavcloudsolutions@gmail.com
"""

    # HTML Formatted Email Template
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #0b0f19; color: #f9fafb; margin: 0; padding: 20px; }}
        .email-container {{ max-width: 600px; margin: 0 auto; background: #111827; border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 12px; padding: 32px; }}
        .brand-title {{ font-size: 24px; font-weight: 800; color: #3b82f6; text-align: center; margin-bottom: 24px; }}
        .btn-verify {{ display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #3b82f6 0%, #4f46e5 100%); color: #ffffff !important; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; text-align: center; }}
        .footer-text {{ font-size: 12px; color: #9ca3af; margin-top: 28px; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 16px; text-align: center; }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="brand-title"><span style="color:#ffffff;">DAV</span> Cloud Solutions</div>
        <h2>Welcome, {full_name}!</h2>
        <p>Thank you for registering with DAV Cloud Solutions. To activate your account and gain full access to your personalized portal, please verify your email address.</p>
        
        <div style="text-align: center;">
            <a href="{verification_url}" class="btn-verify">Verify Email Address</a>
        </div>

        <p style="font-size: 13px; color: #9ca3af;">Or copy and paste this link into your browser:<br>
        <a href="{verification_url}" style="color: #3b82f6;">{verification_url}</a></p>

        <p style="font-size: 13px; color: #9ca3af;"><em>Note: This verification link is valid for 24 hours.</em></p>

        <div class="footer-text">
            &copy; 2026 DAV Cloud Solutions. Founded by V Akhil.<br>
            If you did not register for this account, please ignore this email.
        </div>
    </div>
</body>
</html>
"""

    msg.attach(MIMEText(text_content, 'plain'))
    msg.attach(MIMEText(html_content, 'html'))

    # Development fallback if credentials are unset
    if not mail_username or not mail_password:
        current_app.logger.warning("SMTP Mailer credentials missing. Email dispatch simulated.")
        print(f"[SIMULATED VERIFICATION EMAIL] Link for {to_email}: {verification_url}")
        return True

    # Dispatch in background thread so Gunicorn worker does not timeout
    threading.Thread(
        target=_dispatch_smtp_background,
        args=(msg, to_email, mail_server, mail_port, mail_username, mail_password, mail_sender),
        daemon=True
    ).start()

    return True


def send_admin_inquiry_notification(inquiry_data: dict) -> bool:
    """
    Sends an instant email notification to the company whenever a user submits any form
    (Project Scope, Mentorship Booking, or Support Query).
    """
    mail_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
    mail_port = int(current_app.config.get('MAIL_PORT', 465))
    mail_username = current_app.config.get('MAIL_USERNAME')
    mail_password = (current_app.config.get('MAIL_PASSWORD') or '').replace(' ', '').strip()
    admin_email = current_app.config.get('ADMIN_EMAIL') or mail_username or "contactdavcloudsolutions@gmail.com"
    mail_sender = current_app.config.get('MAIL_DEFAULT_SENDER') or mail_username or "contactdavcloudsolutions@gmail.com"

    name = inquiry_data.get('name', 'Guest Visitor')
    email = inquiry_data.get('email', 'N/A')
    phone = inquiry_data.get('phone', 'N/A')
    category = inquiry_data.get('user_category', 'General')
    project_name = inquiry_data.get('project_name', 'General Project Requirement')
    message = inquiry_data.get('message', 'No details provided.')
    schedule = inquiry_data.get('schedule')

    subject = f"🚨 New Lead / Inquiry: {project_name} ({name})"

    # Plain text version
    text_content = f"""
New Inquiry Received on DAV Cloud Solutions:

Category: {category}
Client / Student: {name}
Email: {email}
Phone / WhatsApp: {phone}
Project / Topic: {project_name}
Schedule: {schedule if schedule else 'N/A'}

Message / Scope:
{message}
"""

    # HTML Formatted Notification Email
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        .card {{ max-width: 600px; margin: 0 auto; background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 28px; }}
        .header {{ border-bottom: 1px solid #334155; padding-bottom: 16px; margin-bottom: 20px; }}
        .header h2 {{ color: #38bdf8; margin: 0 0 6px 0; font-size: 20px; }}
        .badge {{ display: inline-block; background: #0284c7; color: #ffffff; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: bold; }}
        .field {{ margin-bottom: 14px; font-size: 14px; line-height: 1.6; }}
        .field strong {{ color: #94a3b8; display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .field span {{ color: #f8fafc; font-size: 15px; }}
        .message-box {{ background: #0f172a; border-left: 4px solid #38bdf8; padding: 14px; border-radius: 6px; margin-top: 8px; color: #e2e8f0; }}
        .footer {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid #334155; font-size: 12px; color: #64748b; text-align: center; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <span class="badge">{category}</span>
            <h2>New Inquiry Received</h2>
            <p style="margin: 0; color: #94a3b8; font-size: 13px;">DAV Cloud Solutions Lead Intake Engine</p>
        </div>

        <div class="field">
            <strong>Client / Student Name</strong>
            <span>{name}</span>
        </div>

        <div class="field">
            <strong>Email Address</strong>
            <span><a href="mailto:{email}" style="color: #38bdf8; text-decoration: none;">{email}</a></span>
        </div>

        <div class="field">
            <strong>Phone / WhatsApp</strong>
            <span>{phone}</span>
        </div>

        <div class="field">
            <strong>Project / Topic</strong>
            <span>{project_name}</span>
        </div>

        {f'<div class="field"><strong>Requested Schedule</strong><span>{schedule}</span></div>' if schedule else ''}

        <div class="field">
            <strong>Message / Scope Details</strong>
            <div class="message-box">{message}</div>
        </div>

        <div class="footer">
            Logged into MongoDB database and dispatched via DAV Cloud Solutions Core.
        </div>
    </div>
</body>
</html>
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"DAV Cloud Portal <{mail_sender}>"
    msg["To"] = admin_email
    if email and "@" in email:
        msg["Reply-To"] = email

    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    if not mail_username or not mail_password:
        current_app.logger.warning("SMTP Mailer credentials missing. Admin inquiry email simulated.")
        print(f"[SIMULATED ADMIN INQUIRY EMAIL] {subject} from {email}")
        return True

    # Dispatch in background thread
    threading.Thread(
        target=_dispatch_smtp_background,
        args=(msg, admin_email, mail_server, mail_port, mail_username, mail_password, mail_sender),
        daemon=True
    ).start()

    return True