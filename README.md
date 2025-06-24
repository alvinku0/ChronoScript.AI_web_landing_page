# ChronoScript.AI Landing Page

A responsive landing page for ChronoScript.AI built with Flask and Tailwind CSS.

## Features

- Responsive design for mobile and desktop
- Smooth scrolling navigation
- Modern gradient hero section
- Product features showcase
- Security infrastructure section
- About section
- Contact form with map placeholder
- Mobile-friendly navigation menu

## Technology Stack

- **Backend**: Flask
- **Frontend**: HTML5, Tailwind CSS
- **JavaScript**: Vanilla JS for interactivity
- **Fonts**: Google Fonts (Inter)

## Sections

1. **Home** - Hero section with main value proposition
2. **Product** - Three-column feature showcase
3. **Data & Security** - Security infrastructure overview
4. **About** - Company information in two columns
5. **Contact** - Contact form and location

The navigation automatically scrolls to the corresponding sections when clicked.

## Database Setup

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
   Environment=SECRET_KEY=70dcxxxxxxxxxxxxxxxxxxxxxxx
   Environment=ADMIN_PASSWORD=xxxxxxxxxxxxxxxxxxxxxxxxxx
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
  systemctl restart ChronoScript
  ```

- **Check service status:**
  ```bash
  systemctl status ChronoScript
  systemctl status nginx
  ```

### Security Features Implemented
- ✅ Rate limiting (3 submissions/hour per IP)
- ✅ Input validation and sanitization
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ XSS protection headers
- ✅ CSRF protection considerations
- ✅ Secure session handling
- ✅ Email validation with regex
- ✅ Input length limits
- ✅ Error handling without information disclosure

### (to-do) Additional Production Recommendations

1. **SSL/HTTPS**: Use Let's Encrypt or similar
2. **Firewall**: Configure UFW or iptables
3. **Monitoring**: Add logging and monitoring
4. **Updates**: Regular security updates
5. **Backup**: Automated database backups
6. **CDN**: Consider CloudFlare for additional protection

### (to-do) Security Considerations Still Needed

1. **CSRF Tokens**: Consider Flask-WTF for forms
2. **Content Security Policy**: Fine-tune CSP headers
3. **Logging**: Add security event logging
4. **Health Checks**: Add /health endpoint for monitoring