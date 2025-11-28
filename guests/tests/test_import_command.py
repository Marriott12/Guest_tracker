import json
import os
import tempfile
from django.core.management import call_command
from django.test import TestCase
from django.conf import settings

from guests.models import Event, Guest, Invitation


class ImportCommandTests(TestCase):
    def setUp(self):
        # create a staff user for created_by
        from django.contrib.auth.models import User
        self.staff = User.objects.create_user(username='importer', password='pass')
        self.staff.is_staff = True
        self.staff.save()

    def test_import_event_idempotent_and_email_mapping(self):
        # create temp JSON files
        tmpdir = tempfile.mkdtemp()
        program = {'event_title': 'Imported Event', 'items': []}
        menu = {'menu_name': 'Imported Event', 'date': '2025-12-31'}
        seating = {'tables': [{'number': '1', 'assigned': [{'guest_name': 'Alice Example', 'seat': 1}]}]}

        ppath = os.path.join(tmpdir, 'program.json')
        mpath = os.path.join(tmpdir, 'menu.json')
        spath = os.path.join(tmpdir, 'seating.json')
        with open(ppath, 'w', encoding='utf-8') as fh:
            json.dump(program, fh)
        with open(mpath, 'w', encoding='utf-8') as fh:
            json.dump(menu, fh)
        with open(spath, 'w', encoding='utf-8') as fh:
            json.dump(seating, fh)

        # create emails mapping
        emails_map = { 'Alice Example': 'alice@example.com' }
        emap_path = os.path.join(tmpdir, 'emails.json')
        with open(emap_path, 'w', encoding='utf-8') as fh:
            json.dump(emails_map, fh)

        # run import
        call_command('import_event_data', '--program', ppath, '--menu', mpath, '--seating', spath, '--emails', emap_path)

        # assert created
        event = Event.objects.filter(name='Imported Event').first()
        self.assertIsNotNone(event)
        guest = Guest.objects.filter(first_name='Alice').first()
        self.assertIsNotNone(guest)
        self.assertEqual(guest.email, 'alice@example.com')

        # run again to test idempotency
        call_command('import_event_data', '--program', ppath, '--menu', mpath, '--seating', spath, '--emails', emap_path)
        # ensure no duplicate invitations
        inv_count = Invitation.objects.filter(event=event, guest=guest).count()
        self.assertEqual(inv_count, 1)
