# Guest Tracker - Production Deployment Guide

## Quick Start

### 1. Environment Setup
Copy `.env.example` to `.env` and configure all variables:
```bash
cp .env.example .env
```

**Critical settings:**
- `SECRET_KEY`: Generate new key with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DEBUG=False` (MUST be False in production)
- `ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com`
- `DATABASE_URL=postgresql://user:password@localhost:5432/guest_tracker`
- `REDIS_URL=redis://localhost:6379/1`

### 2. Install Dependencies
```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
source .venv/bin/activate      # Linux/Mac

# Install production requirements
pip install -r requirements.txt
```

### 3. Database Setup
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Static Files
```bash
# Collect static files for production serving
python manage.py collectstatic --noinput
```

### 5. Redis Setup
Install and start Redis server:
```bash
# Windows (using Chocolatey)
choco install redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS (using Homebrew)
brew install redis
brew services start redis
```

### 6. Start Production Server

#### Option A: Gunicorn (Linux/Mac)
```bash
gunicorn -c gunicorn_config.py guest_tracker.wsgi:application
```

#### Option B: Manual with environment
```bash
gunicorn --bind 0.0.0.0:8000 --workers 4 guest_tracker.wsgi:application
```

#### Option C: Systemd Service (Linux)
Create `/etc/systemd/system/guest_tracker.service`:
```ini
[Unit]
Description=Guest Tracker Django App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/guest_tracker
Environment="PATH=/var/www/guest_tracker/.venv/bin"
EnvironmentFile=/var/www/guest_tracker/.env
ExecStart=/var/www/guest_tracker/.venv/bin/gunicorn \
    -c /var/www/guest_tracker/gunicorn_config.py \
    guest_tracker.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable guest_tracker
sudo systemctl start guest_tracker
sudo systemctl status guest_tracker
```

## Web Server Configuration

### Nginx Configuration
Create `/etc/nginx/sites-available/guest_tracker`:
```nginx
upstream guest_tracker {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    client_max_body_size 10M;
    
    # Static files
    location /static/ {
        alias /var/www/guest_tracker/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /var/www/guest_tracker/media/;
        expires 7d;
    }
    
    # Proxy to Gunicorn
    location / {
        proxy_pass http://guest_tracker;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/guest_tracker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL/TLS Setup with Let's Encrypt
```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is set up automatically
sudo certbot renew --dry-run
```

## Deployment Script Usage
Use the provided `deploy.ps1` script for common tasks:

```powershell
# Run all deployment tasks
.\deploy.ps1 -All

# Run migrations only
.\deploy.ps1 -Migrate

# Collect static files only
.\deploy.ps1 -CollectStatic

# Clear cache only
.\deploy.ps1 -ClearCache

# Multiple tasks
.\deploy.ps1 -Migrate -CollectStatic
```

## Environment Variables Reference

### Required
- `SECRET_KEY`: Django secret key (generate new for production)
- `DEBUG`: Set to `False`
- `ALLOWED_HOSTS`: Comma-separated domain list
- `DATABASE_URL`: PostgreSQL connection string

### Recommended
- `REDIS_URL`: Redis connection for caching (multi-server deployments)
- `EMAIL_HOST_USER`: SMTP username
- `EMAIL_HOST_PASSWORD`: SMTP password or app-specific password

### Security (Production)
- `SECURE_SSL_REDIRECT=True`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SECURE_HSTS_SECONDS=31536000`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS=True`
- `SECURE_HSTS_PRELOAD=True`

### Optional
- `CHECKIN_SESSION_ENFORCE`: Require DB session before check-ins
- `SENTRY_DSN`: Error monitoring with Sentry
- `USE_S3=True`: Use AWS S3 for static/media files
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`: S3 credentials

## Database Migration from SQLite to PostgreSQL

### 1. Dump SQLite data
```bash
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission -o datadump.json
```

