from django.core.management.base import BaseCommand, CommandError
from guests.models import Table, Seat

class Command(BaseCommand):
    help = 'Create Seat rows for tables based on their capacity. Use --event EVENT_ID to limit to one event. --preview to dry-run.'

    def add_arguments(self, parser):
        parser.add_argument('--event', type=int, help='Event ID to target')
        parser.add_argument('--preview', action='store_true', help='Preview only; do not create seats')

    def handle(self, *args, **options):
        event_id = options.get('event')
        preview = options.get('preview')

        qs = Table.objects.all()
        if event_id:
            qs = qs.filter(event_id=event_id)

        total_to_create = 0
        details = []
        for table in qs:
            try:
                capacity = int(table.capacity or 0)
            except Exception:
                capacity = 0
            for i in range(1, capacity + 1):
                if not Seat.objects.filter(table=table, number=str(i)).exists():
                    total_to_create += 1
                    details.append((table.id, table.number, i))
        if preview:
            self.stdout.write(self.style.SUCCESS(f'Preview: {total_to_create} seats would be created'))
            for t_id, t_num, seat_num in details[:100]:
                self.stdout.write(f'  Table {t_num} (id={t_id}) -> seat {seat_num}')
            return

        created = 0
        for t_id, t_num, seat_num in details:
            table = Table.objects.get(id=t_id)
            obj, was_created = Seat.objects.get_or_create(table=table, number=str(seat_num))
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created} seats'))
