# Step-by-Step cPanel Deployment Guide
# Zambia Army Guest Tracking System

## Prerequisites
- cPanel hosting account with Python support
- SSH access enabled
- Domain name configured
- MySQL or PostgreSQL database support

---

## PART 1: CPANEL INITIAL SETUP

### Step 1: Access cPanel
1. Log in to your cPanel account
2. URL usually: `https://yourdomain.com/cpanel` or `https://yourdomain.com:2083`

### Step 2: Set Up Python Application
1. In cPanel, search for "**Setup Python App**" or "**Python Selector**"
2. Click on it to open

### Step 3: Create Python Application
1. Click "**Create Application**"
2. Configure:
   - **Python Version**: Select **3.11** or **3.10** (latest available)
   - **Application Root**: `guest_tracker` (or your preferred folder name)
   - **Application URL**: Leave as `/` for main domain, or `/app` for subdirectory
   - **Application Startup File**: `passenger_wsgi.py`
   - **Application Entry Point**: `application`
3. Click "**Create**"

### Step 4: Note Important Information
After creation, cPanel will show:
- **Virtual Environment Path**: `/home/username/virtualenv/guest_tracker/3.11`
- **Command to enter environment**: Copy this command (you'll need it)

---

## PART 2: DATABASE SETUP

### Step 5: Create MySQL Database
1. In cPanel, go to "**MySQL Databases**"
2. Under "**Create New Database**":
   - Database Name: `username_guesttracker` (cPanel adds prefix automatically)
   - Click "**Create Database**"

### Step 6: Create Database User
1. Scroll to "**MySQL Users**" → "**Add New User**"
2. Configure:
   - Username: `username_dbuser`
   - Password: Generate a strong password (click "**Password Generator**")
   - **SAVE THIS PASSWORD** - you'll need it
3. Click "**Create User**"

### Step 7: Assign User to Database
1. Scroll to "**Add User To Database**"
2. Select:
   - User: `username_dbuser`
   - Database: `username_guesttracker`
3. Click "**Add**"
4. On next page, check "**ALL PRIVILEGES**"
5. Click "**Make Changes**"

### Step 8: Note Database Information
Write down:
- Database Name: `username_guesttracker`
- Database User: `username_dbuser`
- Database Password: (the one you generated)
- Database Host: `localhost` (or as shown in cPanel)

---

## PART 3: FILE UPLOAD & CONFIGURATION

### Step 9: Access File Manager
1. In cPanel, open "**File Manager**"
2. Navigate to your application root folder (e.g., `guest_tracker`)
3. If folder doesn't exist, create it

### Step 10: Upload Project Files

**Option A: Using Git (Recommended)**
1. In cPanel, open "**Terminal**" or use SSH
2. Navigate to home directory:
   ```bash
   cd ~
   ```
3. Clone repository:
   ```bash
   git clone https://github.com/Marriott12/Guest_tracker.git guest_tracker
   cd guest_tracker
   ```

**Option B: Upload ZIP File**
1. On your local machine, compress the `guest_tracker` folder (exclude `.venv`, `db.sqlite3`, `media`)
2. In cPanel File Manager, navigate to the application folder
3. Click "**Upload**"
4. Select your ZIP file and upload
5. After upload, right-click the ZIP → "**Extract**"

### Step 11: Create .env File
1. In File Manager, navigate to your `guest_tracker` folder
2. Click "**+ File**" to create new file
3. Name it `.env`
4. Right-click `.env` → "**Edit**"
5. Copy and paste this content (update with YOUR values):

```env
# Django Settings
SECRET_KEY=GENERATE-A-NEW-SECRET-KEY-HERE
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database Configuration (MySQL for cPanel)
DB_ENGINE=django.db.backends.mysql
DB_NAME=username_guesttracker
DB_USER=username_dbuser
DB_PASSWORD=your-database-password-here
DB_HOST=localhost
DB_PORT=3306

# Email Configuration (Example with Gmail)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@zambiaarmyevents.com

# Security Settings (IMPORTANT for Production)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Time Zone
TIME_ZONE=Africa/Lusaka

# Media and Static Files
MEDIA_ROOT=media
STATIC_ROOT=staticfiles

# Leave these empty unless using AWS S3
RECAPTCHA_PUBLIC_KEY=
RECAPTCHA_PRIVATE_KEY=
```

6. Click "**Save Changes**"

### Step 12: Generate SECRET_KEY
1. In cPanel Terminal, activate virtual environment:
   ```bash
   source /home/username/virtualenv/guest_tracker/3.11/bin/activate
   cd ~/guest_tracker
   ```
2. Generate SECRET_KEY:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
3. Copy the output
4. Edit `.env` file and replace `GENERATE-A-NEW-SECRET-KEY-HERE` with the generated key

---

## PART 4: INSTALL DEPENDENCIES

### Step 13: Activate Virtual Environment
1. In cPanel Terminal:
   ```bash
   source /home/username/virtualenv/guest_tracker/3.11/bin/activate
   cd ~/guest_tracker
   ```
   (Replace `username` and `3.11` with your actual values)

### Step 14: Install MySQL Client
```bash
pip install mysqlclient
```

If that fails, try:
```bash
pip install pymysql
```

Then add to `guest_tracker/__init__.py`:
```python
import pymysql
pymysql.install_as_MySQLdb()
```

### Step 15: Install All Dependencies
```bash
pip install -r requirements.txt
```

Wait for all packages to install (may take 5-10 minutes)

---

## PART 5: CONFIGURE PASSENGER WSGI

### Step 16: Create passenger_wsgi.py
1. In File Manager, navigate to `guest_tracker` folder
2. Create new file: `passenger_wsgi.py`
3. Add this content:

```python
import os
import sys

# Add your project directory to the sys.path
project_home = '/home/username/guest_tracker'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'guest_tracker.settings'

# Activate virtual environment
activate_this = '/home/username/virtualenv/guest_tracker/3.11/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Import Django application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

4. **IMPORTANT**: Replace `/home/username/` with your actual cPanel username
5. Save the file

---

## PART 6: RUN DJANGO SETUP COMMANDS

### Step 17: Run Migrations
```bash
cd ~/guest_tracker
source /home/username/virtualenv/guest_tracker/3.11/bin/activate
python manage.py migrate
```

### Step 18: Create Superuser
```bash
python manage.py createsuperuser
```

Follow prompts:
- Username: (choose a strong username, NOT "Admin")
- Email: your-email@domain.com
- Password: (strong password, minimum 12 characters)

### Step 19: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

This creates the `staticfiles` folder with all CSS, JS, images

---

## PART 7: SET UP STATIC FILES SERVING

### Step 20: Configure Static Files in cPanel
1. Go back to "**Setup Python App**"
2. Find your application and click the pencil icon to edit
3. Scroll to "**Static Files**"
4. Add two entries:

**Entry 1:**
- URL: `/static`
- Path: `/home/username/guest_tracker/staticfiles`

**Entry 2:**
- URL: `/media`
- Path: `/home/username/guest_tracker/media`

5. Click "**Save**"

---

## PART 8: SSL CERTIFICATE (HTTPS)

### Step 21: Install SSL Certificate
1. In cPanel, go to "**SSL/TLS Status**"
2. Find your domain
3. Click "**Run AutoSSL**" (if available - free Let's Encrypt)
4. Wait for installation to complete

OR use "**SSL/TLS**" → "**Manage SSL Sites**" to install custom certificate

---

## PART 9: RESTART & TEST

### Step 22: Restart Application
1. Go to "**Setup Python App**"
2. Find your application
3. Click "**Restart**" button (circular arrow icon)

### Step 23: Test Your Application
1. Open browser and go to: `https://yourdomain.com`
2. You should see the landing page
3. Test: `https://yourdomain.com/admin`
4. Login with superuser credentials

### Step 24: Verify All Features
- [ ] Landing page loads
- [ ] Admin panel accessible
- [ ] Can create event
- [ ] Can add guests
- [ ] Can send invitations (test email)
- [ ] QR codes generate
- [ ] Seating chart works

---

## PART 10: TROUBLESHOOTING

### Issue: 500 Internal Server Error

**Check Error Logs:**
1. In cPanel → "**Setup Python App**"
2. Click on your app
3. Scroll down to "**Log files**"
4. Check `error.log` and `access.log`

**Common Fixes:**
1. Check `.env` file has correct database credentials
2. Verify `passenger_wsgi.py` paths are correct
3. Ensure all packages installed: `pip list`
4. Check file permissions: `chmod 755 guest_tracker`

### Issue: Static Files Not Loading

1. Verify Static Files configuration in Python App setup
2. Run: `python manage.py collectstatic --noinput`
3. Check paths in `.env`: `STATIC_ROOT=staticfiles`
4. Restart application

### Issue: Database Connection Error

1. Verify database credentials in `.env`
2. Test database access in cPanel → phpMyAdmin
3. Ensure database user has ALL PRIVILEGES
4. Try: `python manage.py dbshell` to test connection

### Issue: Import Errors

```bash
# Reinstall requirements
pip install --upgrade -r requirements.txt

# Check installed packages
pip list
```

---

## PART 11: SCHEDULE AUTOMATIC BACKUPS

### Step 25: Set Up Cron Jobs
1. In cPanel, go to "**Cron Jobs**"
2. Add new cron job for daily backup:

**Minute**: `0`  
**Hour**: `2`  
**Day**: `*`  
**Month**: `*`  
**Weekday**: `*`

**Command**:
```bash
/home/username/virtualenv/guest_tracker/3.11/bin/python /home/username/guest_tracker/manage.py dbbackup
```

3. Click "**Add New Cron Job**"

---

## PART 12: FINAL CHECKLIST

Before announcing your system is live:

- [ ] SSL certificate installed (HTTPS working)
- [ ] `.env` configured with strong SECRET_KEY
- [ ] DEBUG=False in `.env`
- [ ] Database created and migrated
- [ ] Superuser created (NOT using default password)
- [ ] Static files collected and serving
- [ ] Email sending tested and working
- [ ] All features tested (events, guests, invitations, QR codes)
- [ ] Backups configured
- [ ] Domain pointing to correct directory
- [ ] Error logging reviewed

---

## PART 13: ONGOING MAINTENANCE

### Daily
- Check error logs in cPanel → Python App → Log files
- Monitor email delivery

### Weekly
- Verify backups are running
- Check disk space usage
- Review access logs

### Monthly
- Update dependencies: `pip install --upgrade -r requirements.txt`
- Review security settings
- Test backup restoration

---

## SUPPORT & RESOURCES

**If you get stuck:**
1. Check error logs in cPanel
2. Review `DEPLOYMENT.md` and `SECURITY.md` in your project
3. Contact your hosting provider's support
4. Check Django documentation: https://docs.djangoproject.com/

**Important Files:**
- `.env` - Configuration (NEVER commit to Git)
- `passenger_wsgi.py` - Application entry point
- `requirements.txt` - Dependencies list
- `manage.py` - Django management commands

---

## Quick Reference Commands

**Activate Environment:**
```bash
source /home/username/virtualenv/guest_tracker/3.11/bin/activate
cd ~/guest_tracker
```

**Run Migrations:**
```bash
python manage.py migrate
```

**Create Superuser:**
```bash
python manage.py createsuperuser
```

**Collect Static Files:**
```bash
python manage.py collectstatic --noinput
```

**Restart App:**
Go to cPanel → Setup Python App → Click Restart button

**View Logs:**
```bash
tail -f ~/guest_tracker/logs/django.log
```

---

🎉 **Congratulations! Your Zambia Army Guest Tracking System is now live on cPanel!**
