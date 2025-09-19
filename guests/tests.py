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
