from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Event, Guest, Invitation, RSVP, EventCategory, EventTemplate, 
    GuestProfile, EventAnalytics, EmailTemplate, EventWaitlist
)

# Set custom admin site headers/titles directly
admin.site.site_header = "Zambia Army Guest Tracking System Administration"
admin.site.site_title = "Zambia Army Guest Tracking System Admin"
admin.site.index_title = "Welcome to Zambia Army Guest Tracking System Administration"

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'location', 'created_by', 'invitation_count', 'rsvp_count']
    list_filter = ['date', 'created_by']
    search_fields = ['name', 'location']
    readonly_fields = ['created_at']
    
    def invitation_count(self, obj):
        return obj.invitations.count()
    invitation_count.short_description = 'Invitations Sent'
    
    def rsvp_count(self, obj):
        return sum(1 for inv in obj.invitations.all() if hasattr(inv, 'rsvp'))
    rsvp_count.short_description = 'RSVPs Received'

@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'created_at']
    list_filter = ['created_at']
    search_fields = ['first_name', 'last_name', 'email']
    readonly_fields = ['created_at']

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ['guest', 'event', 'email_sent', 'email_sent_at', 'rsvp_status', 'checked_in', 'rsvp_link']
    list_filter = ['event', 'email_sent', 'sent_at', 'checked_in']
    search_fields = ['guest__first_name', 'guest__last_name', 'guest__email', 'barcode_number']
    readonly_fields = ['unique_code', 'sent_at', 'rsvp_link', 'barcode_number', 'barcode_display', 'qr_display', 'check_in_time']
    
    def rsvp_status(self, obj):
        if hasattr(obj, 'rsvp'):
            status = obj.rsvp.get_response_display()
            color = {'Yes, I will attend': 'green', 'No, I cannot attend': 'red', 'Maybe, I am not sure': 'orange'}
            return format_html(
                '<span style="color: {};">{}</span>',
                color.get(status, 'black'),
                status
            )
        return format_html('<span style="color: gray;">No response</span>')
    rsvp_status.short_description = 'RSVP Status'
    
    def rsvp_link(self, obj):
        if obj.unique_code:
            url = obj.get_rsvp_url()
            return format_html('<a href="{}" target="_blank">RSVP Link</a>', url)
        return '-'
    rsvp_link.short_description = 'RSVP Link'
    
    def barcode_display(self, obj):
        if obj.barcode_image:
            return format_html('<img src="{}" style="max-width: 300px;" />', obj.barcode_image.url)
        return '-'
    barcode_display.short_description = 'Barcode'
    
    def qr_display(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" style="max-width: 150px;" />', obj.qr_code.url)
        return '-'
    qr_display.short_description = 'QR Code'

@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ['guest_name', 'event_name', 'response', 'plus_ones', 'total_guests', 'responded_at'
]
    list_filter = ['response', 'invitation__event', 'responded_at']
    search_fields = ['invitation__guest__first_name', 'invitation__guest__last_name']
    readonly_fields = ['responded_at', 'updated_at']
    
    def guest_name(self, obj):
        return obj.invitation.guest.full_name
    guest_name.short_description = 'Guest'
    
    def event_name(self, obj):
        return obj.invitation.event.name
    event_name.short_description = 'Event'

@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'color', 'icon']
    search_fields = ['name']

@admin.register(EventTemplate)
class EventTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'created_by', 'created_at']
    list_filter = ['category', 'created_by', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']

@admin.register(GuestProfile)
class GuestProfileAdmin(admin.ModelAdmin):
    list_display = ['guest', 'company', 'job_title', 'vip_status', 'preferred_contact_method']
    list_filter = ['vip_status', 'blacklisted', 'preferred_contact_method', 'subscribe_newsletter']
    search_fields = ['guest__first_name', 'guest__last_name', 'company', 'job_title']

@admin.register(EventAnalytics)
class EventAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['event', 'emails_sent', 'open_rate', 'response_rate', 'last_updated']
    list_filter = ['event', 'last_updated']
    readonly_fields = ['last_updated', 'open_rate', 'response_rate']
    
    def open_rate(self, obj):
        return f"{obj.open_rate:.1f}%"
    open_rate.short_description = 'Open Rate'
    
    def response_rate(self, obj):
        return f"{obj.response_rate:.1f}%"
    response_rate.short_description = 'Response Rate'

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'is_default', 'created_by', 'created_at']
    list_filter = ['template_type', 'is_default', 'created_by']
    search_fields = ['name', 'subject']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(EventWaitlist)
class EventWaitlistAdmin(admin.ModelAdmin):
    list_display = ['guest', 'event', 'position', 'joined_at', 'notified', 'invitation_sent']
    list_filter = ['event', 'notified', 'invitation_sent']
    search_fields = ['guest__first_name', 'guest__last_name', 'event__name']
    readonly_fields = ['joined_at']
