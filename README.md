# ChronoScript.AI Landing Page

A modern, responsive landing page for ChronoScript.AI built with Flask and Tailwind CSS.

## 🛠️ Technology Stack

- **Backend**: Flask 3.1.1 with SQLAlchemy 2.0.41
- **Frontend**: HTML5, Tailwind CSS 4.0 (CDN), Vanilla JavaScript
- **Database**: SQLite with SQLAlchemy ORM
- **Email**: Flask-Mail with SMTP integration
- **Security**: Flask-Limiter, Flask-WTF CSRF protection, input validation
- **Production**: Gunicorn 23.0.0 ready
- **Performance**: Flask-Minify for production optimization
- **Fonts**: System fonts (-apple-system, BlinkMacSystemFont, Helvetica Neue)
- **Icons**: Font Awesome 6.0

## 📄 Page Structure

### Main Landing Page (`/`)
- **Hero Section**: Animated word carousel
- **Product Section**: Three-column feature showcase
- **Benefits Section**: Product benefits
- **Security Section**: Data protection and infrastructure overview
- **About Section**: Company information
- **Contact Section**: Contact submission form

### Additional Pages
- **Terms of Service** (`/terms`): Legal terms of service
- **Admin Login** (`/admin/login`): Secure admin authentication
- **Admin Dashboard** (`/admin/contacts`): Contact submissions management interface
- **Health Check** (`/health`): Health monitoring endpoint

## 🔒 Security Features

### Authentication & Authorization
- **Admin Protection**: Password-protected admin area with session management
- **Brute Force Protection**: 5 login attempts per IP with 15-minute lockout
- **Session Security**: Secure session handling with 30-minute timeout
- **CSRF Protection**: Flask-WTF CSRF protection on all forms

### Input Validation & Sanitization
- **Email Validation**: Advanced regex pattern validation
- **Input Length Limits**: Prevents buffer overflow attacks
- **XSS Prevention**: HTML escaping and input sanitization
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries

### Rate Limiting
- **Contact Form**: 3 submissions per hour per IP
- **Admin Login**: 5 attempts per minute
- **Default Limits**: 20 requests per hour per IP

### Security Headers
- **Content Security Policy**: Strict CSP with external resource controls
- **HSTS**: HTTP Strict Transport Security
- **XSS Protection**: Browser XSS filtering
- **Frame Options**: Clickjacking protection
- **Content Type Options**: MIME type sniffing protection
- **Referrer Policy**: Strict origin when cross-origin

## 🚀 Features

### Contact Management System
- **Contact Form**: Multi-field form with company information
- **Email Notifications**: Automatic HTML email notifications to admin
- **Database Storage**: SQLite database with efficient querying
- **Admin Dashboard**: View all submissions with sorting and filtering
- **IP Tracking**: Track submission IP addresses for security

### Frontend Features
- **Responsive Design**: Mobile responsive layout
- **Smooth Animations**: Intersection Observer-based animations
- **Interactive Elements**: Hover effects, smooth scrolling navigation
- **Word Carousel**: 3D animated text carousel in hero section
- **Mobile Navigation**: Collapsible mobile menu

### Performance Optimization
- **Minification**: HTML/CSS/JS minification in production
- **Caching**: Browser caching with appropriate headers
- **Lazy Loading**: Intersection Observer for performance
- **Optimized Images**: Efficient image loading and display

## 🔧 Configuration

### Environment Variables (`.env`)

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=production

# Admin Login Configuration
ADMIN_PASSWORD=your-admin-password-here

# Email Configuration (SMTP)
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
   ExecStart=/home/ubuntu/ChronoScript.AI_web_landing_page/myvenv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 app:app
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
