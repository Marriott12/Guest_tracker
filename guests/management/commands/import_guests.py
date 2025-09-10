from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from guests.models import Event, Guest, Invitation, RSVP
import csv
from django.utils import timezone

class Command(BaseCommand):
    help = 'Import guests from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument('--event-id', type=int, help='Event ID to create invitations for')
        parser.add_argument('--create-invitations', action='store_true', 
                          help='Create invitations for the specified event')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        event_id = options.get('event_id')
        create_invitations = options.get('create_invitations')

        if create_invitations and not event_id:
            self.stdout.write(
                self.style.ERROR('Event ID is required when creating invitations')
            )
            return

        event = None
        if event_id:
            try:
                event = Event.objects.get(id=event_id)
            except Event.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Event with ID {event_id} does not exist')
                )
                return

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                guests_created = 0
                invitations_created = 0

                for row in reader:
                    # Expected CSV columns: first_name, last_name, email, phone, address
                    guest, created = Guest.objects.get_or_create(
                        first_name=row.get('first_name', '').strip(),
                        last_name=row.get('last_name', '').strip(),
                        email=row.get('email', '').strip(),
                        defaults={
                            'phone': row.get('phone', '').strip(),
                            'address': row.get('address', '').strip(),
                        }
                    )

                    if created:
                        guests_created += 1
                        self.stdout.write(f'Created guest: {guest.full_name}')

                    # Create invitation if requested
                    if create_invitations and event:
                        invitation, inv_created = Invitation.objects.get_or_create(
                            event=event,
                            guest=guest
                        )
                        if inv_created:
                            invitations_created += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully processed CSV file:\n'
                        f'- Guests created: {guests_created}\n'
                        f'- Invitations created: {invitations_created}'
                    )
                )

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file_path}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error processing CSV file: {str(e)}')
            )
