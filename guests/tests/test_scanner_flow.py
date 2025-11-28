from django.test import TestCase, Client
from django.contrib.auth.models import User
from guests.models import Event, Guest, Invitation, CheckInLog, Table, Seat
from django.utils import timezone

class ScannerFlowTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', 'staff@example.com', 'pass')
        self.staff.is_staff = True
        self.staff.save()
        self.client = Client()
        self.client.login(username='staff', password='pass')

        self.event = Event.objects.create(name='Test Event', date=timezone.now(), location='HQ', created_by=self.staff)
        self.guest = Guest.objects.create(first_name='John', last_name='Doe', email='john@example.com')
        self.inv = Invitation.objects.create(event=self.event, guest=self.guest)

    def test_lookup_and_checkin_with_override(self):
        # Lookup by barcode (api_check_in)
        resp = self.client.post('/api/check-in/', data={'barcode_number': self.inv.barcode_number}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('invitation', data)
        # Now perform check-in with override
        resp2 = self.client.post('/api/check-in/', data={'barcode_number': self.inv.barcode_number, 'check_in': True, 'table_number':'A1', 'seat_number':'3'}, content_type='application/json')
        self.assertEqual(resp2.status_code, 200)
        self.inv.refresh_from_db()
        self.assertTrue(self.inv.checked_in)
        self.assertEqual(self.inv.table_number, 'A1')
        self.assertEqual(self.inv.seat_number, '3')
        # Check log created
        log = CheckInLog.objects.filter(invitation=self.inv).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.table_number, 'A1')
        self.assertEqual(log.seat_number, '3')

    def test_seat_reservation_prefers_normalized_seats(self):
        # Create table and seats
        t = Table.objects.create(event=self.event, number='1', capacity=2)
        s1 = Seat.objects.create(table=t, number='1')
        s2 = Seat.objects.create(table=t, number='2')
        # Another invitation
        guest2 = Guest.objects.create(first_name='Jane', last_name='Smith', email='jane@example.com')
        inv2 = Invitation.objects.create(event=self.event, guest=guest2)
        # Check-in inv1
        resp = self.client.post('/api/check-in/', data={'barcode_number': self.inv.barcode_number, 'check_in': True}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.inv.refresh_from_db()
        self.assertTrue(self.inv.checked_in)
        # One of the seats should be assigned to inv1
        s1.refresh_from_db(); s2.refresh_from_db()
        assigned = s1.assigned_invitation or s2.assigned_invitation
        self.assertIsNotNone(assigned)
*** End Patch