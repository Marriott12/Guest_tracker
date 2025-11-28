from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.files import File
import uuid
import qrcode
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from PIL import Image
import os
from django.conf import settings
from django.db import transaction
from django.db.models import F
import logging

class EventCategory(models.Model):
    """Categories for events"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    icon = models.CharField(max_length=50, default='fas fa-calendar', help_text="Font Awesome icon class")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Event Categories"

class EventTemplate(models.Model):
    """Templates for recurring events"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, blank=True)
    default_location = models.CharField(max_length=300, blank=True)
    default_max_guests = models.IntegerField(null=True, blank=True)
    default_rsvp_deadline_days = models.IntegerField(default=7, help_text="Days before event for RSVP deadline")
    email_template = models.TextField(blank=True, help_text="Default invitation email template")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Event(models.Model):
    """Model for events/occasions"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateTimeField()
    location = models.CharField(max_length=300)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    rsvp_deadline = models.DateTimeField(null=True, blank=True)
    max_guests = models.IntegerField(null=True, blank=True, help_text="Maximum number of guests allowed")
    
    # Event Details
    dress_code = models.CharField(max_length=200, blank=True, help_text="e.g., Formal, Casual, Military Uniform")
    parking_info = models.TextField(blank=True, help_text="Parking instructions and availability")
    special_instructions = models.TextField(blank=True, help_text="Any special instructions for guests")
    
    # Program Schedule
    program_schedule = models.JSONField(default=dict, blank=True, help_text="Event program/agenda as JSON")
    
    # Menu Information
    menu = models.JSONField(default=dict, blank=True, help_text="Event menu details as JSON")
    
    # Seating Arrangement
    seating_arrangement = models.JSONField(default=dict, blank=True, help_text="Seating arrangement details as JSON")
    has_assigned_seating = models.BooleanField(default=False, help_text="Whether this event has assigned seating")
    
    # Contact Information
    contact_person = models.CharField(max_length=200, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    
    # Event Image/Banner
    event_banner = models.ImageField(upload_to='event_banners/', blank=True, null=True)
    # Count of guests who have checked in (maintained on check-in)
    checked_in_count = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-date']


class ProgramItem(models.Model):
    """Individual program/agenda items for an event"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='program_items')
    start_time = models.TimeField(null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'start_time']

    def __str__(self):
        return f"{self.start_time or ''} - {self.title}"


class MenuItem(models.Model):
    """Menu items for an event"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    dietary_tags = models.CharField(max_length=200, blank=True, help_text='Comma-separated dietary tags')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Table(models.Model):
    """Normalized table representation for assigned seating"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tables')
    number = models.CharField(max_length=50)
    capacity = models.IntegerField(default=0)
    section = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ['event', 'number']

    def __str__(self):
        return f"Table {self.number} ({self.event.name})"


class Seat(models.Model):
    """Individual seat linked to a table; can be reserved for an invitation"""
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='seats')
    number = models.CharField(max_length=50)
    assigned_invitation = models.OneToOneField('Invitation', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_seat')

    class Meta:
        unique_together = ['table', 'number']

    def __str__(self):
        return f"{self.table} - Seat {self.number}"

class Guest(models.Model):
    """Model for guest information"""
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='guest_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Internal notes about the guest")
    # Optional military/professional rank and institution
    rank = models.CharField(max_length=100, blank=True, help_text="Military or professional rank/title")
    institution = models.CharField(max_length=200, blank=True, help_text="Institution or unit (e.g., Army Division)")
    
    # Guest portal settings
    can_login = models.BooleanField(default=False, help_text="Allow this guest to login to the portal")
    last_login = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def create_user_account(self):
        """Create a user account for this guest"""
        if not self.user and self.email:
            # Generate a random password
            import secrets
            password = secrets.token_urlsafe(12)
            
            # Create username from email
            username = self.email.split('@')[0]
            base_username = username
            counter = 1
            
            # Ensure unique username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=self.email,
                password=password,
                first_name=self.first_name,
                last_name=self.last_name
            )
            self.user = user
            self.can_login = True
            self.save()
            
            return password  # Return password so it can be emailed to guest
        return None
    
    class Meta:
        ordering = ['last_name', 'first_name']
        unique_together = ['first_name', 'last_name', 'email']

