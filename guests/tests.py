from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import EventCategory, EventTemplate, Event, Guest, Invitation, RSVP
from django.urls import reverse
from django.utils import timezone
import datetime

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.category = EventCategory.objects.create(name='Conference')
        self.event = Event.objects.create(
            name='Test Event',
            description='A test event',
            date=timezone.now() + datetime.timedelta(days=10),
            location='Test Location',
            created_by=self.user
        )
        self.guest = Guest.objects.create(
            first_name='John', last_name='Doe', email='john@example.com'
        )
        self.invitation = Invitation.objects.create(event=self.event, guest=self.guest)

    def test_event_str(self):
        self.assertEqual(str(self.event), 'Test Event')

    def test_guest_str(self):
        self.assertEqual(str(self.guest), 'John Doe')

    def test_invitation_str(self):
        self.assertIn('Invitation to John Doe for Test Event', str(self.invitation))

    def test_rsvp_creation(self):
        rsvp = RSVP.objects.create(invitation=self.invitation, response='yes')
        self.assertEqual(rsvp.total_guests, 1)
        self.assertEqual(str(rsvp), 'John Doe - Yes, I will attend')

class HomeViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.event = Event.objects.create(
            name='Test Event',
            description='A test event',
            date=timezone.now() + datetime.timedelta(days=10),
            location='Test Location',
            created_by=self.user
        )

    def test_home_view_status_code(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Event')


class APICheckInTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Organizer/staff user
        self.staff = User.objects.create_user(username='staff', password='pass')
        self.staff.is_staff = True
        self.staff.save()

        # Regular user
        self.user = User.objects.create_user(username='user', password='pass')

        self.event = Event.objects.create(
            name='API Event',
            description='API test event',
            date=timezone.now() + datetime.timedelta(days=5),
            location='Test Loc',
            created_by=self.staff
        )
        self.guest = Guest.objects.create(first_name='Alice', last_name='Smith', email='alice@example.com')
        self.invitation = Invitation.objects.create(event=self.event, guest=self.guest)

    def test_unauthorized_user_cannot_checkin(self):
        self.client.login(username='user', password='pass')
        url = reverse('api_check_in')
        resp = self.client.post(url, {'barcode_number': self.invitation.barcode_number}, content_type='application/json')
        self.assertEqual(resp.status_code, 403)

    def test_lookup_by_barcode(self):
        self.client.login(username='staff', password='pass')
        url = reverse('api_check_in')
        resp = self.client.post(url, {'barcode_number': self.invitation.barcode_number}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['invitation']['guest_name'], self.guest.full_name)
        # Seating should not be included for lookup-only (not checked in)
        self.assertIsNone(data['invitation']['table_number'])
        self.assertIsNone(data['invitation']['seat_number'])

    def test_checkin_marks_guest(self):
        self.client.login(username='staff', password='pass')
        url = reverse('api_check_in')
        resp = self.client.post(url, {'barcode_number': self.invitation.barcode_number, 'check_in': True, 'table_number': 'A1', 'seat_number': '5'}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['invitation']['checked_in'])
        # Seating should be assigned when checking in
        self.assertEqual(data['invitation']['table_number'], 'A1')
        self.assertEqual(data['invitation']['seat_number'], '5')
        # Check that check-in time was logged
        self.assertIsNotNone(data['invitation']['check_in_time'])
