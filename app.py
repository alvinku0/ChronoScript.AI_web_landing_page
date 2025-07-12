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

# Custom modules (email_service.py)
from email_service import create_email_message, get_email_summary

# Create Flask app
app = Flask(__name__)

# =============================================================================
# CONFIGURATION & ENVIRONMENT VARIABLE
# =============================================================================

# Secret key to cryptographically sign session cookies
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise ValueError("SECRET_KEY environment variable is required.")

# Session configuration for security
app.config['SESSION_COOKIE_SECURE'] = False # True if HTTPS required in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=3)  # session timeout = 3 hours

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

# Admin password to read contacts information
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD environment variable is required")

# Hash admin password for comparison
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

# Validate production environment variables
required_env_vars = ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
    print("Email functionality may not work properly")

# Flask-Mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# =============================================================================
# EXTENSIONS INITIALIZATION
# =============================================================================

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize rate limiter (flask_limiter)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,  # With ProxyFix, this will now return the real client IP
    default_limits=["500 per day", "100 per hour", "30 per minute"],
    storage_uri="memory://",
)

# Initialize Flask-Mail
mail = Mail(app)

# Initialize database
init_db(app)

# =============================================================================
# MIDDLEWARE SETUP
# =============================================================================

# Get the real client IP address (ProxyFix)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

# Production optimization (flask_minify)
if not app.debug:
    app.config['COMPRESS_MIMETYPES'] = [
        'text/html', 'text/css', 'text/xml', 'application/json',
        'application/javascript', 'application/xml+rss',
        'application/atom+xml', 'image/svg+xml'
    ]
    minify(app=app, html=True, js=False, cssless=False)

# =============================================================================
# GLOBAL VARIABLES
# =============================================================================

# Store failed login attempts with thread safety
failed_login_attempts = {}
failed_login_lock = threading.Lock()

# =============================================================================
# BEFORE/AFTER REQUEST HANDLERS
# =============================================================================

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

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

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

# =============================================================================
# ROUTES
# =============================================================================

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
        
        # Limit length
        first_name = first_name[:100]
        last_name = last_name[:100] if last_name else ''
        email = email[:255]
        company_name = company_name[:200] if company_name else ''
        message = message[:5000] if message else ''
        
        # Get client IP address
        ip_address = request.remote_addr  # ProxyFix uses the real client IP
        
        # Create new contact using SQLAlchemy
        contact = Contact.create_contact(first_name, last_name, email, company_name, message, ip_address)
        
        # Send email notification
        try:
            # Create secure email message using email service
            mail_config = {
                'sender': app.config['MAIL_DEFAULT_SENDER'],
                'recipients': [app.config['MAIL_DEFAULT_SENDER']]
            }
            
            msg = create_email_message(contact.to_dict(), mail_config)
            
            # Send the email
            mail.send(msg)
            print(f"Email notification sent for contact submission {contact.id}")
            print(f"Contact summary: {get_email_summary(contact.to_dict())}")
            
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

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(RateLimitExceeded)
def handle_rate_limit_exceeded(e):
    """Handle rate limit exceeded errors for contact form submissions"""
    return jsonify({
        'error': 'You have submitted too many requests. Please email us for support.',
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

# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

# For production, run with Gunicorn:
#   gunicorn -w 4 -b 0.0.0.0:5001 app:app

# Local development/testing:
# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=8000)