class Invitation(models.Model):
    """Model for invitations sent to guests"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('opened', 'Opened'),
        ('responded', 'Responded'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='invitations')
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='invitations')
    unique_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Enhanced tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    sent_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    
    # QR Code functionality
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    
    # Barcode functionality
    barcode_image = models.ImageField(upload_to='barcodes/', blank=True, null=True)
    barcode_number = models.CharField(max_length=50, blank=True, unique=True)
    
    # Check-in tracking
    checked_in = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(null=True, blank=True)
    
    # Seating assignment
    table_number = models.CharField(max_length=50, blank=True, help_text="Assigned table number")
    seat_number = models.CharField(max_length=50, blank=True, help_text="Assigned seat number")
    
    # Personal message
    personal_message = models.TextField(blank=True, help_text="Personal message for this guest")
    
    def __str__(self):
        return f"Invitation to {self.guest} for {self.event}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.qr_code:
            self.generate_qr_code()
        if not self.barcode_image:
            self.generate_barcode()
    
    def generate_qr_code(self):
        """Generate QR code for the invitation"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Create the RSVP URL
        rsvp_url = f"http://localhost:8000/rsvp/{self.unique_code}/"
        qr.add_data(rsvp_url)
        qr.make(fit=True)

        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Save to memory
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        buffer.seek(0)

        # Ensure media directory exists
        try:
            media_root = settings.MEDIA_ROOT
            qr_dir = os.path.join(media_root, 'qr_codes')
            os.makedirs(qr_dir, exist_ok=True)
        except Exception:
            pass

        # Save to model
        filename = f'qr_{self.unique_code}.png'
        self.qr_code.save(filename, File(buffer), save=False)
        super().save(update_fields=['qr_code'])
    
    def generate_barcode(self):
        """Generate barcode for the invitation"""
        # Use the UUID as the barcode number (convert to numeric string)
        if not self.barcode_number:
            # Create a unique numeric ID based on the invitation ID and timestamp
            import hashlib
            hash_str = hashlib.md5(str(self.unique_code).encode()).hexdigest()[:12]
            self.barcode_number = ''.join([str(int(c, 16)) for c in hash_str])[:12]
        
        # Generate Code128 barcode
        try:
            code128 = barcode.get_barcode_class('code128')
            barcode_instance = code128(self.barcode_number, writer=ImageWriter())
            
            # Save to memory
            buffer = BytesIO()
            barcode_instance.write(buffer, options={
                'module_width': 0.3,
                'module_height': 10,
                'quiet_zone': 2,
                'font_size': 10,
                'text_distance': 3,
            })
            buffer.seek(0)
            
            # Save to model
            filename = f'barcode_{self.unique_code}.png'
            # Ensure media directory exists
            try:
                media_root = settings.MEDIA_ROOT
                bc_dir = os.path.join(media_root, 'barcodes')
                os.makedirs(bc_dir, exist_ok=True)
            except Exception:
                pass

            self.barcode_image.save(filename, File(buffer), save=False)
            super().save(update_fields=['barcode_image', 'barcode_number'])
        except Exception as e:
            print(f"Error generating barcode: {e}")
    
    def check_in_guest(self):
        """Mark guest as checked in"""
        if not self.checked_in:
            self.checked_in = True
            self.check_in_time = timezone.now()
            self.save(update_fields=['checked_in', 'check_in_time'])
            return True
        return False

    def check_in_guest_with_seating(self, table=None, seat=None, checked_in_by=None):
        """Check in the guest and optionally assign seating during check-in.

        Seating (table/seat) will only be assigned if provided at the time of check-in.
        Returns True if the guest was newly checked in, False if already checked in.
        """
        newly_checked_in = False
        if not self.checked_in:
            self.checked_in = True
            self.check_in_time = timezone.now()
            newly_checked_in = True

        # Only assign seating during check-in
        assigned = False
        if table is not None:
            self.table_number = table
            assigned = True
        if seat is not None:
            self.seat_number = seat
            assigned = True

        # If the event uses assigned seating and no table/seat were provided,
        # perform a simple automatic assignment: find the first table in the
        # event.seating_arrangement with available capacity and assign the
        # next sequential seat number.
        if not assigned and self.event and getattr(self.event, 'has_assigned_seating', False):
            try:
                tables = (self.event.seating_arrangement or {}).get('tables', [])
                for t in tables:
                    table_num = t.get('number')
                    try:
                        capacity = int(t.get('capacity', 0))
                    except Exception:
                        capacity = 0
                    if not table_num or capacity <= 0:
                        continue
                    # Count currently assigned checked-in guests for this table
                    assigned_count = Invitation.objects.filter(
                        event=self.event,
                        checked_in=True,
                        table_number=str(table_num)
                    ).count()
                    if assigned_count < capacity:
                        # Assign this table and the next seat number
                        self.table_number = str(table_num)
                        self.seat_number = str(assigned_count + 1)
                        assigned = True
                        break
            except Exception:
                logging.exception('Auto seat assignment failed for invitation %s', getattr(self, 'id', None))

        # Prepare which fields should be saved
        update_fields = []
        if newly_checked_in:
            update_fields.extend(['checked_in', 'check_in_time'])
        if assigned:
            update_fields.extend(['table_number', 'seat_number'])

        # If newly checking in, perform seat assignment and logging atomically
        if newly_checked_in:
            try:
                with transaction.atomic():
                    # Lock invitations for this event to avoid race conditions during assignment
                    Invitation.objects.select_for_update().filter(event=self.event)

                    # If event uses assigned seating and no explicit assignment was provided,
                    # try to reserve an available Seat row (normalized seating) first.
                    if not assigned and getattr(self.event, 'has_assigned_seating', False):
                        try:
                            from .models import Seat
                            # Find an available seat for this event
                            seat_obj = Seat.objects.select_for_update().filter(table__event=self.event, assigned_invitation__isnull=True).order_by('table__number', 'number').first()
                            if seat_obj:
                                seat_obj.assigned_invitation = self
                                seat_obj.save()
                                self.table_number = str(seat_obj.table.number)
                                self.seat_number = str(seat_obj.number)
                                update_fields.extend(['table_number', 'seat_number'])
                                assigned = True
                            else:
                                # Fall back to simple seating_arrangement assignment if no Seat rows exist
                                tables = (self.event.seating_arrangement or {}).get('tables', [])
                                for t in tables:
                                    table_num = t.get('number')
                                    try:
                                        capacity = int(t.get('capacity', 0))
                                    except Exception:
                                        capacity = 0
                                    if not table_num or capacity <= 0:
                                        continue
                                    assigned_count = Invitation.objects.filter(
                                        event=self.event,
                                        checked_in=True,
                                        table_number=str(table_num)
                                    ).count()
                                    if assigned_count < capacity:
                                        self.table_number = str(table_num)
                                        self.seat_number = str(assigned_count + 1)
                                        update_fields.extend(['table_number', 'seat_number'])
                                        assigned = True
                                        break
                        except Exception:
                            logging.exception('Auto seat assignment failed for invitation %s', getattr(self, 'id', None))

                    # Save the invitation with updated fields
                    if update_fields:
                        self.save(update_fields=update_fields)

                    # Increment event checked_in_count atomically and create log
                    Event.objects.filter(pk=self.event.pk).update(checked_in_count=F('checked_in_count') + 1)
                    self.event.refresh_from_db(fields=['checked_in_count'])

                    CheckInLog.objects.create(
                        event=self.event,
                        invitation=self,
                        guest=self.guest,
                        checked_in_by=checked_in_by,
                        table_number=self.table_number,
                        seat_number=self.seat_number,
                    )
            except Exception:
                logging.exception("Failed to complete atomic check-in for invitation id=%s", getattr(self, 'id', None))
                raise
        else:
            # Not a new check-in: save any seating changes that were provided
            if update_fields:
                try:
                    self.save(update_fields=update_fields)
                except Exception:
                    logging.exception('Failed to save seating updates for invitation %s', getattr(self, 'id', None))

        return newly_checked_in
    
    def get_rsvp_url(self):
        """Generate the RSVP URL for this invitation"""
        return reverse('rsvp', kwargs={'code': str(self.unique_code)})
    
    @property
    def is_responded(self):
        """Check if guest has responded"""
        return hasattr(self, 'rsvp') and self.rsvp is not None
    
    class Meta:
        unique_together = ['event', 'guest']

