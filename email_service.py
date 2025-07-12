"""
Email Service Module for ChronoScript.AI

This module handles secure email template generation and HTML sanitization
for contact form submissions. All user input is sanitized to prevent XSS
and HTML injection attacks.
"""

import bleach
from markupsafe import Markup
from flask_mail import Message


# Configure bleach for HTML sanitization
BLEACH_CONFIG = {
    'tags': [],           # No HTML tags allowed in user input
    'attributes': {},     # No attributes allowed
    'strip': True,        # Strip disallowed tags instead of escaping
    'strip_comments': True
}


def sanitize_html_content(content):
    """Sanitize HTML content using bleach for robust security"""
    if not content:
        return ''
    return bleach.clean(str(content), **BLEACH_CONFIG)


def create_email_from_html_template(contact_data):
    """Create a secure HTML email template with proper sanitization"""
    # Sanitize all input data
    sanitized_data = {
        'first_name': sanitize_html_content(contact_data.get('first_name', '')),
        'last_name': sanitize_html_content(contact_data.get('last_name', '')),
        'email': sanitize_html_content(contact_data.get('email', '')),
        'company_name': sanitize_html_content(contact_data.get('company_name', '')),
        'message': sanitize_html_content(contact_data.get('message', '')),
        'created_at': sanitize_html_content(str(contact_data.get('created_at', ''))),
        'ip_address': sanitize_html_content(contact_data.get('ip_address', ''))
    }
    
    # Safe template using format()
    email_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Contact Submission - ChronoScript.AI</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-bottom: 20px; }}
        .content-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        .content-table th {{ background-color: #f8f9fa; padding: 12px; text-align: left; border: 1px solid #dee2e6; font-weight: bold; }}
        .content-table td {{ padding: 12px; border: 1px solid #dee2e6; vertical-align: top; }}
        .message-content {{ max-width: 100%; word-wrap: break-word; white-space: pre-wrap; }}
        .footer {{ color: #666; font-size: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; }}
        .email-link {{ color: #667eea; text-decoration: none; }}
        .email-link:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <h2 class="header">New Contact Form Submission - ChronoScript.AI</h2>
        
        <table class="content-table">
            <tr>
                <th style="width: 150px;">Name:</th>
                <td>{full_name}</td>
            </tr>
            <tr>
                <th>Email:</th>
                <td><a href="mailto:{email}" class="email-link">{email}</a></td>
            </tr>
            <tr>
                <th>Company:</th>
                <td>{company}</td>
            </tr>
            <tr>
                <th>Submission Time:</th>
                <td>{submission_time}</td>
            </tr>
            <tr>
                <th>IP Address:</th>
                <td>{ip_address}</td>
            </tr>
            <tr>
                <th>Message:</th>
                <td class="message-content">{message}</td>
            </tr>
        </table>
        
        <div class="footer">
            <p>This email was automatically generated from the ChronoScript.AI contact form.</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Format the template with sanitized data
    formatted_email = email_template.format(
        full_name=f"{sanitized_data['first_name']} {sanitized_data['last_name']}".strip(),
        email=sanitized_data['email'],
        company=sanitized_data['company_name'] or 'Not provided',
        submission_time=sanitized_data['created_at'],
        ip_address=sanitized_data['ip_address'] or 'Not available',
        message=sanitized_data['message'] or 'No message provided'
    )
    
    return Markup(formatted_email)


def create_email_from_text_template(contact_data):
    """Create a secure plain text email with proper sanitization"""
    # Sanitize all input data for text email
    sanitized_data = {
        'first_name': bleach.clean(str(contact_data.get('first_name', '')), strip=True),
        'last_name': bleach.clean(str(contact_data.get('last_name', '')), strip=True),
        'email': bleach.clean(str(contact_data.get('email', '')), strip=True),
        'company_name': bleach.clean(str(contact_data.get('company_name', '')), strip=True),
        'message': bleach.clean(str(contact_data.get('message', '')), strip=True),
        'created_at': str(contact_data.get('created_at', '')),
        'ip_address': bleach.clean(str(contact_data.get('ip_address', '')), strip=True)
    }
    
    text_template = """
New Contact Form Submission - ChronoScript.AI:

Name: {full_name}
Email: {email}
Company: {company}
Submission Time: {submission_time}
IP Address: {ip_address}

Message:
{message}

---
This email was automatically generated from the ChronoScript.AI contact form.
"""
    
    return text_template.format(
        full_name=f"{sanitized_data['first_name']} {sanitized_data['last_name']}".strip(),
        email=sanitized_data['email'],
        company=sanitized_data['company_name'] or 'Not provided',
        submission_time=sanitized_data['created_at'],
        ip_address=sanitized_data['ip_address'] or 'Not available',
        message=sanitized_data['message'] or 'No message provided'
    )


def create_email_message(contact_data, mail_config):
    """
    Create a complete Flask-Mail Message object for contact form submissions
    
    Args:
        contact_data (dict): Contact form data
        mail_config (dict): Mail configuration with 'sender' and 'recipients'
    
    Returns:
        Message: Flask-Mail Message object ready to send
    """
    msg = Message(
        subject="New Contact Submission - ChronoScript.AI",
        sender=mail_config.get('sender'),
        recipients=mail_config.get('recipients', [])
    )
    
    # Set email body (text version)
    msg.body = create_email_from_text_template(contact_data)
    
    # Set email HTML (HTML version)
    msg.html = create_email_from_html_template(contact_data)
    
    return msg


# Email service utility functions
def get_email_summary(contact_data):
    """Get a brief summary of the contact submission for logging"""
    name = f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip()
    email = contact_data.get('email', 'Unknown')
    company = contact_data.get('company_name', 'No company')
    
    return f"Contact from {name} ({email}) at {company}"
