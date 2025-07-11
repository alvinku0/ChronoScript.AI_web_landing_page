from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from database.models import db, Contact, init_db
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
from flask_mail import Mail, Message
from flask_minify import minify
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re
import html
from datetime import datetime, timedelta
import threading
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)

# Production optimization
if not app.debug:
    app.config['COMPRESS_MIMETYPES'] = [
        'text/html', 'text/css', 'text/xml', 'application/json',
        'application/javascript', 'application/xml+rss',
        'application/atom+xml', 'image/svg+xml'
    ]
    minify(app=app, html=True, js=False, cssless=False)

app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,  # With ProxyFix, this will now return the real client IP
    default_limits=["500 per day", "100 per hour", "30 per minute"],
    storage_uri="memory://",
)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Secret key to cryptographically sign session cookies
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise ValueError("SECRET_KEY environment variable is required.")

# Admin password to read contacts information
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD environment variable is required")

# Hash admin password for comparison
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

# Session configuration for security
app.config['SESSION_COOKIE_SECURE'] = False # True if HTTPS required in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=3)  # session timeout - 3 hours

# Store failed login attempts with thread safety
failed_login_attempts = {}
failed_login_lock = threading.Lock()

# Validate production environment variables
required_env_vars = ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
    print("Email functionality may not work properly")

# flask_mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# SQLAlchemy configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "database", "contacts.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# SQLite WAL mode configuration
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 100,
    'connect_args': {
        'check_same_thread': False,
        'timeout': 30
    }
}

# Initialize database
init_db(app)

# Initialize Flask-Mail
mail = Mail(app)

# HTTPS enforcement for production
@app.before_request
def force_https():
    """Force HTTPS in production""" ########### uncomment for production
    # if not app.debug and not request.is_secure:
    #     if request.headers.get('X-Forwarded-Proto') != 'https':
    #         return redirect(request.url.replace('http://', 'https://'))

# Security headers for production
@app.after_request
def security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    
    # Content Security Policy - Updated to allow all required external resources
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com",
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com",
        "img-src 'self' data: http: https:",   ####### remove http: for production
        "connect-src 'self'",
        "frame-src 'none'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        # "upgrade-insecure-requests" ######## uncomment for production
    ]
    
    response.headers['Content-Security-Policy'] = "; ".join(csp_directives)
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('terms.html')

@app.route('/health')
@limiter.exempt
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow()})