class RSVP(models.Model):
    """Model for RSVP responses"""
    RESPONSE_CHOICES = [
        ('yes', 'Yes, I will attend'),
        ('no', 'No, I cannot attend'),
        ('maybe', 'Maybe, I am not sure'),
    ]
    
    invitation = models.OneToOneField(Invitation, on_delete=models.CASCADE, related_name='rsvp')
    response = models.CharField(max_length=5, choices=RESPONSE_CHOICES)
    plus_ones = models.IntegerField(default=0, help_text="Number of additional guests")
    dietary_restrictions = models.TextField(blank=True)
    special_requests = models.TextField(blank=True)
    responded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.invitation.guest} - {self.get_response_display()}"
    
    @property
    def total_guests(self):
        """Total number of guests including plus ones"""
        return 1 + self.plus_ones if self.response == 'yes' else 0

class GuestProfile(models.Model):
    """Extended profile information for guests"""
    guest = models.OneToOneField(Guest, on_delete=models.CASCADE, related_name='profile')
    photo = models.ImageField(upload_to='guest_photos/', blank=True, null=True)
    company = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    social_media = models.JSONField(default=dict, blank=True)  # Store social media links
    dietary_preferences = models.TextField(blank=True)
    accessibility_needs = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=200, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[('email', 'Email'), ('phone', 'Phone'), ('sms', 'SMS')],
        default='email'
    )
    
    # Marketing preferences
    subscribe_newsletter = models.BooleanField(default=False)
    allow_marketing = models.BooleanField(default=False)
    
    # Internal tracking
    vip_status = models.BooleanField(default=False)
    blacklisted = models.BooleanField(default=False)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    def __str__(self):
        return f"Profile for {self.guest}"

