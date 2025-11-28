from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache
from guests.models import Event, CheckInSession
from django.utils import timezone

class AdminSessionTests(TestCase):
    def setUp(self):
        # create admin user
        self.admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='pass')
        # create a sample event
        self.event = Event.objects.create(name='Test Event', date=timezone.now() + timezone.timedelta(days=1), location='Test', created_by=self.admin)
        self.client = Client()
        self.client.force_login(self.admin)

    def test_admin_start_end_session(self):
        url = reverse('admin:guests_active_sessions')
        # ensure no active session
        cache_key = f'guests:checkin_session:{self.event.id}'
        cache.delete(cache_key)
        CheckInSession.objects.filter(event=self.event).delete()

        # Start session via admin POST
        resp = self.client.post(url, {'action': 'start', 'event_id': str(self.event.id)}, follow=True)
        self.assertEqual(resp.status_code, 200)
        # check DB record
        active = CheckInSession.objects.filter(event=self.event, ended_at__isnull=True).first()
        self.assertIsNotNone(active, 'CheckInSession record should be created')
        self.assertEqual(active.started_by, self.admin)
        # check cache
        cached = cache.get(cache_key)
        self.assertIsNotNone(cached)
        self.assertEqual(cached.get('session_id'), active.id)

        # End session via admin POST
        resp2 = self.client.post(url, {'action': 'end', 'event_id': str(self.event.id)}, follow=True)
        self.assertEqual(resp2.status_code, 200)
        active.refresh_from_db()
        self.assertIsNotNone(active.ended_at)
        self.assertEqual(active.ended_by, self.admin)
        # cache should be cleared
        self.assertIsNone(cache.get(cache_key))
