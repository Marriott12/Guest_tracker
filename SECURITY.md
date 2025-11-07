# Security Guide - Zambia Army Guest Tracking System

## 🔐 Critical Security Tasks

### 1. Generate New SECRET_KEY (REQUIRED)

**Before deploying to production, you MUST generate a new secret key:**

```powershell
# In PowerShell
cd c:\wamp64\www\guest_tracker
.\.venv\Scripts\activate
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and update `.env`:
```
SECRET_KEY=<paste-your-new-secret-key-here>
```

### 2. Change Default Admin Credentials (REQUIRED)

**Current admin credentials are publicly known and MUST be changed:**

```powershell
python manage.py createsuperuser
```

Create a new admin with:
- Strong username (not "Admin")
- Strong password (minimum 12 characters, mix of upper/lower/numbers/symbols)
- Valid email address

Then delete the old admin account via Django admin panel.

### 3. Configure HTTPS (REQUIRED for Production)

**Never run in production without HTTPS!**

Update `.env`:
```
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### 4. Set Production Allowed Hosts

Update `.env` with your actual domain(s):
```
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### 5. Disable Debug Mode

Update `.env`:
```
DEBUG=False
```

## 📧 Email Security

### Gmail Configuration (Two-Step Example)

1. Enable 2-Step Verification in your Google Account
2. Generate an App Password:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other"
   - Name it "Zambia Army Guest Tracker"
   - Copy the 16-character password

3. Update `.env`:
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@zambiaarmyevents.com
```

### Alternative: SendGrid (Recommended for Production)

1. Create SendGrid account: https://sendgrid.com
2. Generate API key
3. Update `.env`:
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<your-sendgrid-api-key>
DEFAULT_FROM_EMAIL=noreply@zambiaarmyevents.com
```

## 🗄️ Database Security

### PostgreSQL Setup (Recommended for Production)

1. Install PostgreSQL
2. Create database and user:
```sql
CREATE DATABASE guest_tracker_db;
CREATE USER guest_tracker_user WITH PASSWORD 'your-strong-password';
GRANT ALL PRIVILEGES ON DATABASE guest_tracker_db TO guest_tracker_user;
ALTER DATABASE guest_tracker_db OWNER TO guest_tracker_user;
```

3. Update `.env`:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=guest_tracker_db
DB_USER=guest_tracker_user
DB_PASSWORD=your-strong-password
DB_HOST=localhost
DB_PORT=5432
```

4. Migrate data:
```powershell
python manage.py migrate
```

### Database Backup Schedule

**Automated Daily Backups (Windows Task Scheduler):**

1. Open Task Scheduler
2. Create New Task:
   - Name: "Guest Tracker DB Backup"
   - Trigger: Daily at 2:00 AM
   - Action: Run PowerShell script
   - Script: `C:\wamp64\www\guest_tracker\backup_database.ps1`

## 🛡️ Additional Security Measures

### 1. Rate Limiting

Already implemented on:
- Invitation sending (50 per hour per user)
- Invitation resending (20 per hour per user)

### 2. File Upload Security

QR codes and barcodes are auto-generated and stored in `/media/`

**For production, use AWS S3:**

Update `.env`:
```
USE_S3=True
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=zambia-army-guest-tracker
AWS_S3_REGION_NAME=us-east-1
```

### 3. CSRF Protection

Already configured in `settings.py`:
- CSRF tokens required on all POST requests
- CSRF cookies are httponly
- SameSite cookies enabled

### 4. XSS Protection

Already configured:
- Browser XSS filter enabled
- Content type sniffing disabled
- X-Frame-Options set to DENY

### 5. Session Security

Sessions expire after 24 hours (86400 seconds)
- Session cookies are httponly
- Session cookies are secure (when HTTPS enabled)

## 🔍 Security Monitoring

### 1. Enable Sentry (Error Tracking)

1. Create account: https://sentry.io
2. Create new Django project
3. Copy DSN
4. Update `.env`:
```
SENTRY_DSN=your-sentry-dsn
```

### 2. Review Logs Regularly

Logs are stored in: `C:\wamp64\www\guest_tracker\logs\django.log`

**Check for:**
- Failed login attempts
- Unusual activity patterns
- Error spikes
- Rate limit violations

### 3. Set Up Admin Email Alerts

Update `.env` with admin email:
```
ADMIN_EMAIL=admin@zambiaarmyevents.com
```

You'll receive emails for:
- Server errors (500)
- Critical exceptions
- Security warnings

## 🔐 Password Policy

Enforce strong passwords through Django's built-in validators (already configured):
- Minimum 8 characters
- Not too similar to user information
- Not a common password
- Not entirely numeric

## 🚨 Security Incident Response

### If you suspect a breach:

1. **Immediately**:
   - Change all admin passwords
   - Rotate SECRET_KEY
   - Review access logs
   - Disable compromised accounts

2. **Investigate**:
   - Check `logs/django.log` for suspicious activity
   - Review database for unauthorized changes
   - Check file system for modifications

3. **Restore** (if necessary):
   - Use backup: `.\restore_database.ps1`
   - Restore from known good backup
   - Review changes before going live

4. **Prevent Future Incidents**:
   - Update all dependencies
   - Review and strengthen security settings
   - Implement additional monitoring
   - Conduct security audit

## 📋 Security Checklist

Before going live, verify:

- [ ] New SECRET_KEY generated and set in `.env`
- [ ] DEBUG=False in `.env`
- [ ] ALLOWED_HOSTS configured with actual domain(s)
- [ ] Default admin account deleted
- [ ] Strong passwords enforced
- [ ] HTTPS enabled (SSL certificate installed)
- [ ] All security headers enabled
- [ ] Production database configured (PostgreSQL)
- [ ] Database backups scheduled
- [ ] Email sending configured and tested
- [ ] Sentry configured for error tracking
- [ ] Logs being monitored
- [ ] Rate limiting tested
- [ ] File uploads secured (S3 recommended)
- [ ] Admin email notifications configured
- [ ] Security updates applied
- [ ] Firewall configured
- [ ] Only necessary ports open (80, 443)
- [ ] Server hardening completed

## 🔗 Resources

- Django Security: https://docs.djangoproject.com/en/stable/topics/security/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Django Deployment Checklist: https://docs.djangoproject.com/en/stable/howto/deployment/checklist/

## 📞 Security Contacts

If you discover a security vulnerability:
1. **DO NOT** open a public GitHub issue
2. Email: security@zambiaarmyevents.com (update with actual contact)
3. Include details but keep confidential
4. Allow time for patch before public disclosure
