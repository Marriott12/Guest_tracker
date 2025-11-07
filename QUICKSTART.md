# Quick Start Guide - Automated Deployment
# Zambia Army Guest Tracking System

## Option 1: Automated Script Deployment (Recommended)

### What the script does automatically:
✅ Creates .env file with your configuration  
✅ Generates secure SECRET_KEY  
✅ Creates passenger_wsgi.py  
✅ Installs all dependencies  
✅ Installs MySQL client  
✅ Runs database migrations  
✅ Creates superuser account  
✅ Collects static files  
✅ Sets up directories and permissions  

### What you MUST do manually in cPanel first:
1. Create Python App (Setup Python App)
2. Create MySQL database and user
3. Upload project files (via Git or File Manager)

---

## Step-by-Step Quick Deployment

### PART 1: Manual cPanel Setup (5 minutes)

#### Step 1: Create Python App
1. cPanel → **Setup Python App** → **Create Application**
2. Settings:
   - Python Version: **3.11** (or latest)
   - Application Root: **guest_tracker**
   - Application URL: **/** (for main domain)
3. Click **Create**
4. **COPY the Virtual Environment Path** shown (you'll need this)

#### Step 2: Create Database
1. cPanel → **MySQL Databases**
2. Create Database: `username_guesttracker`
3. Create User: `username_dbuser` (generate strong password)
4. Add user to database with ALL PRIVILEGES
5. **SAVE database name, user, and password**

#### Step 3: Upload Project
**Option A - Via Git (Recommended):**
1. cPanel → **Terminal**
2. Run:
```bash
cd ~
git clone https://github.com/Marriott12/Guest_tracker.git guest_tracker
```

**Option B - Via File Upload:**
1. Download ZIP from GitHub
2. cPanel → **File Manager** → Upload ZIP
3. Extract to `guest_tracker` folder

---

### PART 2: Run Automated Script (10 minutes)

#### Step 4: Run the Deployment Script
1. In cPanel Terminal:
```bash
cd ~/guest_tracker
bash cpanel_auto_deploy.sh
```

2. The script will ask you for:
   - Virtual environment path (paste from Step 1)
   - Database name (from Step 2)
   - Database user (from Step 2)
   - Database password (from Step 2)
   - Your domain name
   - Email configuration (optional - can configure later)
   - Superuser username and password

3. Wait for script to complete (5-10 minutes)

---

### PART 3: Final cPanel Configuration (5 minutes)

#### Step 5: Configure Static Files
1. cPanel → **Setup Python App** → Edit your app
2. Scroll to **Static Files** section
3. Click **Add** twice to create two entries:

**Entry 1:**
- URL: `/static`
- Path: `/home/username/guest_tracker/staticfiles`

**Entry 2:**
- URL: `/media`
- Path: `/home/username/guest_tracker/media`

4. Click **Save**

#### Step 6: Enable SSL
1. cPanel → **SSL/TLS Status**
2. Find your domain → Click **Run AutoSSL**
3. Wait for completion

#### Step 7: Restart Application
1. cPanel → **Setup Python App**
2. Find your application
3. Click the **Restart** button (circular arrow)

---

### PART 4: Test & Verify

#### Step 8: Test Your Site
1. Visit: `https://yourdomain.com`
   - Should see landing page ✓
2. Visit: `https://yourdomain.com/admin`
   - Login with superuser credentials ✓
3. Test creating an event ✓
4. Test adding guests ✓

---

## Troubleshooting the Script

### If script fails at MySQL client installation:
```bash
source /home/username/virtualenv/guest_tracker/3.11/bin/activate
cd ~/guest_tracker
pip install pymysql

# Add to guest_tracker/__init__.py:
echo "import pymysql; pymysql.install_as_MySQLdb()" >> guest_tracker/__init__.py
```

### If migrations fail:
- Check database credentials in `.env`
- Verify database user has ALL PRIVILEGES
- Test connection: `mysql -u username_dbuser -p username_guesttracker`

### If static files don't load:
- Verify paths in cPanel → Setup Python App → Static Files
- Check permissions: `chmod 755 staticfiles media`

### View error logs:
```bash
tail -f ~/guest_tracker/logs/django.log
```

Or in cPanel → Setup Python App → Log files

---

## Manual Alternative (If Script Doesn't Work)

If the automated script fails, follow the full manual guide in:
**CPANEL_DEPLOYMENT.md**

---

## Post-Deployment

### Schedule Backups
cPanel → **Cron Jobs**

Add daily backup at 2 AM:
```
0 2 * * * /home/username/virtualenv/guest_tracker/3.11/bin/python /home/username/guest_tracker/manage.py dumpdata > /home/username/guest_tracker/backups/database/backup_$(date +\%Y\%m\%d).json
```

### Update Application
When you make changes:
```bash
cd ~/guest_tracker
git pull origin main
source /home/username/virtualenv/guest_tracker/3.11/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
# Restart app in cPanel
```

---

## Time Estimate

| Task | Time |
|------|------|
| Manual cPanel setup | 5 min |
| Run automated script | 10 min |
| Final configuration | 5 min |
| Testing | 5 min |
| **Total** | **25 min** |

(vs. 2+ hours doing everything manually)

---

## Support

**Script not working?**
- Check you completed Part 1 (manual steps)
- Verify you have SSH/Terminal access enabled
- Review error messages carefully
- Fall back to CPANEL_DEPLOYMENT.md for manual steps

**Need help?**
- Check error logs in cPanel
- Review SECURITY.md and DEPLOYMENT.md
- Contact your hosting provider for cPanel-specific issues

---

🎉 **That's it! Your application should be live in under 30 minutes!**
