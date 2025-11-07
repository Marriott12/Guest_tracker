# reCAPTCHA Implementation Guide

## Overview
This guide covers the implementation of Google reCAPTCHA v2 (Checkbox) to protect the Guest Tracker system from spam registrations and brute-force login attempts.

## Features Added
- ✅ reCAPTCHA protection on login form
- ✅ reCAPTCHA protection on guest registration form
- ✅ Development mode support (works without keys for testing)
- ✅ Production-ready configuration via environment variables

## Installation

### 1. Install django-recaptcha Package
The package is already included in `requirements.txt`:
```bash
pip install -r requirements.txt
```

Or install directly:
```bash
pip install django-recaptcha==4.0.0
```

### 2. Get reCAPTCHA Keys
1. Go to [Google reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin)
2. Click "Create" or "+" to register a new site
3. Fill in the form:
   - **Label**: Guest Tracker (or your preferred name)
   - **reCAPTCHA type**: Select "reCAPTCHA v2" → "I'm not a robot Checkbox"
   - **Domains**: Add your domain(s)
     - For development: `localhost` and `127.0.0.1`
     - For production: `yourdomain.com` and `www.yourdomain.com`
   - Accept the Terms of Service
4. Click "Submit"
5. Copy the **Site Key** (public key) and **Secret Key** (private key)

### 3. Configure Environment Variables
Add your keys to the `.env` file (create from `.env.example` if needed):

```env
# reCAPTCHA Keys (for spam protection)
RECAPTCHA_PUBLIC_KEY=your-recaptcha-site-key-here
RECAPTCHA_PRIVATE_KEY=your-recaptcha-secret-key-here
```

**For Development/Testing (Optional):**
If you want to test locally without real keys, you can use Google's test keys:
```env
RECAPTCHA_PUBLIC_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
RECAPTCHA_PRIVATE_KEY=6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe
```
⚠️ **Note:** Test keys will always pass validation and should NEVER be used in production!

## Configuration Details

### Settings (guest_tracker/settings.py)
The following configuration has been added:

```python
# reCAPTCHA Configuration
RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY', '')
RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY', '')

# Silence reCAPTCHA checks in development if keys are not set
if not RECAPTCHA_PUBLIC_KEY or not RECAPTCHA_PRIVATE_KEY:
    SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']
```

### Forms Protected (guests/forms.py)
Two forms now include reCAPTCHA:

1. **CustomLoginForm** - Prevents brute-force login attempts
2. **GuestRegistrationForm** - Prevents spam registrations

### Templates Updated
The following templates now render the reCAPTCHA widget:

1. `guests/templates/guests/login.html`
2. `guests/templates/guests/guest_register.html`

## Testing

### Local Testing (Development)
1. Start the development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to:
   - Login: http://127.0.0.1:8000/accounts/login/
   - Registration: http://127.0.0.1:8000/guest/register/

3. You should see the reCAPTCHA checkbox widget
4. Submit the forms to verify validation works

### Testing Without Keys
If running in development without keys, the reCAPTCHA field will be silenced. To test properly, use the test keys mentioned above or your real keys.

### Production Testing
1. Deploy to your production server (cPanel)
2. Ensure `.env` file has your real production keys
3. Test on your actual domain
4. Verify reCAPTCHA widget appears and functions correctly

## Deployment to cPanel

### Step 1: Update .env on Server
SSH into your cPanel account or use File Manager:
```bash
cd ~/public_html/guest_tracker
nano .env
```

Add your production reCAPTCHA keys:
```env
RECAPTCHA_PUBLIC_KEY=your-production-site-key
RECAPTCHA_PRIVATE_KEY=your-production-secret-key
```

### Step 2: Install django-recaptcha
Activate your virtual environment and install:
```bash
source ~/virtualenv/public_html/guest_tracker/3.11/bin/activate
cd ~/public_html/guest_tracker
pip install django-recaptcha==4.0.0
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

### Step 3: Restart Application
Restart the Python app in cPanel:
1. Go to "Setup Python App"
2. Click "Restart" next to your application

## Troubleshooting

### reCAPTCHA Widget Not Appearing
- Check browser console for JavaScript errors
- Verify RECAPTCHA_PUBLIC_KEY is set correctly in .env
- Ensure 'captcha' is in INSTALLED_APPS
- Check that {{ form.captcha }} is in your template

### "Invalid reCAPTCHA" Error on Submit
- Verify RECAPTCHA_PRIVATE_KEY is correct
- Check that your domain is registered in reCAPTCHA admin console
- Ensure server time is synchronized (reCAPTCHA is time-sensitive)
- Check internet connectivity from server to Google's API

### Development Mode Issues
- If using test keys, remember they always pass (for testing UI only)
- If keys are missing, SILENCED_SYSTEM_CHECKS suppresses errors
- For real testing, use actual keys from Google

### reCAPTCHA Appears in Wrong Language
django-recaptcha automatically detects language from Django's LANGUAGE_CODE setting. To force English:
```python
# In settings.py
LANGUAGE_CODE = 'en-us'
```

## Security Considerations

### Best Practices
1. ✅ Never commit real keys to version control
2. ✅ Use different keys for development and production
3. ✅ Add only necessary domains to reCAPTCHA console
4. ✅ Monitor reCAPTCHA admin console for suspicious activity
5. ✅ Keep django-recaptcha package updated

### Additional Security
reCAPTCHA complements, but doesn't replace:
- Rate limiting (django-ratelimit)
- Strong password requirements
- HTTPS/SSL encryption
- CSRF protection
- Secure session management

## API Reference

### Form Field
```python
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox

captcha = ReCaptchaField(
    widget=ReCaptchaV2Checkbox,
    label="Verification",
    error_messages={
        'required': 'Please complete the reCAPTCHA verification.'
    }
)
```

### Template Usage
```django
<div class="mb-3">
    {{ form.captcha }}
    {% if form.captcha.errors %}
        <div class="invalid-feedback d-block">{{ form.captcha.errors }}</div>
    {% endif %}
</div>
```

## Resources
- [Google reCAPTCHA](https://www.google.com/recaptcha/)
- [django-recaptcha Documentation](https://github.com/torchbox/django-recaptcha)
- [reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin)

## Support
For issues specific to this implementation, check:
1. Django error logs
2. Browser console (for frontend issues)
3. reCAPTCHA admin console (for API issues)
4. Server error logs (for backend validation issues)

---

**Last Updated:** January 2025  
**Package Version:** django-recaptcha 4.0.0  
**reCAPTCHA Version:** v2 Checkbox
