Deployment checklist — Guest Tracker

This document lists the recommended steps and environment variables to configure when deploying Guest Tracker to staging/production.

1) Python environment
- Python 3.11 recommended
- Install production dependencies in your environment (requirements.txt should include `django-redis` if using Redis)

2) Environment variables (example)
- SECRET_KEY: required
- DEBUG: set to `False` in production
- ALLOWED_HOSTS: comma-separated hostnames (e.g., `example.com,www.example.com`)
- DB_ENGINE / DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT: configure a production database (Postgres recommended)
- REDIS_URL: e.g., `redis://:password@redis-host:6379/1` — required for shared cache/session features
- EMAIL_BACKEND / EMAIL_HOST / EMAIL_PORT / EMAIL_USE_TLS / EMAIL_HOST_USER / EMAIL_HOST_PASSWORD: mail settings

3) Cache and sessions
- Configure Django CACHES to use Redis (example in `guests/settings_additions.py`)
- Use Redis for both caching and session storage in multi-worker environments

4) Check-in session enforcement
- Set `CHECKIN_SESSION_ENFORCE=True` in staging once shared cache is configured to prevent accidental cross-event check-ins

5) Static files
- Vendor `quagga.min.js` and `jsqr.min.js` into `guests/static/guests/js/` for offline scanner use, or ensure CDN access
- Run `python manage.py collectstatic --noinput` as part of deployment

6) Security
- Ensure `DEBUG=False`
- Set `ALLOWED_HOSTS` appropriately
- Use HTTPS; set `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True`
- Configure HSTS headers if appropriate

7) Process management
- Use Gunicorn/Uvicorn behind nginx or equivalent reverse proxy
- Use systemd/supervisor to keep processes running

8) Monitoring
- Configure Sentry or another error monitoring solution

9) Migration and rollout
- Run `python manage.py migrate` during deployment window
- Run migrations before starting app workers
- Consider running `python manage.py collectstatic` and database migrations in CI/CD

10) Post-deploy checks
- Verify the admin `Active Sessions` page lists sessions and starting/ending works
- Verify scanner UI loads `quagga.min.js` and `jsqr.min.js` either from staticfiles or CDN

