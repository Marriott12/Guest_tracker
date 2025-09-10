from django.core.management.base import BaseCommand
from guests.models import Event, Invitation
from guests.views import send_invitation_email
from django.utils import timezone

class Command(BaseCommand):
    help = 'Send email invitations for an event'

    def add_arguments(self, parser):
        parser.add_argument('event_id', type=int, help='Event ID to send invitations for')
        parser.add_argument('--unsent-only', action='store_true', 
                          help='Only send to guests who haven\'t received invitations yet')
        parser.add_argument('--dry-run', action='store_true',
                          help='Show what would be sent without actually sending')

    def handle(self, *args, **options):
        event_id = options['event_id']
        unsent_only = options.get('unsent_only', False)
        dry_run = options.get('dry_run', False)

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Event with ID {event_id} does not exist')
            )
            return

        # Get invitations to send
        invitations = event.invitations.all()
        if unsent_only:
            invitations = invitations.filter(email_sent=False)

        if not invitations.exists():
            self.stdout.write(
                self.style.WARNING('No invitations to send')
            )
            return

        self.stdout.write(
            f'Found {invitations.count()} invitations to send for event: {event.name}'
        )

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No emails will be sent'))
            for invitation in invitations:
                self.stdout.write(f'Would send to: {invitation.guest.email}')
            return

        sent_count = 0
        error_count = 0

        for invitation in invitations:
            try:
                if not invitation.email_sent or not unsent_only:
                    send_invitation_email(invitation)
                    invitation.email_sent = True
                    invitation.email_sent_at = timezone.now()
                    invitation.save()
                    sent_count += 1
                    self.stdout.write(f'✓ Sent to: {invitation.guest.email}')
                else:
                    self.stdout.write(f'- Skipped (already sent): {invitation.guest.email}')
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to send to {invitation.guest.email}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nInvitation sending complete:\n'
                f'- Successfully sent: {sent_count}\n'
                f'- Errors: {error_count}'
            )
        )
