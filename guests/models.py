from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.files import File
import uuid
import qrcode
from io import BytesIO
from PIL import Image
import os

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
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-date']

class Guest(models.Model):
    """Model for guest information"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Internal notes about the guest")
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
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
    
    # Personal message
    personal_message = models.TextField(blank=True, help_text="Personal message for this guest")
    
    def __str__(self):
        return f"Invitation to {self.guest} for {self.event}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.qr_code:
            self.generate_qr_code()
    
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
        
        # Save to model
        filename = f'qr_{self.unique_code}.png'
        self.qr_code.save(filename, File(buffer), save=False)
        super().save(update_fields=['qr_code'])
    
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
