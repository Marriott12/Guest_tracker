# Guest Portal & User Profile Management - Implementation Guide

## Overview

This implementation adds a complete guest portal system that allows:
1. **Guests** to register, login, view invitations, manage RSVPs, and edit their profiles
2. **Admins/Organizers** to edit their own user profiles
3. **Secure authentication** with password management

---

## Features Implemented

### 1. Guest Portal System

#### Guest Registration (`/register/`)
- Self-registration form for new guests
- Creates both User account and Guest profile automatically
- Fields: username, email, first name, last name, phone, password
- Automatic login after successful registration

#### Guest Portal Dashboard (`/portal/`)
- View all upcoming and past event invitations
- Quick stats: Pending RSVPs, Confirmed, Declined
- One-click access to RSVP forms
- View invitation details including QR codes

#### Guest Profile Management (`/portal/profile/`)
- Edit personal information: name, email, phone, address
- Change password link
- Updates both Guest and User models simultaneously

#### RSVP Management (`/portal/rsvp/<invitation_id>/`)
- Submit or edit RSVPs from the portal
- Same form as public RSVP with better integration
- Tracks response status automatically

#### Invitation Details (`/portal/invitation/<invitation_id>/`)
- Full event information
- Personal QR code for check-in
- RSVP status display
- Event details: program, menu, seating (if available)

### 2. Admin/Organizer Profile Management

#### User Profile Edit (`/profile/edit/`)
- For staff/admin users
- Edit: first name, last name, email
- Change password option
- Separate from guest portal

### 3. Authentication System

#### Login (`/login/`)
- Standard Django authentication
- Username + password
- "Next" parameter support for redirects
- Link to registration page

#### Logout (`/logout/`)
- Secure logout
- Redirects to home page

#### Password Change (`/password-change/`)
- Change password for logged-in users
- Django's built-in security
- Success confirmation page

---

## Model Changes

### Guest Model Updates

```python
class Guest(models.Model):
    # NEW FIELDS:
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    can_login = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # NEW METHOD:
    def create_user_account(self):
        """Programmatically create user account for existing guest"""
        # Generates username from email
        # Creates random secure password
        # Returns password for emailing to guest
```

**Migration:** `0006_guest_can_login_guest_last_login_guest_user.py`

---

## Forms Added

### 1. GuestProfileForm
```python
# For guests to edit their own profile
fields = ['first_name', 'last_name', 'email', 'phone', 'address']
```

### 2. UserProfileForm
```python
# For admins/organizers
fields = ['first_name', 'last_name', 'email']
```

### 3. GuestRegistrationForm
```python
# Extends UserCreationForm
fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'phone']
# Automatically creates Guest profile on save
```

---

## Views Added

| View | URL | Access | Purpose |
|------|-----|--------|---------|
| `guest_portal` | `/portal/` | Login Required | Dashboard for guests |
| `guest_profile_edit` | `/portal/profile/` | Login Required (Guest) | Edit guest profile |
| `guest_invitation_detail` | `/portal/invitation/<id>/` | Login Required (Owner) | View invitation details |
| `guest_rsvp_manage` | `/portal/rsvp/<id>/` | Login Required (Owner) | Manage RSVP |
| `guest_register` | `/register/` | Anonymous Only | Self-registration |
| `user_profile_edit` | `/profile/edit/` | Login Required (Staff) | Edit organizer profile |
| Login | `/login/` | Anonymous | Login page |
| Logout | `/logout/` | Logged In | Logout |
| Password Change | `/password-change/` | Login Required | Change password |

---

## Templates Created

1. **`guest_portal.html`** - Main portal dashboard
2. **`guest_profile_edit.html`** - Guest profile editing
3. **`guest_invitation_detail.html`** - Detailed invitation view
4. **`guest_rsvp_manage.html`** - RSVP form for guests
5. **`guest_register.html`** - Registration form
6. **`login.html`** - Login page
7. **`user_profile_edit.html`** - Admin/staff profile editing
8. **`password_change.html`** - Password change form
9. **`password_change_done.html`** - Success confirmation

### Navigation Updates (base.html)
- Dynamic menu based on authentication status
- Staff users see: Dashboard, Analytics
- Guest users see: My Portal
- User dropdown with profile/logout options
- Login/Register buttons for anonymous users

---

## Usage Examples

### Example 1: Guest Self-Registration

```
1. Visit /register/
2. Fill in:
   - Username: johndoe
   - Email: john@example.com
   - First Name: John
   - Last Name: Doe
   - Password: SecurePass123!
3. Click "Create Account"
4. Automatically logged in and redirected to /portal/
5. Guest profile created with can_login=True
```

### Example 2: Guest Managing Invitations

```
1. Login at /login/
2. Redirected to /portal/
3. See list of pending invitations
4. Click "RSVP Now" on an invitation
5. Submit RSVP form
6. Return to portal with updated status
```

### Example 3: Admin Creating Guest Account Programmatically

