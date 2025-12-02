from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
from django.urls import reverse
from django.urls import path
from django.http import HttpResponse
from django.db.models import Count
from django.db.models.functions import TruncHour
from .models import (
    Event, Guest, Invitation, RSVP, EventCategory, EventTemplate, 
    GuestProfile, EventAnalytics, EmailTemplate, EventWaitlist, CheckInLog
)
from .models import Table, Seat
from .models import ProgramItem, MenuItem
from .models import CheckInSession


class ProgramItemInline(admin.TabularInline):
    model = ProgramItem
    extra = 1
    fields = ('start_time', 'title', 'description', 'order')


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = ('name', 'description', 'dietary_tags', 'order')


class TableInline(admin.TabularInline):
    model = Table
    extra = 1
    fields = ('number', 'capacity', 'section')


# Set custom admin site headers/titles directly
admin.site.site_header = "Zambia Army Guest Tracking System Administration"
admin.site.site_title = "Zambia Army Guest Tracking System Admin"
admin.site.index_title = "Welcome to Zambia Army Guest Tracking System Administration"

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'location', 'created_by', 'invitation_count', 'rsvp_count', 'checked_in_count', 'checkin_summary_link']
    list_filter = ['date', 'created_by']
    search_fields = ['name', 'location']
    readonly_fields = ['created_at']
    actions = ['save_as_template_action']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'date', 'location', 'created_by', 'event_banner')
        }),
        ('RSVP Settings', {
            'fields': ('rsvp_deadline', 'max_guests'),
            'description': 'Set RSVP deadline (date/time) and maximum number of guests allowed for this event.'
        }),
        ('Event Details', {
            'fields': ('dress_code', 'parking_info', 'special_instructions'),
            'classes': ('collapse',),
            'description': 'General event details such as dress code, parking and special instructions.'
        }),
        ('Seating Arrangement', {
            'fields': ('has_assigned_seating',),
            'classes': ('collapse',),
            'description': 'Enable assigned seating to use the seating assignment UI. Use the Tables inline to add tables and capacities, then create seats and assign guests.'
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'contact_phone', 'contact_email'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    inlines = [ProgramItemInline, MenuItemInline, TableInline]
    class Media:
        js = ('guests/js/move_inlines.js',)
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form to pre-populate from template if template_id is in query string"""
        form = super().get_form(request, obj, **kwargs)
        
        # Check for template_id in query string
        template_id = request.GET.get('template_id')
        if template_id and not obj:  # Only for new events
            try:
                template = EventTemplate.objects.get(id=template_id)
                # Set initial values from template
                form.base_fields['name'].initial = template.name
                form.base_fields['description'].initial = template.description
                form.base_fields['location'].initial = template.default_location
                form.base_fields['max_guests'].initial = template.default_max_guests
                form.base_fields['dress_code'].initial = template.dress_code
                form.base_fields['parking_info'].initial = template.parking_info
                form.base_fields['special_instructions'].initial = template.special_instructions
                form.base_fields['program_schedule'].initial = template.program_schedule
                form.base_fields['menu'].initial = template.menu
                form.base_fields['has_assigned_seating'].initial = template.has_assigned_seating
            except EventTemplate.DoesNotExist:
                pass
        
        return form
    
    def invitation_count(self, obj):
        return obj.invitations.count()
    invitation_count.short_description = 'Invitations Sent'
    
    def rsvp_count(self, obj):
        return sum(1 for inv in obj.invitations.all() if hasattr(inv, 'rsvp'))
    rsvp_count.short_description = 'RSVPs Received'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:event_id>/checkin-summary/', self.admin_site.admin_view(self.checkin_summary_view), name='guests_event_checkin_summary'),
            path('<int:event_id>/seating-assign/', self.admin_site.admin_view(self.seating_assignment_view), name='guests_event_seating_assign'),
            path('<int:event_id>/import-csv/', self.admin_site.admin_view(self.import_csv_view), name='guests_event_import_csv'),
            path('active-sessions/', self.admin_site.admin_view(self.active_sessions_view), name='guests_active_sessions'),
        ]
        return custom_urls + urls

    def checkin_summary_link(self, obj):
        url = reverse('admin:guests_event_checkin_summary', args=[obj.pk])
        return format_html('<a class="button" href="{}">Export Check-in Summary</a>', url)
    checkin_summary_link.short_description = 'Check-in Summary'

    def checkin_summary_view(self, request, event_id):
        """Admin view that returns CSV aggregate of check-ins for an event.

        Supports optional GET params `start` and `end` as ISO datetimes to filter the range.
        Requires `guests.export_checkin` permission.
        """
        from django.core.exceptions import PermissionDenied
        if not request.user.has_perm('guests.export_checkin') and not request.user.is_superuser:
            raise PermissionDenied

        # Parse optional date filters
        start = request.GET.get('start')
        end = request.GET.get('end')

        qs = CheckInLog.objects.filter(event_id=event_id)
        if start:
            try:
                from django.utils.dateparse import parse_datetime
                dt = parse_datetime(start)
                if dt is not None:
                    qs = qs.filter(checked_in_at__gte=dt)
            except Exception:
                pass
        if end:
            try:
                from django.utils.dateparse import parse_datetime
                dt = parse_datetime(end)
                if dt is not None:
                    qs = qs.filter(checked_in_at__lte=dt)
            except Exception:
                pass

        # Aggregate by table
        table_agg = qs.values('table_number').annotate(count=Count('id')).order_by('-count')

        # Aggregate by hour
        hour_agg = qs.annotate(hour=TruncHour('checked_in_at')).values('hour').annotate(count=Count('id')).order_by('hour')

        # Build CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=checkin_summary_event_{event_id}.csv'

        writer = __import__('csv').writer(response)

        writer.writerow(['Table Aggregates'])
        writer.writerow(['table_number', 'count'])
        for row in table_agg:
            writer.writerow([row['table_number'] or 'Unassigned', row['count']])

        writer.writerow([])
        writer.writerow(['Hourly Aggregates (UTC)'])
        writer.writerow(['hour', 'count'])
        for row in hour_agg:
            hour = row['hour'].isoformat() if row['hour'] else ''
            writer.writerow([hour, row['count']])

        return response

    def seating_assignment_view(self, request, event_id):
        """Admin view to visualize and edit seat assignments for an event."""
        from django.shortcuts import render, redirect
        from django.urls import reverse
        from django.contrib import messages
        if not request.user.has_perm('guests.change_event') and not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied

        event = Event.objects.get(pk=event_id)
        tables = event.tables.all().prefetch_related('seats')
        # Invitations for this event
        invitations = event.invitations.select_related('guest').all()

        if request.method == 'POST':
            action = request.POST.get('action', 'save')
            from guests.models import Seat, Invitation
            if action == 'save':
                # Iterate seats and update assigned_invitation based on POST
                changed = 0
                for table in tables:
                    for seat in table.seats.all():
                        key = f'seat_{seat.id}'
                        val = request.POST.get(key, '')
                        try:
                            if val == '':
                                if seat.assigned_invitation_id is not None:
                                    seat.assigned_invitation = None
                                    seat.save()
                                    changed += 1
                            else:
                                inv = Invitation.objects.get(pk=int(val))
                                if seat.assigned_invitation_id != inv.id:
                                    seat.assigned_invitation = inv
                                    seat.save()
                                    changed += 1
                        except Exception:
                            continue

                messages.success(request, f'Saved seating assignments ({changed} changes)')
                return redirect(reverse('admin:guests_event_change', args=[event_id]))
            elif action == 'auto_assign':
                # Auto assign remaining unassigned seats to unassigned invitations
                unassigned_invs = list(event.invitations.filter(assigned_seat__isnull=True).order_by('guest__last_name'))
                seats_to_fill = list(Seat.objects.select_for_update().filter(table__event=event, assigned_invitation__isnull=True).order_by('table__number', 'number'))
                assigned = 0
                for seat_obj, inv in zip(seats_to_fill, unassigned_invs):
                    seat_obj.assigned_invitation = inv
                    seat_obj.save()
                    assigned += 1
                messages.success(request, f'Auto-assigned {assigned} seats')
                return redirect(reverse('admin:guests_event_change', args=[event_id]))
            elif action == 'export':
                # Export seating assignment as CSV
                import csv
                from django.http import HttpResponse
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename=seating_event_{event_id}.csv'
                writer = csv.writer(response)
                writer.writerow(['table', 'seat', 'guest_name', 'guest_email', 'invitation_id'])
                for table in tables:
                    for seat in table.seats.all():
                        inv = seat.assigned_invitation
                        writer.writerow([
                            table.number,
                            seat.number,
                            inv.guest.full_name if inv else '',
                            inv.guest.email if inv else '',
                            inv.id if inv else ''
                        ])
                return response

        admin_event_url = reverse('admin:guests_event_change', args=[event_id])
        return render(request, 'admin/guests/event_seating_assign.html', {
            'event': event,
            'tables': tables,
            'invitations': invitations,
            'admin_event_url': admin_event_url,
        })

    def import_csv_view(self, request, event_id):
        """Admin view to import Program/Menu/Tables/Seating from CSV with preview."""
        from django.shortcuts import render, redirect
        from django.urls import reverse
        from django.contrib import messages
        import csv

        if not request.user.has_perm('guests.change_event') and not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied

        event = Event.objects.get(pk=event_id)

        parsed = []
        errors = []
        preview = False

        if request.method == 'POST':
            action = request.POST.get('action')
            source = request.POST.get('source', 'file')
            data_text = ''
            if source == 'textarea':
                data_text = request.POST.get('textarea_data', '')
            else:
                uploaded = request.FILES.get('csv_file')
                if uploaded:
                    try:
                        data_text = uploaded.read().decode('utf-8')
                    except Exception:
                        data_text = uploaded.read().decode('latin-1')

            import_type = request.POST.get('import_type')

            # Parse CSV-like content (support comma or pipe)
            if data_text.strip():
                reader = csv.reader([r for r in data_text.splitlines() if r.strip()])
                for i, row in enumerate(reader, start=1):
                    # Basic validation per import_type
                    if import_type == 'program':
                        # Expect: time,activity,description
                        if len(row) < 2:
                            errors.append((i, 'Expected at least time and activity'))
                            continue
                        parsed.append({'time': row[0].strip(), 'activity': row[1].strip(), 'description': (row[2].strip() if len(row) > 2 else '')})
                    elif import_type == 'menu':
                        # Expect: name,description,dietary_tags
                        if len(row) < 1:
                            errors.append((i, 'Expected at least name'))
                            continue
                        parsed.append({'name': row[0].strip(), 'description': (row[1].strip() if len(row) > 1 else ''), 'dietary_tags': (row[2].strip() if len(row) > 2 else '')})
                    elif import_type == 'tables':
                        # Expect: table_number,capacity,section
                        if len(row) < 2:
                            errors.append((i, 'Expected table_number and capacity'))
                            continue
                        parsed.append({'number': row[0].strip(), 'capacity': row[1].strip(), 'section': (row[2].strip() if len(row) > 2 else '')})
                    elif import_type == 'seating':
                        # Expect: table_number,seat_number,guest_email_or_barcode_or_code
                        if len(row) < 3:
                            errors.append((i, 'Expected table_number, seat_number, guest_identifier'))
                            continue
                        parsed.append({'table': row[0].strip(), 'seat': row[1].strip(), 'guest': row[2].strip()})
                    else:
                        errors.append((i, 'Unknown import type'))

            if action == 'preview':
                preview = True
            elif action == 'apply' and not errors:
                # Apply parsed rows
                if import_type == 'program':
                    # create ProgramItem rows
                    from .models import ProgramItem
                    created = 0
                    for idx, item in enumerate(parsed):
                        try:
                            ProgramItem.objects.create(event=event, start_time=item.get('time') or None, title=item.get('activity') or item.get('title') or '', description=item.get('description', ''), order=idx)
                            created += 1
                        except Exception as e:
                            errors.append(('save', str(e)))
                    messages.success(request, f'Imported {created} program items')
                elif import_type == 'menu':
                    from .models import MenuItem
                    created = 0
                    for idx, item in enumerate(parsed):
                        try:
                            MenuItem.objects.create(event=event, name=item.get('name',''), description=item.get('description',''), dietary_tags=item.get('dietary_tags',''), order=idx)
                            created += 1
                        except Exception as e:
                            errors.append(('save', str(e)))
                    messages.success(request, f'Imported {created} menu items')
                elif import_type == 'tables':
                    created = 0
                    for item in parsed:
                        try:
                            t, created_flag = Table.objects.get_or_create(event=event, number=str(item.get('number')))
                            try:
                                t.capacity = int(item.get('capacity') or 0)
                            except Exception:
                                t.capacity = 0
                            t.section = item.get('section', '')
                            t.save()
                            created += 1 if created_flag else 0
                        except Exception as e:
                            errors.append(('save', str(e)))
                    messages.success(request, f'Processed {len(parsed)} table rows')
                elif import_type == 'seating':
                    created = 0
                    for item in parsed:
                        try:
                            table = Table.objects.filter(event=event, number=str(item.get('table'))).first()
                            if not table:
                                errors.append((item, 'Table not found'))
                                continue
                            seat_obj, _ = Seat.objects.get_or_create(table=table, number=str(item.get('seat')))
                            # find invitation by email, barcode, or unique_code
                            inv = Invitation.objects.filter(event=event, guest__email__iexact=item.get('guest')).first()
                            if not inv:
                                inv = Invitation.objects.filter(event=event, barcode_number=item.get('guest')).first()
                            if not inv:
                                try:
                                    import uuid
                                    inv = Invitation.objects.filter(event=event, unique_code=item.get('guest')).first()
                                except Exception:
                                    inv = None
                            if not inv:
                                errors.append((item, 'Invitation not found for guest identifier'))
                                continue
                            seat_obj.assigned_invitation = inv
                            seat_obj.save()
                            created += 1
                        except Exception as e:
                            errors.append(('save', str(e)))
                    messages.success(request, f'Assigned {created} seats')

                # after apply redirect back to event change page
                return redirect(reverse('admin:guests_event_change', args=[event_id]))

        admin_event_url = reverse('admin:guests_event_change', args=[event_id])
        return render(request, 'admin/guests/event_import_csv.html', {
            'event': event,
            'parsed': parsed,
            'errors': errors,
            'preview': preview,
            'admin_event_url': admin_event_url,
        })

    def active_sessions_view(self, request):
        """Admin view: list active check-in sessions for events and allow forcing end of sessions."""
        from django.core.cache import cache
        from django.shortcuts import render, redirect
        from django.urls import reverse
        from django.contrib import messages

        if not (request.user.is_superuser or request.user.has_perm('guests.change_event')):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied

        # Start / End session actions
        if request.method == 'POST':
            action = request.POST.get('action')
            event_id = request.POST.get('event_id')
            if not event_id:
                messages.error(request, 'event_id required')
                return redirect(reverse('admin:guests_active_sessions'))

            # End existing session: clear cache and mark DB record ended
            if action == 'end':
                cache.delete(f'guests:checkin_session:{event_id}')
                try:
                    from django.conf import settings as dj_settings
                    from .models import CheckInSession
                    active = CheckInSession.objects.filter(event_id=event_id, ended_at__isnull=True).order_by('-started_at').first()
                    if active:
                        active.ended_at = timezone.now()
                        active.ended_by = request.user
                        active.save(update_fields=['ended_at', 'ended_by'])
                except Exception:
                    logger.exception('Failed to mark CheckInSession ended when admin forced end for event %s', event_id)

                messages.success(request, f'Ended session for event {event_id}')
                return redirect(reverse('admin:guests_active_sessions'))

            # Start a new session: create DB record and set cache value
            if action == 'start':
                try:
                    from django.conf import settings as dj_settings
                    from .models import CheckInSession, Event as _Event
                    ev = _Event.objects.filter(id=event_id).first()
                    if not ev:
                        messages.error(request, f'Event {event_id} not found')
                        return redirect(reverse('admin:guests_active_sessions'))

                    # Prevent multiple active DB sessions
                    active_db = CheckInSession.objects.filter(event=ev, ended_at__isnull=True).first()
                    if active_db:
                        messages.warning(request, f'A session is already active for event {event_id}')
                        return redirect(reverse('admin:guests_active_sessions'))

                    sess = CheckInSession.objects.create(event=ev, started_by=request.user)

                    # Prepare session payload and cache it
                    session_key = f'guests:checkin_session:{event_id}'
                    session_data = {
                        'event_id': int(event_id),
                        'event_name': ev.name,
                        'started_by': request.user.username,
                        'started_at': timezone.now().isoformat(),
                        'session_id': sess.id,
                    }
                    timeout = getattr(dj_settings, 'CHECKIN_SESSION_TIMEOUT', 60 * 60 * 8)
                    cache.set(session_key, session_data, timeout=timeout)

                    messages.success(request, f'Started session for event {event_id}')
                except Exception:
                    logger.exception('Failed to start CheckInSession for event %s', event_id)
                    messages.error(request, f'Failed to start session for event {event_id}')

                return redirect(reverse('admin:guests_active_sessions'))

        events = Event.objects.order_by('-date')[:200]
        sessions = []
        for ev in events:
            key = f'guests:checkin_session:{ev.id}'
            s = cache.get(key)
            # Also include recent DB-backed sessions for audit display
            recent_db = []
            try:
                from .models import CheckInSession
                recent_db_qs = CheckInSession.objects.filter(event=ev).order_by('-started_at')[:5]
                for dbs in recent_db_qs:
                    recent_db.append(dbs)
            except Exception:
                recent_db = []

            sessions.append({'event': ev, 'session': s, 'recent_db': recent_db})

        return render(request, 'admin/guests/active_sessions.html', {
            'sessions': sessions,
        })
    
    def save_as_template_action(self, request, queryset):
        """Admin action to save selected events as templates"""
        if queryset.count() != 1:
            self.message_user(request, 'Please select exactly one event to save as template.', level='WARNING')
            return
        
        event = queryset.first()
        
        # Create template from event
        template = EventTemplate.objects.create(
            name=f"{event.name} (Template)",
            description=event.description,
            default_location=event.location,
            default_max_guests=event.max_guests,
            default_rsvp_deadline_days=7,
            dress_code=event.dress_code,
            parking_info=event.parking_info,
            special_instructions=event.special_instructions,
            program_schedule=event.program_schedule.copy() if event.program_schedule else {},
            menu=event.menu.copy() if event.menu else {},
            has_assigned_seating=event.has_assigned_seating,
            created_by=request.user
        )
        
        self.message_user(request, f'✅ Template "{template.name}" created successfully! You can now use it to create future events.')
        
        # Redirect to the template edit page
        return HttpResponse(f'<script>window.location.href="{reverse("admin:guests_eventtemplate_change", args=[template.id])}";</script>')
    
    save_as_template_action.short_description = 'Save selected event as template'

@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'rank', 'institution', 'photo_thumbnail', 'created_at']
    list_filter = ['created_at', 'rank', 'institution']
    search_fields = ['first_name', 'last_name', 'email', 'rank', 'institution']
    readonly_fields = ['created_at', 'photo_preview']
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'address')
        }),
        ('Professional Details', {
            'fields': ('rank', 'institution', 'notes')
        }),
        ('Photo', {
            'fields': ('photo', 'photo_preview')
        }),
        ('Portal Access', {
            'fields': ('user', 'can_login', 'last_login'),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def photo_thumbnail(self, obj):
        """Display small thumbnail in list view"""
        if obj.photo:
            return format_html('<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />', obj.photo.url)
        return format_html('<span style="color: #999;">No photo</span>')
    photo_thumbnail.short_description = 'Photo'
    
    def photo_preview(self, obj):
        """Display larger preview in detail view"""
        if obj.photo:
            return format_html('<img src="{}" width="150" height="150" style="border-radius: 10px; object-fit: cover;" />', obj.photo.url)
        return format_html('<span style="color: #999;">No photo uploaded</span>')
    photo_preview.short_description = 'Photo Preview'

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ['guest', 'event', 'email_sent', 'email_sent_at', 'rsvp_status', 'table_number', 'seat_number', 'checked_in', 'rsvp_link']
    list_filter = ['event', 'email_sent', 'sent_at', 'checked_in', 'table_number']
    search_fields = ['guest__first_name', 'guest__last_name', 'guest__email', 'barcode_number', 'table_number', 'seat_number']
    readonly_fields = ['unique_code', 'sent_at', 'rsvp_link', 'barcode_number', 'barcode_display', 'qr_display', 'check_in_time']
    actions = ['resend_invitations_action']
    list_editable = ['table_number', 'seat_number']
    fieldsets = (
        ('Guest & Event', {
            'fields': ('event', 'guest', 'unique_code')
        }),
        ('Seating Assignment', {
            'fields': ('table_number', 'seat_number'),
            'description': 'Assign table and seat numbers for this guest'
        }),
        ('Invitation Status', {
            'fields': ('status', 'email_sent', 'email_sent_at', 'sent_at', 'opened_at')
        }),
        ('Check-in', {
            'fields': ('checked_in', 'check_in_time')
        }),
        ('Codes', {
            'fields': ('barcode_number', 'barcode_display', 'qr_display', 'rsvp_link'),
            'classes': ('collapse',)
        }),
        ('Personal Message', {
            'fields': ('personal_message',),
            'classes': ('collapse',)
        }),
    )
    
    def resend_invitations_action(self, request, queryset):
        """Admin action to resend selected invitations"""
        from django.utils import timezone
        from guests.views import send_invitation_email
        
        sent_count = 0
        for invitation in queryset:
            try:
                send_invitation_email(invitation, request)
                invitation.email_sent = True
                invitation.email_sent_at = timezone.now()
                invitation.status = 'sent'
                invitation.save(update_fields=['email_sent', 'email_sent_at', 'status'])
                sent_count += 1
            except Exception as e:
                self.message_user(request, f'Error sending to {invitation.guest.full_name}: {str(e)}', level='ERROR')
        
        self.message_user(request, f'Successfully resent {sent_count} invitation(s)!')
    
    resend_invitations_action.short_description = "Resend selected invitations"
    
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
    list_display = ['name', 'category', 'created_by', 'created_at', 'create_event_button']
    list_filter = ['category', 'created_by', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    actions = ['create_event_from_template_action']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'description', 'category')
        }),
        ('Default Settings', {
            'fields': ('default_location', 'default_max_guests', 'default_rsvp_deadline_days')
        }),
        ('Event Details', {
            'fields': ('dress_code', 'parking_info', 'special_instructions', 'has_assigned_seating')
        }),
        ('Program & Menu', {
            'fields': ('program_schedule', 'menu'),
            'classes': ('collapse',)
        }),
        ('Email Template', {
            'fields': ('email_template',),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def create_event_button(self, obj):
        """Display a button to create event from this template"""
        return format_html(
            '<a class="button" href="{}?template_id={}" style="padding: 5px 10px; background: #417690; color: white; border-radius: 4px; text-decoration: none;">Use Template</a>',
            reverse('admin:guests_event_add'),
            obj.id
        )
    create_event_button.short_description = 'Actions'
    
    def create_event_from_template_action(self, request, queryset):
        """Bulk action to create events from selected templates"""
        if queryset.count() != 1:
            self.message_user(request, 'Please select exactly one template to use.', level='WARNING')
            return
        
        template = queryset.first()
        return HttpResponse(f'<script>window.location.href="{reverse("admin:guests_event_add")}?template_id={template.id}";</script>')
    
    create_event_from_template_action.short_description = 'Create event from selected template'
    
    def save_model(self, request, obj, form, change):
        """Auto-set created_by on new templates"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

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


@admin.register(CheckInLog)
class CheckInLogAdmin(admin.ModelAdmin):
    list_display = ['guest', 'event', 'checked_in_at', 'checked_in_by', 'table_number', 'seat_number']
    list_filter = ['event', 'checked_in_at', 'checked_in_by']
    search_fields = ['guest__first_name', 'guest__last_name', 'invitation__barcode_number']
    readonly_fields = ['checked_in_at']
    actions = ['export_as_csv']

    def export_as_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        meta = self.model._meta
        field_names = ['guest', 'event', 'checked_in_at', 'checked_in_by', 'table_number', 'seat_number']

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=checkin_logs.csv'

        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([
                obj.guest.full_name,
                obj.event.name,
                obj.checked_in_at.isoformat(),
                obj.checked_in_by.username if obj.checked_in_by else '',
                obj.table_number,
                obj.seat_number,
            ])
        return response

    export_as_csv.short_description = "Export selected check-in logs as CSV"


@admin.register(CheckInSession)
class CheckInSessionAdmin(admin.ModelAdmin):
    list_display = ['event', 'started_at', 'started_by', 'ended_at', 'ended_by']
    list_filter = ['event', 'started_at', 'ended_at']
    search_fields = ['event__name', 'started_by__username', 'ended_by__username']
    readonly_fields = ['started_at', 'ended_at']


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'event', 'capacity', 'section']
    list_filter = ['event', 'section']
    search_fields = ['number', 'event__name']
    actions = ['create_seats_action']

    def create_seats_action(self, request, queryset):
        created = 0
        for table in queryset:
            try:
                capacity = int(table.capacity or 0)
            except Exception:
                capacity = 0
            # Create seats 1..capacity if they don't already exist
            for i in range(1, capacity + 1):
                seat_number = str(i)
                obj, was_created = Seat.objects.get_or_create(table=table, number=seat_number)
                if was_created:
                    created += 1
        self.message_user(request, f'Created {created} seat(s)')

    create_seats_action.short_description = 'Create seats up to table capacity for selected tables'


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['table', 'number', 'assigned_invitation']
    list_filter = ['table__event', 'table']
    search_fields = ['table__number', 'number', 'assigned_invitation__guest__first_name', 'assigned_invitation__guest__last_name']

