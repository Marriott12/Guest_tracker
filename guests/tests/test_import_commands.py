from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from guests.models import Event, Table, Seat
import tempfile
import os

class ImportCommandsTest(TestCase):
    def setUp(self):
        self.event = Event.objects.create(name='Test Event', date='2026-01-01T10:00:00Z')

    def test_create_seats_preview_and_apply(self):
        t = Table.objects.create(event=self.event, number='1', capacity=3)
        # preview should not create
        out = tempfile.NamedTemporaryFile(delete=False)
        out.close()
        try:
            call_command('create_seats', '--preview', '--event', str(self.event.id))
        finally:
            os.unlink(out.name)
        # still zero seats
        self.assertEqual(Seat.objects.filter(table=t).count(), 0)
        # run create
        call_command('create_seats', '--event', str(self.event.id))
        self.assertEqual(Seat.objects.filter(table=t).count(), 3)

    def test_import_seating_preview_and_apply_tables(self):
        # create a CSV for tables
        fd, path = tempfile.mkstemp(suffix='.csv')
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write('1,4,Main\n')
            f.write('2,6,VIP\n')
        try:
            # preview should parse
            call_command('import_seating', str(self.event.id), path, '--type', 'tables', '--preview')
            # apply
            call_command('import_seating', str(self.event.id), path, '--type', 'tables')
        finally:
            os.unlink(path)
        # verify tables created
        self.assertEqual(Table.objects.filter(event=self.event).count(), 2)
