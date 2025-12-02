Deployment checklist — Guest Tracker

This document lists the recommended steps and environment variables to configure when deploying Guest Tracker to staging/production.

**See PRODUCTION_GUIDE.md for detailed step-by-step deployment instructions, Nginx configuration, SSL setup, and troubleshooting.**

1) Python environment
- Python 3.11 recommended
- Install production dependencies: `pip install -r requirements.txt`
- Requirements now include: `django-redis`, `gunicorn`, `psycopg2-binary`, `dj-database-url`

2) Environment variables (example)
- SECRET_KEY: required (generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- DEBUG: set to `False` in production
- ALLOWED_HOSTS: comma-separated hostnames (e.g., `example.com,www.example.com`)
- DATABASE_URL: `postgresql://user:password@localhost:5432/guest_tracker` (simplifies PostgreSQL setup)
  - OR use individual: DB_ENGINE / DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT
- REDIS_URL: e.g., `redis://localhost:6379/1` — required for shared cache/session features in multi-server deployments
- EMAIL_BACKEND / EMAIL_HOST / EMAIL_PORT / EMAIL_USE_TLS / EMAIL_HOST_USER / EMAIL_HOST_PASSWORD: mail settings
- Security settings: SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE (all True in production)

3) Cache and sessions
- Redis caching is automatically enabled when REDIS_URL is set (see settings.py)
- Use Redis for both caching and session storage in multi-worker environments

4) Check-in session enforcement
- Set `CHECKIN_SESSION_ENFORCE=True` in staging once shared cache is configured to prevent accidental cross-event check-ins

5) Static files
- Scanner libraries (`quagga.min.js`, `jsqr.min.js`) are already vendored in `guests/static/guests/js/`
- Run deployment script: `.\deploy.ps1 -CollectStatic` or `python manage.py collectstatic --noinput`

6) Security
- Ensure `DEBUG=False`
- Set `ALLOWED_HOSTS` appropriately
- Use HTTPS; set `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True`
- Configure HSTS headers: `SECURE_HSTS_SECONDS=31536000`, `SECURE_HSTS_INCLUDE_SUBDOMAINS=True`

7) Process management
- Use Gunicorn with provided config: `gunicorn -c gunicorn_config.py guest_tracker.wsgi:application`
- Use systemd/supervisor to keep processes running (see PRODUCTION_GUIDE.md for systemd service example)
- Deploy behind nginx or equivalent reverse proxy with SSL/TLS

8) Database setup
- Run migrations: `.\deploy.ps1 -Migrate` or `python manage.py migrate`
- Create superuser: `python manage.py createsuperuser`
- For SQLite to PostgreSQL migration, see PRODUCTION_GUIDE.md

9) Monitoring
- Configure Sentry or another error monitoring solution (SENTRY_DSN environment variable)
- Set up health checks and log monitoring (see PRODUCTION_GUIDE.md)

10) Deployment workflow
- Use provided deployment script: `.\deploy.ps1 -All` (runs migrations, collects static, clears cache)
- Or run manually:
  ```bash
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput --clear
  gunicorn -c gunicorn_config.py guest_tracker.wsgi:application
  ```

11) Post-deploy checks
- Verify the admin `Active Sessions` page lists sessions and starting/ending works
- Verify scanner UI loads `quagga.min.js` and `jsqr.min.js` from staticfiles
- Test check-in flow end-to-end
- Verify email delivery for invitations
- Check Redis connectivity: `redis-cli ping`
- Monitor logs for errors

