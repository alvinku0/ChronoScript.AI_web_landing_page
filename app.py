from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from database.models import db, Contact, init_db
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
from flask_mail import Mail, Message
import os
import re

app = Flask(__name__)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["20 per hour"],
    storage_uri="memory://",
)

# Secret key to cryptographically sign session cookies
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise ValueError("SECRET_KEY environment variable is required.")

# Admin password to read contacts information
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD environment variable is required")

# Validate production environment variables
required_env_vars = ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
    print("Email functionality may not work properly")

# flask_mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# SQLAlchemy configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "database", "contacts.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
init_db(app)

# Initialize Flask-Mail
mail = Mail(app)

# Security headers for production
@app.after_request
def security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; img-src 'self' data:; connect-src 'self'"
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('terms.html')

@app.route('/submit_contact', methods=['POST'])
@limiter.limit("3 per hour")
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
        
        # Sanitize inputs (basic XSS prevention)
        first_name = first_name[:100]  # Limit length
        last_name = last_name[:100] if last_name else ''
        email = email[:255]
        company_name = company_name[:200] if company_name else ''
        message = message[:5000] if message else ''  # Limit message length
        
        # Get client IP address
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        
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
            
            msg.html = f"""
<h2>New Contact Form Submission - ChronoScript.AI</h2>

<table style="border-collapse: collapse; width: 100%; max-width: 600px;">
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Name:</td>
        <td style="padding: 8px; border: 1px solid #ddd;">{first_name} {last_name}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Email:</td>
        <td style="padding: 8px; border: 1px solid #ddd;"><a href="mailto:{email}">{email}</a></td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Company:</td>
        <td style="padding: 8px; border: 1px solid #ddd;">{company_name if company_name else 'Not provided'}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Submission Time:</td>
        <td style="padding: 8px; border: 1px solid #ddd;">{contact.created_at}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9; font-weight: bold;">Message:</td>
        <td style="padding: 8px; border: 1px solid #ddd;">{message if message else 'No message provided'}</td>
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
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin_contacts'))
        else:
            flash('Invalid password!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    flash('Successfully logged out!', 'success')
    return redirect(url_for('admin_login'))

def require_admin():
    """Check if admin is logged in"""
    if not session.get('admin_logged_in'):
        flash('Please login to access admin area.', 'error')
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
        'error': 'Internal server error. Please try again later.'
    }), 500

@app.errorhandler(404)
def page_not_found(error):
    """Redirect all 404 errors to home page"""
    return redirect(url_for('index'))

# For production, run with Gunicorn:
#   gunicorn -w 4 -b 0.0.0.0:5001 app:app

# Local development/testing:
# if __name__ == '__main__':
#     app.run(debug=False, host='0.0.0.0', port=8000)
