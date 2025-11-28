from django.core.management.base import BaseCommand, CommandError
from guests.models import Event, Table, Seat, ProgramItem, MenuItem, Invitation
import csv
import io

class Command(BaseCommand):
    help = 'Import program/menu/tables/seating from a CSV file. Use --type to pick program|menu|tables|seating. Use --preview to only parse and show what would happen.'

    def add_arguments(self, parser):
        parser.add_argument('event_id', type=int, help='Event ID')
        parser.add_argument('csvfile', type=str, help='Path to CSV file')
        parser.add_argument('--type', dest='import_type', choices=['program','menu','tables','seating'], required=True)
        parser.add_argument('--preview', action='store_true')

    def handle(self, *args, **options):
        event_id = options['event_id']
        csvpath = options['csvfile']
        import_type = options['import_type']
        preview = options.get('preview', False)

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            raise CommandError('Event not found')

        data_text = ''
        with open(csvpath, 'rb') as f:
            raw = f.read()
            try:
                data_text = raw.decode('utf-8')
            except Exception:
                data_text = raw.decode('latin-1')

        reader = csv.reader([r for r in data_text.splitlines() if r.strip()])
        parsed = []
        errors = []
        for i, row in enumerate(reader, start=1):
            if import_type == 'program':
                if len(row) < 2:
                    errors.append((i, 'Expected at least time and activity'))
                    continue
                parsed.append({'time': row[0].strip(), 'activity': row[1].strip(), 'description': (row[2].strip() if len(row) > 2 else '')})
            elif import_type == 'menu':
                if len(row) < 1:
                    errors.append((i, 'Expected at least name'))
                    continue
                parsed.append({'name': row[0].strip(), 'description': (row[1].strip() if len(row) > 1 else ''), 'dietary_tags': (row[2].strip() if len(row) > 2 else '')})
            elif import_type == 'tables':
                if len(row) < 2:
                    errors.append((i, 'Expected table_number and capacity'))
                    continue
                parsed.append({'number': row[0].strip(), 'capacity': row[1].strip(), 'section': (row[2].strip() if len(row) > 2 else '')})
            elif import_type == 'seating':
                if len(row) < 3:
                    errors.append((i, 'Expected table_number, seat_number, guest_identifier'))
                    continue
                parsed.append({'table': row[0].strip(), 'seat': row[1].strip(), 'guest': row[2].strip()})

        if errors:
            for err in errors[:20]:
                self.stdout.write(self.style.ERROR(f'Row {err[0]}: {err[1]}'))
            raise CommandError('Validation errors in CSV')

        self.stdout.write(self.style.SUCCESS(f'Parsed {len(parsed)} rows for import_type={import_type}'))

        if preview:
            for r in parsed[:50]:
                self.stdout.write(str(r))
            return

        # Apply
        if import_type == 'program':
            created = 0
            for idx, item in enumerate(parsed):
                ProgramItem.objects.create(event=event, start_time=item.get('time') or None, title=item.get('activity') or '', description=item.get('description',''), order=idx)
                created += 1
            self.stdout.write(self.style.SUCCESS(f'Created {created} program items'))
        elif import_type == 'menu':
            created = 0
            for idx, item in enumerate(parsed):
                MenuItem.objects.create(event=event, name=item.get('name',''), description=item.get('description',''), dietary_tags=item.get('dietary_tags',''), order=idx)
                created += 1
            self.stdout.write(self.style.SUCCESS(f'Created {created} menu items'))
        elif import_type == 'tables':
            created = 0
            for item in parsed:
                t, created_flag = Table.objects.get_or_create(event=event, number=str(item.get('number')))
                try:
                    t.capacity = int(item.get('capacity') or 0)
                except Exception:
                    t.capacity = 0
                t.section = item.get('section','')
                t.save()
                if created_flag:
                    created += 1
            self.stdout.write(self.style.SUCCESS(f'Processed {len(parsed)} table rows'))
        elif import_type == 'seating':
            assigned = 0
            for item in parsed:
                table = Table.objects.filter(event=event, number=str(item.get('table'))).first()
                if not table:
                    self.stdout.write(self.style.ERROR(f'Table {item.get("table")} not found'))
                    continue
                seat_obj, _ = Seat.objects.get_or_create(table=table, number=str(item.get('seat')))
                inv = Invitation.objects.filter(event=event, guest__email__iexact=item.get('guest')).first()
                if not inv:
                    inv = Invitation.objects.filter(event=event, barcode_number=item.get('guest')).first()
                if not inv:
                    inv = Invitation.objects.filter(event=event, unique_code=item.get('guest')).first()
                if not inv:
                    self.stdout.write(self.style.ERROR(f'Invitation not found for guest {item.get("guest")}'))
                    continue
                seat_obj.assigned_invitation = inv
                seat_obj.save()
                assigned += 1
            self.stdout.write(self.style.SUCCESS(f'Assigned {assigned} seats'))