```python
# In Django shell or admin action
guest = Guest.objects.get(email='existing@guest.com')
password = guest.create_user_account()

# Send password to guest via email
send_mail(
    'Your Guest Portal Access',
    f'Username: {guest.user.username}\nPassword: {password}',
    'from@example.com',
    [guest.email]
)
```

### Example 4: Admin Editing Own Profile

```
1. Login as staff user
2. Click user dropdown → "Edit Profile"
3. Update first name, last name, email
4. Click "Save Changes"
5. Can also change password from same page
```

---

## Security Features

1. **@login_required decorators** on all portal views
2. **Permission checks** - guests can only access their own data
3. **Password validation** - Django's built-in validators
4. **CSRF protection** on all forms
5. **Secure password storage** - Django's password hashing
6. **Session management** - Django's session framework

---

## Settings Configuration

```python
# guest_tracker/settings.py

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'  # For staff
LOGOUT_REDIRECT_URL = '/'
GUEST_PORTAL_LOGIN_REDIRECT = '/portal/'  # For guests
```

---

## Admin Panel Integration

### Guest Admin
- New fields visible: `user`, `can_login`, `last_login`
- Can manually link guests to user accounts
- Filter by `can_login` status

### Recommended Admin Actions
```python
# Add to guests/admin.py

@admin.action(description='Create user accounts for selected guests')
def create_user_accounts(modeladmin, request, queryset):
    for guest in queryset:
        if not guest.user:
            password = guest.create_user_account()
            # Email password to guest
            messages.success(request, f'Account created for {guest.full_name}')
```

---

## Testing Guide

### Test Guest Registration
```bash
# Visit in browser
http://localhost:8000/register/

# Create account with:
- Username: testguest
- Email: test@guest.com
- Names: Test Guest
- Password: TestPass123!

# Should redirect to portal dashboard
```

### Test Guest Portal
```bash
# After login, visit:
http://localhost:8000/portal/

# Should see:
- Welcome message with name
- Stats cards
- List of invitations
- Edit profile button
```

### Test RSVP Management
```bash
# From portal, click "RSVP Now" on invitation
# Fill form and submit
# Should return to portal with success message
# Invitation status should update
```

### Test Profile Editing
```bash
# Click "Edit Profile"
# Change phone number or address
# Click "Save Changes"
# Should update both Guest and User models
```

---

## Migration Path for Existing Guests

### Option 1: Bulk Account Creation
```python
# management command: create_guest_accounts.py
from guests.models import Guest
from django.core.mail import send_mail

for guest in Guest.objects.filter(user__isnull=True, email__isnull=False):
    password = guest.create_user_account()
    # Email credentials to guest
    send_mail(
        'Your Guest Portal Access',
        f'''
        Welcome to the Guest Portal!
        
        Username: {guest.user.username}
        Temporary Password: {password}
        
        Login at: https://yourdomain.com/login/
        Please change your password after first login.
        ''',
        'noreply@yourdomain.com',
        [guest.email]
    )
```

### Option 2: Self-Service with Email Verification
Allow guests to claim their profile:
1. Send email with unique link
2. Guest clicks link → registration form pre-filled
3. Sets password
4. Account linked to existing Guest record

---

## API/Future Enhancements

### Potential Additions:
1. **Email verification** for new registrations
2. **Password reset** via email
3. **Social login** (Google, Facebook)
4. **Two-factor authentication**
5. **Guest preferences** (notification settings)
6. **Calendar integration** (add to Google Calendar)
7. **Mobile app** access with API
8. **Guest-to-guest messaging**

---

## Troubleshooting

### Issue: Guest can't see portal
**Solution:** Check `can_login=True` and `user` is not None

### Issue: Login redirects to wrong place
**Solution:** Check LOGIN_REDIRECT_URL and middleware

### Issue: Password change fails
**Solution:** Ensure user is authenticated, check form validation

### Issue: Guest sees admin dashboard
**Solution:** Check is_staff status, update navigation logic

---

## Files Modified/Created

### Modified:
- `guests/models.py` - Added fields to Guest model
- `guests/forms.py` - Added 3 new forms
- `guests/views.py` - Added 6 new views
- `guests/urls.py` - Added 6 new URL patterns
- `guest_tracker/urls.py` - Added authentication URLs
- `guest_tracker/settings.py` - Updated LOGIN_URL
- `guests/templates/guests/base.html` - Updated navigation

### Created:
- Migration: `0006_guest_can_login_guest_last_login_guest_user.py`
- 9 new templates for guest portal and authentication

---

## Deployment Checklist

- [ ] Run migrations: `python manage.py migrate`
- [ ] Update ALLOWED_HOSTS in production
- [ ] Configure EMAIL_BACKEND for password reset emails
- [ ] Set strong SECRET_KEY
- [ ] Enable HTTPS (SECURE_SSL_REDIRECT = True)
- [ ] Configure session security settings
- [ ] Test all portal features
- [ ] Create test guest account
- [ ] Document login credentials for support team

---

🎉 **Complete Guest Portal System Ready!**

Guests can now self-register, manage their invitations, and update their profiles independently!
