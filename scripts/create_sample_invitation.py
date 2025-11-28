import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guest_tracker.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from django.test import Client
from django.urls import reverse
import datetime

from guests.models import Event, Guest, Invitation

# Create/get a staff user
staff, created = User.objects.get_or_create(username='staff', defaults={'email': 'staff@example.com'})
if created:
    staff.set_password('staffpass')
    staff.is_staff = True
    staff.is_superuser = False
    staff.save()
else:
    if not staff.is_staff:
        staff.is_staff = True
        staff.save()

# Create an event
event = Event.objects.create(
    name='Sample Event',
    date=timezone.now() + datetime.timedelta(days=1),
    location='Test Hall',
    created_by=staff
)

# Create a guest with rank/institution
guest = Guest.objects.create(
    first_name='John',
    last_name='Smith',
    email='john.smith@example.com',
    rank='Capt.',
    institution='1st Infantry'
)

# Create invitation
inv = Invitation.objects.create(event=event, guest=guest)

# Ensure images generated (save already does generation, but re-call to be safe)
try:
    inv.generate_qr_code()
except Exception:
    pass
try:
    inv.generate_barcode()
except Exception:
    pass

print('--- Sample Invitation Created ---')
print('Invitation ID:', inv.id)
print('Unique code:', str(inv.unique_code))
print('Barcode number:', inv.barcode_number)
print('QR path:', inv.qr_code.url if inv.qr_code else '(no qr)')
print('Barcode path:', inv.barcode_image.url if inv.barcode_image else '(no barcode)')

# Perform scripted lookup and check-in using Django test client
client = Client()
client.force_login(staff)

api_url = reverse('api_check_in')
print('\nUsing API endpoint:', api_url)

# Lookup without checking in
resp = client.post(api_url, data=json.dumps({'barcode_number': inv.barcode_number, 'check_in': False}), content_type='application/json')
print('Lookup response status:', resp.status_code)
try:
    print('Lookup JSON:', resp.json())
except Exception as e:
    print('Lookup response text:', resp.content)

# Now perform check-in
resp2 = client.post(api_url, data=json.dumps({'barcode_number': inv.barcode_number, 'check_in': True}), content_type='application/json')
print('Check-in response status:', resp2.status_code)
try:
    print('Check-in JSON:', resp2.json())
except Exception as e:
    print('Check-in response text:', resp2.content)

# Verify event counter and CheckInLog
try:
    from guests.models import CheckInLog
    logs = CheckInLog.objects.filter(event=event, invitation=inv)
    print('\nCheckInLog entries:', logs.count())
    for l in logs:
        print('Log:', l.id, l.checked_in_at.isoformat(), 'table=', l.table_number, 'seat=', l.seat_number, 'by=', l.checked_in_by)
except Exception as e:
    print('Could not fetch CheckInLog:', e)

print('\nDone')
