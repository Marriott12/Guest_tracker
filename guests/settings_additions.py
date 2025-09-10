# Add this to your guest_tracker/guest_tracker/settings.py

# After creating the Django project, add 'guests' to INSTALLED_APPS:
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'guests',  # Add this line
]

# Add email configuration at the end of settings.py:

# Email Configuration
# For development (emails will appear in console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# For production (configure with your SMTP provider)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@gmail.com'
# EMAIL_HOST_PASSWORD = 'your-app-password'  # Use app password for Gmail

DEFAULT_FROM_EMAIL = 'noreply@guesttracker.com'

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files (if you plan to add photo uploads later)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
