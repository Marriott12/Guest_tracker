"""
Additional settings and deployment notes for Guests app (check-in sessions & scanner libs)

Add these to your production configuration (e.g., environment variables or `settings_local.py`) to
ensure safe operation of shared check-in sessions and scanning.

Recommended settings:

- CHECKIN_SESSION_ENFORCE (bool): When True, API check-ins require an active check-in session for the event.
  Default: False (development). Set to True in staging/production after you configure a shared cache.

- CHECKIN_SESSION_TIMEOUT (int): Timeout in seconds for session cache entries. Default: 8 hours (28800).

- CHECKIN_REQUIRE_BARCODE (bool): When True, require a scanned `barcode_number` for check-in instead of
  accepting `unique_code`. Default: False.

Shared cache (required for multi-process ushers):
- The app uses Django's cache to publish the current active session (cache key pattern: `guests:checkin_session:{event_id}`).
- For multi-server or multi-process deployments use a shared cache backend such as Redis or Memcached.
  Example (Redis):

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

- After configuring a shared cache, set `CHECKIN_SESSION_ENFORCE=True` in staging to validate the
  enforcement behavior before enabling in production.

Vendorizing scanner libraries for offline use:
- The project's scanner UI loads `quagga.min.js` and `jsqr.min.js` from `guests/static/guests/js/` if present.
- To vendor the libraries for air-gapped deployments, run the provided PowerShell script from the
  project root (Windows):

  PowerShell command:
  .\scripts\vendor_scanner_libs.ps1

- Then collect static files:
  python manage.py collectstatic --noinput

Security & production notes:
- Ensure `DEBUG=False` in production and set `ALLOWED_HOSTS` appropriately.
- Configure a proper email backend (SMTP or transactional provider) and set `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD`.
- Use HTTPS, secure cookies, and HSTS as appropriate for your environment.
- Use a process manager (systemd, supervisor) and an application server (Gunicorn/uvicorn) behind a reverse proxy.

"""
