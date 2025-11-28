import csv
import os
import tempfile
from unittest.mock import patch, Mock
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.core import mail

from guests.models import Event, Guest, Invitation


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ImportGuestsCommandTests(TestCase):
    def setUp(self):
        # create an event for invitations
        from django.contrib.auth.models import User
        self.staff = User.objects.create_user(username='importer_test', password='pass')
        self.staff.is_staff = True
        self.staff.save()
        self.event = Event.objects.create(name='Import Test Event', date='2026-01-01T10:00:00', location='Hall', created_by=self.staff)

    def test_import_guests_with_emails_csv_and_create_users_and_send(self):
        tmpdir = tempfile.mkdtemp()
        csv_path = os.path.join(tmpdir, 'guests.csv')
        emails_csv = os.path.join(tmpdir, 'emails_map.csv')

        # write guests CSV without emails
        with open(csv_path, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.writer(fh)
            writer.writerow(['first_name','last_name','email','rank','institution'])
            writer.writerow(['Bob','Builder','','Mr.','Construction'])

        # write emails map
        with open(emails_csv, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.writer(fh)
            writer.writerow(['Bob Builder','bob.builder@example.com'])

        call_command('import_guests', csv_path, '--event-id', str(self.event.id), '--create-users', '--send-emails', '--emails-csv', emails_csv)

        # assert guest created and user attached
        guest = Guest.objects.filter(first_name='Bob', last_name='Builder').first()
        self.assertIsNotNone(guest)
        self.assertEqual(guest.email, 'bob.builder@example.com')

        # one invitation created and one email sent
        inv = Invitation.objects.filter(event=self.event, guest=guest).first()
        self.assertIsNotNone(inv)
        self.assertEqual(len(mail.outbox), 1)

    def test_import_guests_external_lookup(self):
        tmpdir = tempfile.mkdtemp()
        csv_path = os.path.join(tmpdir, 'guests2.csv')

        with open(csv_path, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.writer(fh)
            writer.writerow(['first_name','last_name','email','rank','institution'])
            writer.writerow(['Eve','Finder','','',''])

        # mock external lookup
        mock_resp = Mock()
        mock_resp.ok = True
        mock_resp.json.return_value = {'email': 'eve.finder@lookup.com'}

        with patch('guests.management.commands.import_guests.requests.get', return_value=mock_resp):
            call_command('import_guests', csv_path, '--event-id', str(self.event.id), '--email-lookup-url', 'http://fake/{first}/{last}')

        guest = Guest.objects.filter(first_name='Eve', last_name='Finder').first()
        self.assertIsNotNone(guest)
        self.assertEqual(guest.email, 'eve.finder@lookup.com')