### 2. Configure PostgreSQL
Update `.env` with `DATABASE_URL`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/guest_tracker
```

### 3. Create PostgreSQL database
```bash
sudo -u postgres createdb guest_tracker
sudo -u postgres psql -c "CREATE USER your_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE guest_tracker TO your_user;"
```

### 4. Run migrations on PostgreSQL
```bash
python manage.py migrate
```

### 5. Load data
```bash
python manage.py loaddata datadump.json
```

## Health Check Monitoring

### Django Management Command
Create a health check endpoint or use admin:
```bash
# Check database connectivity
python manage.py dbshell --command="SELECT 1;"

# Check Redis
python manage.py shell -c "from django.core.cache import cache; cache.set('health', 'ok', 10); print(cache.get('health'))"
```

### Process Monitoring
```bash
# Check Gunicorn status
sudo systemctl status guest_tracker

# View logs
sudo journalctl -u guest_tracker -f

# Check Nginx status
sudo systemctl status nginx
```

## Backup Strategy

### Database Backups
```bash
# PostgreSQL backup
pg_dump -U your_user guest_tracker > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated daily backups (cron)
0 2 * * * pg_dump -U your_user guest_tracker | gzip > /backups/guest_tracker_$(date +\%Y\%m\%d).sql.gz
```

### Media Files Backup
```bash
# Rsync media files
rsync -avz /var/www/guest_tracker/media/ /backups/media/

# Or use AWS S3
aws s3 sync /var/www/guest_tracker/media/ s3://your-bucket/media/
```

## Troubleshooting

### Check Logs
```bash
# Application logs
tail -f /var/www/guest_tracker/logs/django.log

# Gunicorn logs
sudo journalctl -u guest_tracker -n 100

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Common Issues

**Static files not loading:**
```bash
python manage.py collectstatic --noinput --clear
sudo systemctl restart guest_tracker
```

**Database connection errors:**
- Verify `DATABASE_URL` in `.env`
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Test connection: `psql $DATABASE_URL`

**Redis connection errors:**
- Check Redis is running: `redis-cli ping` (should return PONG)
- Verify `REDIS_URL` in `.env`

**Permission errors:**
- Check file ownership: `sudo chown -R www-data:www-data /var/www/guest_tracker`
- Check permissions: `sudo chmod -R 755 /var/www/guest_tracker`

## Performance Optimization

### Enable Redis Caching
Ensure `REDIS_URL` is set in `.env` for shared cache across workers.

### Database Connection Pooling
The settings already include `CONN_MAX_AGE=600` for connection pooling.

### Static File Compression
WhiteNoise is configured with `CompressedManifestStaticFilesStorage` for automatic Gzip compression.

### Gunicorn Workers
The `gunicorn_config.py` automatically calculates optimal worker count: `(CPU cores * 2) + 1`

## Security Checklist

- [ ] `DEBUG=False` in production
- [ ] Generate new `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` with actual domains
- [ ] Enable HTTPS/SSL with valid certificate
- [ ] Set all `SECURE_*` and `*_COOKIE_SECURE` settings to `True`
- [ ] Configure firewall (allow only 80, 443, SSH)
- [ ] Set up automated backups
- [ ] Configure error monitoring (Sentry)
- [ ] Review and restrict database user permissions
- [ ] Enable Redis authentication if exposed
- [ ] Keep dependencies updated: `pip list --outdated`

## Post-Deployment Testing

1. **Test admin access:** https://yourdomain.com/admin/
2. **Test check-in flow:** Create event, add guests, test QR/barcode scanning
3. **Test email delivery:** Send test invitation
4. **Verify Redis caching:** Check active sessions in admin
5. **Load testing:** Use tools like `ab` or `locust` to test under load
6. **Monitor error logs** for first 24 hours

## Scaling Considerations

### Horizontal Scaling
- Use load balancer (Nginx, HAProxy, AWS ELB)
- Redis required for shared session state
- Database connection pooling (PgBouncer)
- Shared media storage (S3, NFS)

### Vertical Scaling
- Increase Gunicorn workers in `gunicorn_config.py`
- Upgrade database instance
- Add more Redis memory

---

**Need help?** Check `DEPLOYMENT.md` in the repository for additional details.
