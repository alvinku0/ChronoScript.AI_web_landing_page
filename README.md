# ChronoScript.AI Landing Page

A responsive landing page for ChronoScript.AI built with Flask and Tailwind CSS.

## Features

- 🎨 **Modern Design**: Responsive design optimized for mobile and desktop
- 🚀 **Smooth Navigation**: Smooth scrolling navigation with animated word carousel
- 🌈 **Gradient Hero Section**: Eye-catching hero with animated elements
- 📱 **Mobile-First**: Mobile-friendly navigation menu and layouts
- 📋 **Contact System**: Advanced contact form with email notifications
- 🔒 **Security**: Production-grade security with rate limiting and input validation
- 📄 **Terms of Service**: Complete legal terms page with consistent styling
- 👑 **Admin Panel**: Secure admin interface for managing contact submissions
- ⚡ **Production ready**: Optimized for production deployment with Gunicorn

## 🛠️ Technology Stack

- **Backend**: Flask 3.1.1 with SQLAlchemy
- **Frontend**: HTML5, Tailwind CSS 4.0 (CDN)
- **JavaScript**: Vanilla JS for smooth interactions
- **Database**: SQLite (production-ready with PostgreSQL support)
- **Email**: Flask-Mail with SMTP integration
- **Security**: Flask-Limiter, comprehensive input validation
- **Server**: Gunicorn for production deployment
- **Fonts**: Google Fonts (Inter)
- **Icons**: Font Awesome 6.0

## 📄 Page Structure

### Main Landing Page (`/`)
1. **Home** - Hero section with animated word carousel and main value proposition
2. **Product** - Three-column feature showcase with hover animations
3. **Security** - Data protection and infrastructure overview with security icons
4. **About** - Company information in responsive two-column layout
5. **Contact** - Advanced contact form with real-time validation and email integration

### Additional Pages
- **Terms of Service** (`/terms`) - Complete legal terms with consistent styling
- **Admin Login** (`/admin/login`) - Secure admin authentication
- **Admin Dashboard** (`/admin/contacts`) - Contact submissions management

## 🔒 Security Features ✅

- ✅ **Rate Limiting**: 3 contact submissions per hour per IP, 20 requests/hour default
- ✅ **Input Validation**: Email regex validation, length limits, XSS prevention
- ✅ **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- ✅ **Security Headers**: CSP, HSTS, XSS protection, frame options, CSRF protection
- ✅ **Session Security**: Secure session handling with cryptographic signing
- ✅ **Admin Protection**: Password-protected admin area with session management
- ✅ **Error Handling**: Graceful error handling without information disclosure
- ✅ **Environment Variables**: Secure configuration management
- ✅ **Email Validation**: Advanced email validation with regex patterns
- ✅ **Input Sanitization**: Length limits and content filtering

## 🚀 Production Features

- 🚀 **Gunicorn Configuration**: Multi-worker production server setup (`gunicorn.conf.py`)
- 📊 **Health Monitoring**: `/health` endpoint for load balancer checks
- 📝 **Comprehensive Logging**: Rotating file handlers and structured logging (`logging_config.py`)
- 🔧 **Deployment Scripts**: Automated deployment with environment validation (`deploy.sh`)
- 🌐 **Nginx Ready**: Reverse proxy configuration included
- 📧 **Email Integration**: SMTP email notifications for contact submissions
- 🗄️ **Database Management**: Automatic database initialization and migrations

## 🔧 Configuration

### Environment Variables (`.env`)

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
DEBUG=False
FLASK_ENV=production

# Admin Login Configuration
ADMIN_PASSWORD=your-admin-password-here

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Database Configuration
DATABASE_URL=sqlite:///database/contacts.db
```

### Database Setup

The application uses SQLite for storing contact form submissions. The database will be created automatically when the application starts.

## Webapp deployment on virtual machine

1. **Connect to instance:**
   ```bash
   ssh -i /path/to/key.pem ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com
   ```

2. **Update system and install dependencies:**
   ```bash
   sudo -s # become root for installation
   apt update && apt upgrade -y
   apt install -y python3 python3-venv python3-pip git nginx
   ```

3. **Clone the repository:**
   ```bash
   git clone https://github.com/alvinku0/ChronoScript.AI_web_landing_page
   cd ChronoScript.AI_web_landing_page
   ```

4. **Set up Python virtual environment:**
   ```bash
   python3 -m venv myvenv
   source myvenv/bin/activate
   pip install -r requirements.txt
   ```

5. **Create systemd service file:**
   ```bash
   sudo vim /etc/systemd/system/ChronoScript.service
   ```

   Add the following content:
   ```ini
   [Unit]
   Description=Gunicorn service for ChronoScript.AI
   After=network.target

   [Service]
   User=ubuntu
   Group=ubuntu
   WorkingDirectory=/home/ubuntu/ChronoScript.AI_web_landing_page
   EnvironmentFile=/home/ubuntu/ChronoScript.AI_web_landing_page/.env
   ExecStart=/home/ubuntu/ChronoScript.AI_web_landing_page/myvenv/bin/gunicorn --workers 5 --bind 127.0.0.1:8000 app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   
   ```
   sudo systemctl daemon-reload
   sudo systemctl enable ChronoScript
   sudo systemctl start ChronoScript
   sudo systemctl status ChronoScript
   ```


6. **Configure Nginx reverse proxy:**
   ```bash
   sudo vim /etc/nginx/sites-available/chronoscript
   ```

   Add the following configuration:
   ```nginx
   server {
       listen 80;
       server_name _your-domain.com_;  # Accept requests to any hostname   # Can replace with domain name

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       location /static {
           alias /home/ubuntu/ChronoScript.AI_web_landing_page/static/;
       }
   }
   ```

7. **Enable the site and start services:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/chronoscript /etc/nginx/sites-enabled/
   sudo nginx -t  # Test configuration
   sudo systemctl reload nginx
   ```

### SSL Certificate

To enable HTTPS with Let's Encrypt:
```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

### Monitoring and Maintenance

- **View application logs:**
  ```bash
  journalctl -u ChronoScript -f
  ```

- **Restart the service:**
  ```bash
  sudo systemctl restart ChronoScript
  ```

- **Check service status:**
  ```bash
  systemctl status ChronoScript
  systemctl status nginx
  ```

### Security Features Implemented
- ✅ Rate limiting
- ✅ Input validation and sanitization
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ Secure session handling
- ✅ Email validation with regex
- ✅ Input length limits
- ✅ Error handling without information disclosure

### Additional Production Recommendations

1. **SSL/HTTPS**: Use Let's Encrypt or similar
2. **Firewall**: Configure UFW or iptables
3. **Monitoring**: Add logging and monitoring
4. **Updates**: Regular security updates
5. **Backup**: Automated database backups
6. **CDN**: Consider CloudFlare for additional protection
7. **CSRF Tokens**: Consider Flask-WTF for forms
8. **Content Security Policy**: Fine-tune CSP headers
9. **Logging**: Add security event logging
10. **Health Checks**: Add /health endpoint for monitoring
