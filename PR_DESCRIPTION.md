PR: Admin session audit + production readiness

Summary:
- Add admin control to start check-in sessions (creates DB `CheckInSession` and caches session payload).
- Admin forced-end now records `ended_by` and `ended_at` in DB.
- Admin Active Sessions page now displays recent DB sessions and offers links to the CheckInSession changelist filtered by event.
- Add vendor helper script to download `quagga.min.js` and `jsqr.min.js` and integrate into staticfiles.
- Add deployment checklist and settings adjustments to support Redis and environment-based `DEBUG`.

Changes to review:
- `guests/admin.py` : start/end session handling + include recent DB sessions
- `guests/templates/admin/guests/active_sessions.html` : show recent DB sessions and Start button
- `guest_tracker/settings.py` : allow `DEBUG` from env, optional `REDIS_URL` based CACHES
- `scripts/vendor_scanner_libs.ps1` : helper to vendor scanner libs
- `guests/settings_additions.py` and `DEPLOYMENT.md` : documentation
- `guests/tests/test_admin_sessions.py` : tests for admin start/end actions

Recommended merge steps:
- Ensure `django-redis` is present in production requirements if using Redis
- Configure `REDIS_URL` in environment
- Set `DEBUG=False` and `ALLOWED_HOSTS` appropriately
- Run `python manage.py migrate` and `python manage.py collectstatic` after deployment

