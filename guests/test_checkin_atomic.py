from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User

from guests.models import Event, Guest, Invitation, CheckInLog


class TestAtomicCheckIn(TestCase):
    def setUp(self):
        # create a staff user
        self.staff = User.objects.create_user(username='staff2', password='pass')
        self.staff.is_staff = True
        self.staff.save()

        # create an event
        self.event = Event.objects.create(
            name='Test Event',
            date=timezone.now(),
            location='Test Hall',
            created_by=self.staff,
        )

        # create a guest
        self.guest = Guest.objects.create(
            first_name='John',
            last_name='Smith',
            email='john.smith2@example.com',
            rank='Capt.',
            institution='1st Infantry',
        )

        # create an invitation
        self.invitation = Invitation.objects.create(event=self.event, guest=self.guest)

    def test_atomic_checkin(self):
        # perform check-in with seating
        result = self.invitation.check_in_guest_with_seating(table='5', seat='A', checked_in_by=self.staff)
        self.assertTrue(result)

        # reload objects
        self.invitation.refresh_from_db()
        self.event.refresh_from_db()

        # assert invitation updated
        self.assertTrue(self.invitation.checked_in)
        self.assertEqual(self.invitation.table_number, '5')
        self.assertEqual(self.invitation.seat_number, 'A')

        # assert CheckInLog created
        logs = CheckInLog.objects.filter(invitation=self.invitation)
        self.assertEqual(logs.count(), 1)

        # assert event counter incremented
        self.assertEqual(self.event.checked_in_count, 1)

        # calling check-in again should return False and not increment
        result2 = self.invitation.check_in_guest_with_seating(table='5', seat='A', checked_in_by=self.staff)
        self.assertFalse(result2)
        self.event.refresh_from_db()
        self.assertEqual(self.event.checked_in_count, 1)
