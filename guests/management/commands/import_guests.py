import csv
import json
import os
try:
    import requests
except Exception:
    requests = None
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from guests.models import Guest, Invitation, Event
from django.core.mail import send_mail


class Command(BaseCommand):
    help = 'Import guests from a CSV. Optionally create users and invitations.'

    def add_arguments(self, parser):
        parser.add_argument('csvfile', help='Path to CSV with columns first_name,last_name,email,rank,institution')
        parser.add_argument('--event-id', type=int, default=None, help='Event ID to create invitations for')
        parser.add_argument('--create-users', action='store_true', help='Create Django user accounts for imported guests')
        parser.add_argument('--send-emails', action='store_true', help='Send invitation emails for created invitations')
        parser.add_argument('--emails-csv', default=None, help='Optional CSV mapping full_name,email')
        parser.add_argument('--email-lookup-url', default=None, help='Optional URL template for email lookup, use {first} and {last}')

    def handle(self, *args, **options):
        csvfile = options['csvfile']
        event_id = options.get('event_id')
        create_users = options.get('create_users')
        send_emails_opt = options.get('send_emails')
        emails_csv = options.get('emails_csv')
        email_lookup_url = options.get('email_lookup_url')

        email_map = {}
        if emails_csv and os.path.exists(emails_csv):
            with open(emails_csv, newline='', encoding='utf-8') as fh:
                rdr = csv.reader(fh)
                for row in rdr:
                    if len(row) >= 2:
                        email_map[row[0].strip()] = row[1].strip()

        event = None
        if event_id:
            try:
                event = Event.objects.get(id=event_id)
            except Event.DoesNotExist:
                self.stderr.write(f"Event id={event_id} not found; skipping invitations")
                event = None

        created = 0
        with open(csvfile, newline='', encoding='utf-8') as fh:
            rdr = csv.DictReader(fh)
            for row in rdr:
                first = row.get('first_name', '').strip()
                last = row.get('last_name', '').strip()
                rank = row.get('rank', '').strip()
                inst = row.get('institution', '').strip()
                email = row.get('email', '').strip()

                full = f"{first} {last}".strip()
                if not email:
                    email = email_map.get(full)
                if not email and email_lookup_url and requests:
                    try:
                        url = email_lookup_url.format(first=first, last=last)
                        resp = requests.get(url, timeout=5)
                        if resp.ok:
                            data = resp.json()
                            email = data.get('email') or email
                    except Exception:
                        pass

                if not email:
                    base = f"{first.lower()}.{(last.split()[0].lower() if last else 'import')}"
                    domain = 'import.example.com'
                    email = f"{base}@{domain}"
                    counter = 1
                    while Guest.objects.filter(email=email).exists():
                        email = f"{base}{counter}@{domain}"
                        counter += 1

                guest, gcreated = Guest.objects.get_or_create(
                    first_name=first,
                    last_name=last,
                    email=email,
                    defaults={'rank': rank, 'institution': inst}
                )

                if create_users and not guest.user and email:
                    import secrets
                    User = get_user_model()
                    username = email.split('@')[0]
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                    password = secrets.token_urlsafe(12)
                    user = User.objects.create_user(username=username, email=email, password=password)
                    guest.user = user
                    guest.save(update_fields=['user'])

                if event:
                    inv, inv_created = Invitation.objects.get_or_create(event=event, guest=guest)
                    if inv_created:
                        created += 1
                        if send_emails_opt:
                            # attempt to send simple email
                            try:
                                send_mail(f"You're invited to {event.name}", f"Please RSVP: {inv.get_rsvp_url()}", settings.DEFAULT_FROM_EMAIL, [guest.email])
                                inv.email_sent = True
                                inv.email_sent_at = timezone.now()
                                inv.save(update_fields=['email_sent', 'email_sent_at'])
                            except Exception as e:
                                self.stderr.write(f"Failed to send email to {guest.email}: {e}")

        self.stdout.write(f"Imported guests; created {created} invitations")
