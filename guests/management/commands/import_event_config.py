import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from guests.models import Event


class Command(BaseCommand):
    help = 'Import event program/menu/seating configuration from a JSON file into an Event JSONFields'

    def add_arguments(self, parser):
        parser.add_argument('event_id', type=int, help='ID of the event to update')
        parser.add_argument('json_file', type=str, help='Path to the JSON file containing program/menu/seating')
        parser.add_argument('--preview', action='store_true', help='Show changes that would be applied without modifying the database')
        parser.add_argument('--merge', action='store_true', help='Merge seating into existing Tables/Seats instead of deleting them')
        parser.add_argument('--sync', action='store_true', help='Synchronize tables/seats to match exactly (prune extras when merging)')

    def handle(self, *args, **options):
        event_id = options['event_id']
        json_file = options['json_file']

        if not os.path.exists(json_file):
            raise CommandError(f'JSON file not found: {json_file}')

        try:
            with open(json_file, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception as e:
            raise CommandError(f'Failed to parse JSON file: {e}')

        # Try to perform JSON Schema validation if jsonschema is available; fall back to lightweight checks.
        schema_errors = []
        try:
            from jsonschema import validate, ValidationError

            schema = {
                'type': 'object',
                'properties': {
                    'program_schedule': {
                        'type': 'object',
                        'properties': {
                            'items': {'type': 'array'}
                        }
                    },
                    'menu': {'type': 'object'},
                    'seating_arrangement': {
                        'type': 'object',
                        'properties': {
                            'tables': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'number': {'type': ['string', 'number']},
                                        'capacity': {'type': 'integer', 'minimum': 0},
                                        'section': {'type': 'string'}
                                    },
                                    'required': ['number']
                                }
                            }
                        }
                    },
                    'has_assigned_seating': {'type': 'boolean'}
                }
            }
            validate(instance=data, schema=schema)
        except Exception:
            # jsonschema not available or validation failed; fall back to simple checks
            try:
                from jsonschema import ValidationError
            except Exception:
                ValidationError = None

            def validate_structure(d):
                errors = []
                if 'program_schedule' in d:
                    ps = d['program_schedule']
                    if not isinstance(ps, dict) or ('items' in ps and not isinstance(ps.get('items'), list)):
                        errors.append('program_schedule must be an object with an "items" list')
                if 'menu' in d:
                    menu = d['menu']
                    if not isinstance(menu, dict):
                        errors.append('menu must be an object')
                if 'seating_arrangement' in d:
                    seating = d['seating_arrangement']
                    if not isinstance(seating, dict) or ('tables' in seating and not isinstance(seating.get('tables'), list)):
                        errors.append('seating_arrangement must be an object with a "tables" list')
                    else:
                        for t in seating.get('tables', []):
                            if not isinstance(t, dict) or 'number' not in t:
                                errors.append('each table must be an object with a "number"')
                return errors

            schema_errors = validate_structure(data)
            if schema_errors:
                raise CommandError('JSON validation errors: ' + '; '.join(schema_errors))

        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            raise CommandError(f'Event with id {event_id} does not exist')

        changed = False
        preview = options.get('preview', False)
        do_merge = options.get('merge', False)
        do_sync = options.get('sync', False)
        # Accept keys: program_schedule, menu, seating_arrangement, has_assigned_seating
        if 'program_schedule' in data:
            event.program_schedule = data['program_schedule']
            changed = True
        if 'menu' in data:
            event.menu = data['menu']
            changed = True
        if 'seating_arrangement' in data:
            event.seating_arrangement = data['seating_arrangement']
            changed = True
        if 'has_assigned_seating' in data:
            event.has_assigned_seating = bool(data['has_assigned_seating'])
            changed = True

        if changed:
            if preview:
                self.stdout.write(self.style.WARNING('Preview mode: no changes applied. Detected changes:'))
                if 'program_schedule' in data:
                    self.stdout.write(' - program_schedule: would update')
                if 'menu' in data:
                    self.stdout.write(' - menu: would update')
                if 'seating_arrangement' in data:
                    self.stdout.write(' - seating_arrangement: would update')
                if 'has_assigned_seating' in data:
                    self.stdout.write(' - has_assigned_seating: would update')
                return

            event.save()
            # If seating_arrangement provided, also populate normalized Table and Seat models
            if 'seating_arrangement' in data:
                try:
                    from guests.models import Table, Seat
                    tables = data['seating_arrangement'].get('tables', []) if isinstance(data['seating_arrangement'], dict) else []
                    if not do_merge:
                        # Clear existing tables/seats for the event
                        Table.objects.filter(event=event).delete()
                    for t in tables:
                        number = t.get('number')
                        capacity = int(t.get('capacity', 0)) if t.get('capacity') is not None else 0
                        section = t.get('section', '')
                        if not number:
                            continue
                        tbl, created = Table.objects.get_or_create(event=event, number=str(number), defaults={'capacity': capacity, 'section': section})
                        if not created and do_merge:
                            # update capacity/section if provided
                            tbl.capacity = capacity or tbl.capacity
                            tbl.section = section or tbl.section
                            tbl.save()
                        # create seat rows up to capacity, but don't overwrite existing seats
                        existing_seat_numbers = set(tbl.seats.values_list('number', flat=True))
                        for i in range(1, capacity + 1):
                            if str(i) not in existing_seat_numbers:
                                Seat.objects.create(table=tbl, number=str(i))
                        if do_sync:
                            # prune extra seats beyond capacity if unassigned
                            extra = tbl.seats.exclude(number__in=[str(i) for i in range(1, capacity + 1)])
                            for s in extra:
                                if s.assigned_invitation_id is None:
                                    s.delete()
                except Exception:
                    self.stderr.write('Warning: failed to populate Table/Seat models from seating_arrangement')

            self.stdout.write(self.style.SUCCESS(f'Updated event {event_id} with provided configuration'))
        else:
            self.stdout.write(self.style.WARNING('No recognized keys found in JSON (expected program_schedule/menu/seating_arrangement/has_assigned_seating)'))
