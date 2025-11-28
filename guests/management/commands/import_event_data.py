import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from guests.models import Event, Guest, Invitation
from django.core.mail import send_mail
import csv


class Command(BaseCommand):
    help = 'Import event program, menu, and seating JSON into an Event (idempotent)'

    def add_arguments(self, parser):
        parser.add_argument('--program', default=os.path.join(settings.BASE_DIR, 'program.json'))
        parser.add_argument('--menu', default=os.path.join(settings.BASE_DIR, 'menu.json'))
        parser.add_argument('--seating', default=os.path.join(settings.BASE_DIR, 'seating.json'))
        parser.add_argument('--emails', default=None, help='Optional JSON file mapping guest full names to emails')
        parser.add_argument('--name', default=None, help='Event name to use (overrides program file)')
        parser.add_argument('--date', default=None, help='Event date (ISO) to use, overrides menu file date')
        parser.add_argument('--emails-csv', default=None, help='Optional CSV mapping full_name,email')
        parser.add_argument('--create-users', action='store_true', help='Create Django user accounts for created guests')
        parser.add_argument('--send-emails', action='store_true', help='Send invitation emails for created invitations')
        parser.add_argument('--email-lookup-url', default=None, help='Optional URL template to lookup email by {first}/{last}')

    def handle(self, *args, **options):
        program_path = options['program']
        menu_path = options['menu']
        seating_path = options['seating']

        # Load JSON files if present
        program = {}
        menu = {}
        seating = {}
        emails_map = {}
        for path, dest in ((program_path, 'program'), (menu_path, 'menu'), (seating_path, 'seating')):
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as fh:
                        data = json.load(fh)
                except Exception as e:
                    self.stderr.write(f"Error reading {path}: {e}")
                    data = {}
            else:
                data = {}
            if dest == 'program':
                program = data
            elif dest == 'menu':
                menu = data
            else:
                seating = data

        # Load emails mapping if provided
        emails_path = options.get('emails')
        if emails_path and os.path.exists(emails_path):
            try:
                with open(emails_path, 'r', encoding='utf-8') as fh:
                    emails_map = json.load(fh)
            except Exception as e:
                self.stderr.write(f"Error reading emails mapping {emails_path}: {e}")
                emails_map = {}
        # Load emails CSV mapping if provided via --emails-csv
        emails_csv = options.get('emails_csv')
        if emails_csv and os.path.exists(emails_csv):
            try:
                with open(emails_csv, newline='', encoding='utf-8') as fh:
                    rdr = csv.reader(fh)
                    for row in rdr:
                        if len(row) >= 2:
                            emails_map[row[0].strip()] = row[1].strip()
            except Exception as e:
                self.stderr.write(f"Error reading emails CSV {emails_csv}: {e}")

        # Determine event name and date
        name = options.get('name') or program.get('event_title') or menu.get('menu_name') or 'Imported Event'
        date_str = options.get('date') or menu.get('date')
        if date_str:
            try:
                event_date = timezone.datetime.fromisoformat(date_str)
                # Make timezone-aware if naive
                if timezone.is_naive(event_date):
                    event_date = timezone.make_aware(event_date, timezone.get_current_timezone())
            except Exception:
                # fallback to now
                event_date = timezone.now()
        else:
            event_date = timezone.now()

        # Determine a user to mark as created_by
        User = get_user_model()
        user = User.objects.filter(is_staff=True).first()
        if not user:
            # create a system user
            user = User.objects.create_user(username='importer', password='importer')
            user.is_staff = True
            user.save()

        # Idempotent create/update event by name + date
        event, created = Event.objects.get_or_create(name=name, date=event_date, defaults={
            'location': 'Imported Location',
            'created_by': user,
        })
        if not created:
            self.stdout.write(f"Updating existing event '{event}'")
        else:
            self.stdout.write(f"Created event '{event}'")

        # Update JSON fields
        if program:
            event.program_schedule = program
        if menu:
            event.menu = menu
        if seating:
            event.seating_arrangement = seating
            # mark assigned seating flag
            if seating.get('tables'):
                event.has_assigned_seating = True

        event.save()

        # Create guests and invitations for assigned seats
        created_invitations = 0
        tables = seating.get('tables') or []
        for table in tables:
            table_num = table.get('number')
            assigned = table.get('assigned') or []
            for a in assigned:
                guest_name = a.get('guest_name')
                seat = a.get('seat')
                if not guest_name:
                    continue
                # smart name/email handling
                parts = guest_name.split()
                first = parts[0]
                last = ' '.join(parts[1:]) if len(parts) > 1 else ''

                # prefer explicit email provided in seating entry
                provided_email = a.get('email')
                # check mapping by full name
                mapped_email = emails_map.get(guest_name) if emails_map else None

                # Try to find existing guest by name
                guest = Guest.objects.filter(first_name=first, last_name=last).first()
                if guest:
                    email = guest.email
                else:
                    # Determine email to use
                    if provided_email:
                        email = provided_email
                    elif mapped_email:
                        email = mapped_email
                    else:
                        base = f"{first.lower()}.{(last.split()[0].lower() if last else 'import')}"
                        domain = 'import.example.com'
                        email = f"{base}@{domain}"
                        # ensure uniqueness
                        counter = 1
                        while Guest.objects.filter(email=email).exists():
                            email = f"{base}{counter}@{domain}"
                            counter += 1

                    guest = Guest.objects.create(
                        first_name=first,
                        last_name=last,
                        email=email,
                        rank=a.get('rank', ''),
                        institution=a.get('institution', ''),
                    )

                inv, inv_created = Invitation.objects.get_or_create(event=event, guest=guest)
                # assign seating
                inv.table_number = str(table_num)
                inv.seat_number = str(seat)
                inv.save()

                # Force generation of QR and barcode if missing
                try:
                    if not inv.qr_code:
                        inv.generate_qr_code()
                except Exception as e:
                    self.stderr.write(f"Failed to generate QR for invitation {inv.id}: {e}")
                try:
                    if not inv.barcode_image:
                        inv.generate_barcode()
                except Exception as e:
                    self.stderr.write(f"Failed to generate barcode for invitation {inv.id}: {e}")

                if inv_created:
                    created_invitations += 1

                # Optionally create users and send emails
                if options.get('create_users') and guest and not guest.user:
                    User = get_user_model()
                    username = guest.email.split('@')[0]
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                    user = User.objects.create_user(username=username, email=guest.email, password=User.objects.make_random_password())
                    guest.user = user
                    guest.save(update_fields=['user'])

                if options.get('send_emails') and inv:
                    try:
                        # Use the existing helper if available
                        try:
                            from guests.views import send_invitation_email
                            send_invitation_email(inv, request=None)
                        except Exception:
                            # Fallback simple mail
                            send_mail(f"You're invited to {event.name}", f"Please RSVP: {inv.get_rsvp_url()}", settings.DEFAULT_FROM_EMAIL, [guest.email])
                        inv.email_sent = True
                        inv.email_sent_at = timezone.now()
                        inv.save(update_fields=['email_sent', 'email_sent_at'])
                    except Exception as e:
                        self.stderr.write(f"Failed to send invitation email for invitation {inv.id}: {e}")

        self.stdout.write(f"Imported event '{event.name}' with {created_invitations} new invitations")