class EventAnalytics(models.Model):
    """Track event analytics and statistics"""
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='analytics')
    
    # Email metrics
    emails_sent = models.IntegerField(default=0)
    emails_opened = models.IntegerField(default=0)
    emails_clicked = models.IntegerField(default=0)
    emails_bounced = models.IntegerField(default=0)
    
    # RSVP metrics
    total_responses = models.IntegerField(default=0)
    yes_responses = models.IntegerField(default=0)
    no_responses = models.IntegerField(default=0)
    maybe_responses = models.IntegerField(default=0)
    
    # Engagement metrics
    page_views = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    
    # Timing metrics
    average_response_time = models.DurationField(null=True, blank=True)
    
    # Updated tracking
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analytics for {self.event}"
    
    @property
    def open_rate(self):
        if self.emails_sent == 0:
            return 0
        return (self.emails_opened / self.emails_sent) * 100
    
    @property
    def response_rate(self):
        if self.emails_sent == 0:
            return 0
        return (self.total_responses / self.emails_sent) * 100

class EmailTemplate(models.Model):
    """Templates for email communications"""
    TEMPLATE_TYPES = [
        ('invitation', 'Invitation'),
        ('reminder', 'Reminder'),
        ('confirmation', 'Confirmation'),
        ('update', 'Event Update'),
        ('thank_you', 'Thank You'),
    ]
    
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    subject = models.CharField(max_length=200)
    html_content = models.TextField()
    text_content = models.TextField()
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    class Meta:
        ordering = ['template_type', 'name']

class EventWaitlist(models.Model):
    """Waitlist for full events"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='waitlist')
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    position = models.IntegerField()
    joined_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)
    invitation_sent = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.guest} - Waitlist #{self.position} for {self.event}"
    
    class Meta:
        unique_together = ['event', 'guest']
        ordering = ['position']


class CheckInLog(models.Model):
    """Log each check-in for analytics and auditing"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='checkin_logs')
    invitation = models.ForeignKey(Invitation, on_delete=models.CASCADE, related_name='checkin_logs')
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='checkin_logs')
    checked_in_at = models.DateTimeField(auto_now_add=True)
    checked_in_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    table_number = models.CharField(max_length=50, blank=True)
    seat_number = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.guest} checked in to {self.event} at {self.checked_in_at.isoformat()}"

    class Meta:
        ordering = ['-checked_in_at']


class CheckInSession(models.Model):
    """Persistent record of a check-in session started by an usher/operator."""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='checkin_sessions')
    started_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='started_checkin_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ended_checkin_sessions')
    ended_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']

    def is_active(self):
        return self.ended_at is None

    def __str__(self):
        return f"Session for {self.event.name} started {self.started_at.isoformat()} by {self.started_by or 'unknown'}"