@app.route('/submit_contact', methods=['POST'])
@limiter.limit("5 per hour")
def submit_contact():
    try:
        # Get form data
        first_name = request.form.get('firstName', '').strip()
        last_name = request.form.get('lastName', '').strip()
        email = request.form.get('email', '').strip()
        company_name = request.form.get('companyName', '').strip()
        message = request.form.get('message', '').strip()
        
        # Validation
        if not first_name:
            return jsonify({'success': False, 'error': 'First name is required'}), 400
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        # Improved email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({'success': False, 'error': 'Please enter a valid email address'}), 400
        
        # Sanitize inputs (XSS prevention)
        first_name = first_name[:100]  # Limit length
        last_name = last_name[:100] if last_name else ''
        email = email[:255]
        company_name = company_name[:200] if company_name else ''
        message = message[:5000] if message else ''  # Limit message length
        
        # Get client IP address
        ip_address = request.remote_addr  # ProxyFix ensures this is the real client IP
        
        # Create new contact using SQLAlchemy
        contact = Contact.create_contact(first_name, last_name, email, company_name, message, ip_address)
        
        # Send email notification
        try:
            # Create email message
            msg = Message(
                subject="New Contact Submission - ChronoScript.AI",
                recipients=[app.config['MAIL_DEFAULT_SENDER']]  # Send to admin email
            )
            
            # Email body
            msg.body = f"""
New Contact Form Submission - ChronoScript.AI:

Name: {first_name} {last_name}
Email: {email}
Company: {company_name if company_name else 'Not provided'}
Submission Time: {contact.created_at}
Message: {message if message else 'No message provided'}
"""
            
            # HTML email with proper escaping to prevent XSS
            msg.html = f"""
<h2>New Contact Form Submission - ChronoScript.AI</h2>

<table style="border-collapse: collapse; width: 100%; max-width: 600px;">
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Name:</td>
        <td style="padding: 8px; border: 1px solid #ddd;">{html.escape(first_name)} {html.escape(last_name)}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Email:</td>
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="mailto:{html.escape(email)}">{html.escape(email)}</a></td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Company:</td>
        <td style="padding: 8px; border: 1px solid #ddd;">{html.escape(company_name) if company_name else 'Not provided'}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Submission Time:</td>
        <td style="padding: 8px; border: 1px solid #ddd;">{contact.created_at}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Message:</td>
        <td style="padding: 8px; border: 1px solid #ddd;">{html.escape(message) if message else 'No message provided'}</td>
    </tr>
</table>

<p style="color: #666; font-size: 12px; margin-top: 20px;">
    This email was automatically generated from the ChronoScript.AI contact form.
</p>
"""
            
            # Send the email
            mail.send(msg)
            print(f"Email notification sent for contact submission {contact.id}")
            
        except Exception as email_error:
            print(f"Failed to send email notification: {str(email_error)}")
            # Don't fail the entire request if email fails - contact is already saved
        
        return jsonify({
            'success': True, 
            'message': 'Thank you for your message! We will get back to you soon.',
            'contact_id': contact.id
        })
        
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        print(f"Error submitting contact form: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred while submitting your message. Please email us for support.'}), 500

@app.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def admin_login():
    """Admin login page with brute force protection"""
    if request.method == 'POST':
        password = request.form.get('password')
        client_ip = request.remote_addr
        
        with failed_login_lock:
            # Clean up old failed attempts (older than 24 hours)
            current_time = datetime.now()
            expired_ips = [ip for ip, (_, last_attempt) in failed_login_attempts.items() 
                          if (current_time - last_attempt).total_seconds() > 86400]
            for ip in expired_ips:
                del failed_login_attempts[ip]
            
            # Check if IP is temporarily blocked
            if client_ip in failed_login_attempts:
                attempts, last_attempt = failed_login_attempts[client_ip]
                if attempts >= 5 and (datetime.now() - last_attempt).total_seconds() < 900:  # 15 min lockout
                    flash('Too many failed attempts. Please try again later.', 'error')
                    return render_template('admin_login.html')
                elif (datetime.now() - last_attempt).total_seconds() >= 900:
                    # Reset attempts after lockout period
                    del failed_login_attempts[client_ip]
            
            if password and check_password_hash(ADMIN_PASSWORD_HASH, password):
                session['admin_logged_in'] = True
                session['admin_login_time'] = datetime.now().replace(tzinfo=None)
                session.permanent = True
                # Clear failed attempts on successful login
                if client_ip in failed_login_attempts:
                    del failed_login_attempts[client_ip]
                flash('Successfully logged in!', 'success')
                return redirect(url_for('admin_contacts'))
            else:
                # Track failed login attempts
                if client_ip not in failed_login_attempts:
                    failed_login_attempts[client_ip] = [1, datetime.now()]
                else:
                    failed_login_attempts[client_ip][0] += 1
                    failed_login_attempts[client_ip][1] = datetime.now()
                
                flash('Invalid password!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_login_time', None)  # Clear login time as well
    flash('Successfully logged out!', 'success')
    return redirect(url_for('admin_login'))

def require_admin():
    """Check if admin is logged in and session is valid"""
    if not session.get('admin_logged_in'):
        flash('Please login to access admin area.', 'error')
        return redirect(url_for('admin_login'))
    
    # Check session timeout
    login_time = session.get('admin_login_time')
    if login_time and isinstance(login_time, datetime):
        # Ensure both datetimes are timezone-naive
        current_time = datetime.now()
        if login_time.tzinfo is not None:
            login_time = login_time.replace(tzinfo=None)
        if (current_time - login_time).total_seconds() > 10800:  # 3 hours
            session.clear()
            flash('Session expired. Please login again.', 'error')
            return redirect(url_for('admin_login'))
    
    return None

@app.route('/admin/contacts')
def admin_contacts():
    """Admin route to view all contact submissions"""
    # Check authentication
    auth_redirect = require_admin()
    if auth_redirect:
        return auth_redirect
    
    try:
        contacts = Contact.get_all_contacts()
        return render_template('admin_contacts.html', contacts=contacts)
    except Exception as e:
        print(f"Error fetching contacts: {str(e)}")
        return "Error fetching contacts", 500

@app.errorhandler(RateLimitExceeded)
def handle_rate_limit_exceeded(e):
    """Handle rate limit exceeded errors for contact form submissions"""
    return jsonify({
        'success': False, 
        'error': 'You have submitted too many requests. Please email us for support.',
        'retry_after': getattr(e, 'retry_after', 3600)  # 1 hour in seconds
    }), 429

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    return jsonify({
        'success': False,
        'error': 'Server busy. Please try again later.'
    }), 500

@app.errorhandler(404)
def page_not_found(error):
    """Redirect all 404 errors to home page"""
    return redirect(url_for('index'))

# For production, run with Gunicorn:
#   gunicorn -w 4 -b 0.0.0.0:5001 app:app

# Local development/testing:
# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=8000)
