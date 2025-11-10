# Deployment Guide to cPanel Server

## Server Details
- **Server**: server219.web-hosting.com
- **Username**: envithcy
- **Project Path**: ~/public_html/guest_tracker
- **Virtual Env**: /home/envithcy/virtualenv/guest_tracker/3.11

## Step-by-Step Deployment Process

### 1. SSH into the Server
```bash
ssh envithcy@server219.web-hosting.com
```

### 2. Navigate to Project Directory
```bash
cd ~/public_html/guest_tracker
```

### 3. Pull Latest Changes from GitHub
```bash
git pull origin main
```

### 4. Activate Virtual Environment
```bash
source /home/envithcy/virtualenv/guest_tracker/3.11/bin/activate
```

### 5. Install/Update Dependencies
```bash
pip install -r requirements_clean.txt
```

**CRITICAL**: Make sure django-recaptcha==3.0.0 is installed (NOT 4.0.0)

### 6. Update Environment Variables
Edit the .env file on the server:
```bash
nano .env
```

Update these critical settings:
```bash
# Production Settings
DEBUG=False
ALLOWED_HOSTS=guests.envisagezm.com,www.envisagezm.com

# Database (MySQL on cPanel)
DB_ENGINE=django.db.backends.mysql
DB_NAME=envithcy_guesttracker
DB_USER=envithcy_guestuser
DB_PASSWORD=[your_mysql_password]
DB_HOST=localhost
DB_PORT=3306

# Email (Production SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mail.envisagezm.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=[your_email]
EMAIL_HOST_PASSWORD=[your_email_password]

# reCAPTCHA (Get real keys from https://www.google.com/recaptcha/admin)
RECAPTCHA_PUBLIC_KEY=[your_production_public_key]
RECAPTCHA_PRIVATE_KEY=[your_production_private_key]

# Security (Production)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### 7. Run Database Migrations
```bash
python manage.py migrate
```

### 8. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 9. Create Superuser (if needed)
```bash
python manage.py createsuperuser
```

### 10. Test the Application
```bash
python manage.py check --deploy
```

### 11. Restart the Application
Using cPanel:
1. Go to **Setup Python App** in cPanel
2. Find your application
3. Click **Restart**

Or via command line:
```bash
touch ~/public_html/guest_tracker/tmp/restart.txt
```

### 12. Verify Deployment
Visit: https://guests.envisagezm.com

Test:
- ✅ Landing page loads
- ✅ Login with reCAPTCHA works
- ✅ Admin redirects to dashboard
- ✅ Regular users redirect to guest portal
- ✅ Logout works
- ✅ Bulk resend invitations works
- ✅ Static files load properly

## Troubleshooting

### If you get package import errors:
```bash
source /home/envithcy/virtualenv/guest_tracker/3.11/bin/activate
pip list | grep django-recaptcha
# Should show: django-recaptcha 3.0.0

# If wrong version:
pip uninstall django-recaptcha
pip install django-recaptcha==3.0.0
```

### If static files don't load:
```bash
python manage.py collectstatic --noinput
chmod -R 755 staticfiles/
```

### If database errors:
```bash
python manage.py migrate --run-syncdb
```

### Check logs:
```bash
tail -f logs/django.log
```

## Quick Deploy Script
Create this file as `quick_deploy.sh`:
```bash
#!/bin/bash
cd ~/public_html/guest_tracker
git pull origin main
source /home/envithcy/virtualenv/guest_tracker/3.11/bin/activate
pip install -r requirements_clean.txt
python manage.py migrate
python manage.py collectstatic --noinput
touch ~/public_html/guest_tracker/tmp/restart.txt
echo "Deployment complete!"
```

Make it executable:
```bash
chmod +x quick_deploy.sh
```

Run it:
```bash
./quick_deploy.sh
```

## Important Notes

1. **django-recaptcha version**: MUST be 3.0.0 (version 4.0.0 is broken)
2. **reCAPTCHA keys**: Get production keys from Google reCAPTCHA admin
3. **Database**: Configure MySQL connection in .env
4. **DEBUG**: Must be False in production
5. **ALLOWED_HOSTS**: Set to your domain only
6. **Security**: Enable all HTTPS/HSTS settings in production

## Post-Deployment Checklist

- [ ] Site loads at https://guests.envisagezm.com
- [ ] SSL certificate is active
- [ ] Login with reCAPTCHA works
- [ ] Registration with reCAPTCHA works
- [ ] Admin can access organizer dashboard
- [ ] Regular users can access guest portal
- [ ] Logout functionality works
- [ ] Bulk resend invitations works
- [ ] Individual resend works
- [ ] Email sending works
- [ ] Static files (CSS/JS) load
- [ ] No errors in logs
