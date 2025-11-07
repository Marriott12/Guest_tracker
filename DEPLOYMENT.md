# Production Deployment Checklist
# Zambia Army Guest Tracking System

## Pre-Deployment Security

### 1. Environment Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Generate new SECRET_KEY (run: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- [ ] Set `DEBUG=False` in `.env`
- [ ] Update `ALLOWED_HOSTS` with your domain(s)
- [ ] Configure production database (PostgreSQL recommended)
- [ ] Set up SMTP email settings (EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

### 2. Change Default Credentials
- [ ] **CRITICAL**: Change admin password from `Admin@2025` to a strong unique password
- [ ] Create new superuser for production: `python manage.py createsuperuser`
- [ ] Delete or disable the default "Admin" account

### 3. Database Setup
- [ ] Install PostgreSQL (or your chosen database)
- [ ] Create production database
- [ ] Update `.env` with database credentials
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create database backup schedule

### 4. Static Files
- [ ] Run: `python manage.py collectstatic`
- [ ] Configure web server (Nginx/Apache) to serve static files
- [ ] Set up CDN (optional but recommended)

### 5. Media Files & Storage
- [ ] Configure AWS S3 or alternative cloud storage (recommended)
- [ ] Or ensure media directory has proper permissions
- [ ] Set up media file backups

### 6. Security Headers
- [ ] Set `SECURE_SSL_REDIRECT=True` (requires HTTPS)
- [ ] Set `SESSION_COOKIE_SECURE=True`
- [ ] Set `CSRF_COOKIE_SECURE=True`
- [ ] Set `SECURE_HSTS_SECONDS=31536000`
- [ ] Set `SECURE_HSTS_INCLUDE_SUBDOMAINS=True`
- [ ] Set `SECURE_HSTS_PRELOAD=True`
- [ ] Obtain and install SSL certificate

### 7. Error Monitoring
- [ ] Set up Sentry account (optional but recommended)
- [ ] Add `SENTRY_DSN` to `.env`
- [ ] Configure admin email notifications
- [ ] Test error reporting

### 8. Caching & Performance
- [ ] Install Redis (recommended): `apt-get install redis-server` (Linux)
- [ ] Update `REDIS_URL` in `.env`
- [ ] Configure cache settings
- [ ] Enable GZIP compression on web server

### 9. Email Configuration
- [ ] Test email sending with real SMTP server
- [ ] Verify sender reputation
- [ ] Set up SPF, DKIM, DMARC records
- [ ] Test invitation emails end-to-end

### 10. Backup & Recovery
- [ ] Schedule automatic database backups (daily recommended)
- [ ] Test backup script: `.\backup_database.ps1`
- [ ] Test restore procedure: `.\restore_database.ps1`
- [ ] Set up off-site backup storage
- [ ] Document recovery procedures

## Deployment Steps

### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3-pip python3-venv nginx postgresql redis-server

# Create application user
sudo adduser guesttracker
sudo usermod -aG www-data guesttracker
```

### 2. Application Deployment
```bash
# Clone repository
cd /var/www
git clone https://github.com/Marriott12/Guest_tracker.git
cd Guest_tracker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit with production values

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### 3. Gunicorn Setup
```bash
# Test Gunicorn
gunicorn guest_tracker.wsgi:application --bind 0.0.0.0:8000

# Create systemd service
sudo nano /etc/systemd/system/guesttracker.service
```

```ini
[Unit]
Description=Zambia Army Guest Tracker
After=network.target

[Service]
User=guesttracker
Group=www-data
WorkingDirectory=/var/www/Guest_tracker
Environment="PATH=/var/www/Guest_tracker/venv/bin"
ExecStart=/var/www/Guest_tracker/venv/bin/gunicorn --workers 3 --bind unix:/var/www/Guest_tracker/guesttracker.sock guest_tracker.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl start guesttracker
sudo systemctl enable guesttracker
sudo systemctl status guesttracker
```

### 4. Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/guesttracker
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/Guest_tracker/staticfiles/;
    }
    
    location /media/ {
        alias /var/www/Guest_tracker/media/;
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/Guest_tracker/guesttracker.sock;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/guesttracker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. SSL Certificate (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
sudo systemctl reload nginx
```

## Post-Deployment

### 1. Testing
- [ ] Access admin panel: `https://yourdomain.com/admin/`
- [ ] Create test event
- [ ] Send test invitation
- [ ] Scan test QR code
- [ ] Test RSVP submission
- [ ] Test seating chart
- [ ] Verify email delivery
- [ ] Test all dashboard features

### 2. Monitoring
- [ ] Set up server monitoring (Uptime Robot, Pingdom, etc.)
- [ ] Configure log rotation
- [ ] Set up disk space alerts
- [ ] Monitor database size
- [ ] Check error logs regularly

### 3. Performance
- [ ] Run performance tests
- [ ] Optimize database queries
- [ ] Enable caching
- [ ] Set up CDN for static files
- [ ] Monitor response times

### 4. Documentation
- [ ] Document admin procedures
- [ ] Create user guide
- [ ] Document backup/restore process
- [ ] Document deployment process
- [ ] Create runbook for common issues

### 5. Compliance
- [ ] Create privacy policy
- [ ] Create terms of service
- [ ] Document data retention policy
- [ ] Ensure GDPR compliance (if applicable)
- [ ] Set up data export functionality

## Maintenance Schedule

### Daily
- [ ] Check error logs
- [ ] Monitor server resources
- [ ] Review email delivery reports

### Weekly
- [ ] Review security logs
- [ ] Check disk space
- [ ] Review performance metrics
- [ ] Test backup restoration

### Monthly
- [ ] Update dependencies
- [ ] Security audit
- [ ] Performance optimization
- [ ] Database optimization (VACUUM, ANALYZE)

### Quarterly
- [ ] Full security review
- [ ] Disaster recovery test
- [ ] Update documentation
- [ ] Review and update SSL certificates

## Emergency Contacts

- System Administrator: _______________
- Database Administrator: _______________
- Security Officer: _______________
- Hosting Provider Support: _______________

## Rollback Plan

If deployment fails:
1. Stop the application: `sudo systemctl stop guesttracker`
2. Restore database: `.\restore_database.ps1`
3. Revert code: `git checkout previous-stable-tag`
4. Restart application: `sudo systemctl start guesttracker`

## Support Resources

- Django Documentation: https://docs.djangoproject.com/
- Project Repository: https://github.com/Marriott12/Guest_tracker
- Issue Tracker: https://github.com/Marriott12/Guest_tracker/issues
