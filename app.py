from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from database.models import db, Contact, init_db
import os

app = Flask(__name__)

# Secret key to cryptographically sign session cookies
app.secret_key = os.environ.get('SECRET_KEY')

# Admin password to read contacts information
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

# SQLAlchemy configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "database", "contacts.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
init_db(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    try:
        # Get form data
        first_name = request.form.get('firstName', '').strip()
        last_name = request.form.get('lastName', '').strip()
        email = request.form.get('email', '').strip()
        company_name = request.form.get('companyName', '').strip()
        message = request.form.get('message', '').strip()
        
        # Basic validation
        if not first_name:
            return jsonify({'success': False, 'error': 'First name is required'}), 400
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        # Basic email validation
        if '@' not in email or '.' not in email:
            return jsonify({'success': False, 'error': 'Please enter a valid email address'}), 400
        
        # Get client IP address
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        
        # Create new contact using SQLAlchemy
        contact = Contact.create_contact(first_name, last_name, email, company_name, message, ip_address)
        
        return jsonify({
            'success': True, 
            'message': 'Thank you for your message! We will get back to you soon.',
            'contact_id': contact.id
        })
        
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        print(f"Error submitting contact form: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred while submitting your message. Please try again.'}), 500

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

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.errorhandler(404)
def page_not_found(error):
    """Redirect all 404 errors to home page"""
    return redirect(url_for('index'))

# For production, run with Gunicorn:
#   gunicorn -w 4 -b 0.0.0.0:5001 app:app

# Local development/testing:
# if __name__ == '__main__':
#     app.run(debug=False, host='0.0.0.0', port=8000)
