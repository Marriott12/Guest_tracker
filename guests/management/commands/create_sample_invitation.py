from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.test import Client
from django.urls import reverse
import datetime, json
from guests.models import Event, Guest, Invitation, CheckInLog

class Command(BaseCommand):
    help = 'Create a sample invitation and perform scripted check-in'

    def handle(self, *args, **options):
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

        # Prefer matching by name + creator to avoid colliding with other 'Sample Event' rows
        event = Event.objects.filter(name='Sample Event', created_by=staff).first()
        if not event:
            event = Event.objects.create(
                name='Sample Event',
                date=timezone.now() + datetime.timedelta(days=1),
                location='Test Hall',
                created_by=staff
            )

        guest, _ = Guest.objects.get_or_create(
            first_name='John',
            last_name='Smith',
            email='john.smith@example.com',
            defaults={
                'rank': 'Capt.',
                'institution': '1st Infantry',
            }
        )

        inv, created_inv = Invitation.objects.get_or_create(event=event, guest=guest)

        # Ensure QR/barcode generated (generate if missing)
        try:
            if not inv.qr_code:
                inv.generate_qr_code()
        except Exception as e:
            self.stderr.write(f'Error generating QR: {e}')
        try:
            if not inv.barcode_image:
                inv.generate_barcode()
        except Exception as e:
            self.stderr.write(f'Error generating barcode: {e}')

        self.stdout.write('--- Sample Invitation Created ---')
        self.stdout.write('Invitation ID: %s' % inv.id)
        self.stdout.write('Unique code: %s' % str(inv.unique_code))
        self.stdout.write('Barcode number: %s' % inv.barcode_number)
        self.stdout.write('QR path: %s' % (inv.qr_code.url if inv.qr_code else '(no qr)'))
        self.stdout.write('Barcode path: %s' % (inv.barcode_image.url if inv.barcode_image else '(no barcode)'))

        client = Client()
        client.force_login(staff)

        api_url = reverse('api_check_in')
        self.stdout.write('\nUsing API endpoint: %s' % api_url)

        resp = client.post(api_url, data=json.dumps({'barcode_number': inv.barcode_number, 'check_in': False}), content_type='application/json')
        self.stdout.write('Lookup response status: %s' % resp.status_code)
        try:
            self.stdout.write('Lookup JSON: %s' % resp.json())
        except Exception:
            self.stdout.write('Lookup response text: %s' % resp.content)

        resp2 = client.post(api_url, data=json.dumps({'barcode_number': inv.barcode_number, 'check_in': True}), content_type='application/json')
        self.stdout.write('Check-in response status: %s' % resp2.status_code)
        try:
            self.stdout.write('Check-in JSON: %s' % resp2.json())
        except Exception:
            self.stdout.write('Check-in response text: %s' % resp2.content)

        logs = CheckInLog.objects.filter(event=event, invitation=inv)
        self.stdout.write('\nCheckInLog entries: %s' % logs.count())
        for l in logs:
            self.stdout.write('Log: %s %s table=%s seat=%s by=%s' % (l.id, l.checked_in_at.isoformat(), l.table_number, l.seat_number, l.checked_in_by))

        self.stdout.write('\nDone')
