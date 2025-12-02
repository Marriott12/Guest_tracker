from django.http import JsonResponse, HttpResponse
from django.db.models import Count
from django.db.models.functions import TruncHour
from django.contrib.auth.decorators import login_required

@login_required
def checkin_summary_json(request, event_id):
    """Return JSON aggregates for check-ins for an event, filtered by optional start/end, requires export_checkin permission."""
    from django.core.exceptions import PermissionDenied
    if not request.user.has_perm('guests.export_checkin') and not request.user.is_superuser:
        raise PermissionDenied

    start = request.GET.get('start')
    end = request.GET.get('end')
    from .models import CheckInLog
    qs = CheckInLog.objects.filter(event_id=event_id)
    if start:
        from django.utils.dateparse import parse_datetime
        dt = parse_datetime(start)
        if dt is not None:
            qs = qs.filter(checked_in_at__gte=dt)
    if end:
        from django.utils.dateparse import parse_datetime
        dt = parse_datetime(end)
        if dt is not None:
            qs = qs.filter(checked_in_at__lte=dt)

    table_agg = list(qs.values('table_number').annotate(count=Count('id')).order_by('-count'))
    hour_agg = list(qs.annotate(hour=TruncHour('checked_in_at')).values('hour').annotate(count=Count('id')).order_by('hour'))

    return JsonResponse({
        'table_agg': table_agg,
        'hour_agg': [
            {'hour': row['hour'].isoformat() if row['hour'] else '', 'count': row['count']}
            for row in hour_agg
        ]
    })
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from email.mime.image import MIMEImage
from django.template.loader import render_to_string
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.utils import timezone
from django.db.models import Count, Q
from django_ratelimit.decorators import ratelimit
from django.views.decorators.http import require_POST
import json
from .models import Event, Guest, Invitation, RSVP
from .models import CheckInSession
from django.core.cache import cache
from .forms import RSVPForm, GuestForm, GuestProfileForm, UserProfileForm, GuestRegistrationForm
import logging
import os

# Optional Google reCAPTCHA Enterprise client
try:
    from google.cloud import recaptchaenterprise_v1
    from google.oauth2 import service_account
    RECAPTCHA_ENTERPRISE_AVAILABLE = True
except Exception:
    recaptchaenterprise_v1 = None
    service_account = None
    RECAPTCHA_ENTERPRISE_AVAILABLE = False

logger = logging.getLogger(__name__)

def home(request):
    """Landing page with RBAC - redirects authenticated users to appropriate dashboard"""
    
    # If user is authenticated, redirect based on role
    if request.user.is_authenticated:
        # Check if user is admin/staff
        if request.user.is_staff or request.user.is_superuser:
            return redirect('organizer_dashboard')
        else:
            # Regular user - redirect to guest portal
            return redirect('guest_portal')
    
    # For unauthenticated users, show landing page with login/signup
    # Get upcoming events (public view)
    upcoming_events = Event.objects.filter(
        date__gte=timezone.now()
    ).annotate(
        total_invitations=Count('invitations'),
        confirmed_guests=Count(
            'invitations__rsvp', 
            filter=Q(invitations__rsvp__response='yes')
        )
    ).order_by('date')[:6]
    
    # Get past events
    past_events = Event.objects.filter(
        date__lt=timezone.now()
    ).annotate(
        total_invitations=Count('invitations'),
        confirmed_guests=Count(
            'invitations__rsvp', 
            filter=Q(invitations__rsvp__response='yes')
        )
    ).order_by('-date')[:4]
    
    # Calculate statistics
    total_events = Event.objects.count()
    total_guests = Guest.objects.count()
    total_rsvps = RSVP.objects.count()
    upcoming_count = upcoming_events.count()
    
    context = {
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'stats': {
            'total_events': total_events,
            'total_guests': total_guests,
            'total_rsvps': total_rsvps,
            'upcoming_count': upcoming_count,
        },
        'show_auth_options': True,  # Flag to show login/signup buttons
    }
    
    return render(request, 'guests/landing.html', context)

@login_required
def login_redirect(request):
    """Custom login redirect based on user role (RBAC)"""
    if request.user.is_staff or request.user.is_superuser:
        # Admin/Staff users go to organizer dashboard
        return redirect('organizer_dashboard')
    else:
        # Regular users go to guest portal
        return redirect('guest_portal')

@login_required
def organizer_dashboard(request):
    """Simplified dashboard for event organizers"""
    user_events = Event.objects.filter(created_by=request.user).annotate(
        total_invitations=Count('invitations'),
        confirmed_guests=Count(
            'invitations__rsvp', 
            filter=Q(invitations__rsvp__response='yes')
        ),
        pending_rsvps=Count('invitations') - Count('invitations__rsvp')
    ).order_by('-date')
    
    # Recent RSVP activity
    recent_rsvps = RSVP.objects.filter(
        invitation__event__created_by=request.user
    ).select_related('invitation__guest', 'invitation__event').order_by('-responded_at')[:10]
    
    context = {
        'user_events': user_events,
        'recent_rsvps': recent_rsvps,
        'total_events': user_events.count(),
        'upcoming_events': user_events.filter(date__gte=timezone.now()).count(),
    }
    
    return render(request, 'guests/organizer_dashboard.html', context)

def rsvp_response(request, code):
    """Handle RSVP responses from guests"""
    invitation = get_object_or_404(Invitation, unique_code=code)
    
    # Check if RSVP already exists
    rsvp, created = RSVP.objects.get_or_create(invitation=invitation)
    
    if request.method == 'POST':
        form = RSVPForm(request.POST, instance=rsvp)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you for your RSVP!')
            return render(request, 'guests/rsvp_success.html', {
                'invitation': invitation,
                'rsvp': rsvp
            })
    else:
        form = RSVPForm(instance=rsvp)
    
    return render(request, 'guests/rsvp_form.html', {
        'form': form,
        'invitation': invitation,
        'rsvp': rsvp
    })

@login_required
def event_dashboard(request, event_id):
    """Dashboard view for event organizers"""
    event = get_object_or_404(Event, id=event_id, created_by=request.user)
    invitations = event.invitations.all().select_related('guest').prefetch_related('rsvp')
    
    # Calculate statistics
    total_invitations = invitations.count()
    rsvp_yes = sum(1 for inv in invitations if hasattr(inv, 'rsvp') and inv.rsvp.response == 'yes')
    rsvp_no = sum(1 for inv in invitations if hasattr(inv, 'rsvp') and inv.rsvp.response == 'no')
    rsvp_maybe = sum(1 for inv in invitations if hasattr(inv, 'rsvp') and inv.rsvp.response == 'maybe')
    no_response = total_invitations - (rsvp_yes + rsvp_no + rsvp_maybe)
    
    total_expected_guests = sum(
        inv.rsvp.total_guests for inv in invitations 
        if hasattr(inv, 'rsvp') and inv.rsvp.response == 'yes'
    )
    
    context = {
        'event': event,
        'invitations': invitations,
        'stats': {
            'total_invitations': total_invitations,
            'rsvp_yes': rsvp_yes,
            'rsvp_no': rsvp_no,
            'rsvp_maybe': rsvp_maybe,
            'no_response': no_response,
            'total_expected_guests': total_expected_guests,
        }
    }
    
    return render(request, 'guests/event_dashboard.html', context)

@login_required
@ratelimit(key='user', rate='50/h', method='POST', block=True)
def send_invitations(request, event_id):
    """Send email invitations for an event"""
    event = get_object_or_404(Event, id=event_id, created_by=request.user)
    
    if request.method == 'POST':
        invitation_ids = request.POST.getlist('invitation_ids')
        resend = request.POST.get('resend', 'false') == 'true'
        sent_count = 0
        
        logger.info(f"User {request.user.username} sending invitations for event {event.name}")
        
        for invitation_id in invitation_ids:
            try:
                invitation = Invitation.objects.get(id=invitation_id, event=event)
                # Send if not sent before OR if explicitly resending
                if not invitation.email_sent or resend:
                    send_invitation_email(invitation, request)
                    invitation.email_sent = True
                    invitation.email_sent_at = timezone.now()
                    invitation.status = 'sent'
                    invitation.save(update_fields=['email_sent', 'email_sent_at', 'status'])
                    sent_count += 1
            except Invitation.DoesNotExist:
                logger.warning(f"Invitation {invitation_id} not found for event {event.id}")
                continue
        
        logger.info(f"Sent {sent_count} invitations for event {event.name}")
        
        if resend:
            messages.success(request, f'Successfully resent {sent_count} invitation(s)!')
        else:
            messages.success(request, f'Successfully sent {sent_count} invitation(s)!')
        return redirect('event_dashboard', event_id=event.id)
    
    # Get invitations that haven't been sent yet
    pending_invitations = event.invitations.filter(email_sent=False).select_related('guest')
    
    return render(request, 'guests/send_invitations.html', {
        'event': event,
        'pending_invitations': pending_invitations
    })

def send_invitation_email(invitation, request=None):
    """Send invitation email to a guest"""
    subject = f"You're invited to {invitation.event.name}!"
    
    # Create RSVP URL
    rsvp_url = invitation.get_rsvp_url()
    if request:
        rsvp_url = request.build_absolute_uri(rsvp_url)
    
    context = {
        'invitation': invitation,
        'rsvp_url': rsvp_url,
    }
    
    html_message = render_to_string('guests/invitation_email.html', context)
    plain_message = render_to_string('guests/invitation_email.txt', context)

    # Use EmailMultiAlternatives to support HTML + inline images
    msg = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[invitation.guest.email],
    )
    msg.attach_alternative(html_message, 'text/html')

    # Prepare CIDs and attach images inline if available
    qr_cid = None
    barcode_cid = None
    try:
        if invitation.qr_code and hasattr(invitation.qr_code, 'path') and os.path.exists(invitation.qr_code.path):
            with open(invitation.qr_code.path, 'rb') as f:
                img_data = f.read()
                mime_img = MIMEImage(img_data)
                qr_cid = f"qr-{invitation.id}@guesttracker"
                mime_img.add_header('Content-ID', f"<{qr_cid}>")
                mime_img.add_header('Content-Disposition', 'inline', filename=os.path.basename(invitation.qr_code.name))
                msg.attach(mime_img)
    except Exception:
        logger.exception('Failed to attach QR code for invitation %s', getattr(invitation, 'id', None))

    try:
        if invitation.barcode_image and hasattr(invitation.barcode_image, 'path') and os.path.exists(invitation.barcode_image.path):
            with open(invitation.barcode_image.path, 'rb') as f:
                img_data = f.read()
                mime_img = MIMEImage(img_data)
                barcode_cid = f"barcode-{invitation.id}@guesttracker"
                mime_img.add_header('Content-ID', f"<{barcode_cid}>")
                mime_img.add_header('Content-Disposition', 'inline', filename=os.path.basename(invitation.barcode_image.name))
                msg.attach(mime_img)
    except Exception:
        logger.exception('Failed to attach barcode image for invitation %s', getattr(invitation, 'id', None))

    # If we attached images, re-render HTML with the CID references
    if qr_cid or barcode_cid:
        context['qr_cid'] = qr_cid
        context['barcode_cid'] = barcode_cid
        html_message = render_to_string('guests/invitation_email.html', context)
        # replace existing HTML alternative using the public API
        msg.alternatives = []
        msg.attach_alternative(html_message, 'text/html')

    msg.send(fail_silently=False)

@login_required
def add_guest(request, event_id=None):
    """Add a new guest and optionally create invitation and send email"""
    event = None
    if event_id:
        event = get_object_or_404(Event, id=event_id, created_by=request.user)
    
    if request.method == 'POST':
        form = GuestForm(request.POST, request.FILES)
        if form.is_valid():
            guest = form.save()
            
            # Get event from form if not from URL
            if not event:
                event = form.cleaned_data.get('event')
            
            # Create invitation if event is specified
            if event:
                invitation, created = Invitation.objects.get_or_create(
                    event=event,
                    guest=guest
                )
                if created:
                    # Send invitation email if requested
                    if form.cleaned_data.get('send_invitation'):
                        send_invitation_email(invitation, request=request)
                        invitation.email_sent = True
                        invitation.email_sent_at = timezone.now()
                        invitation.save(update_fields=['email_sent', 'email_sent_at'])
                        messages.success(request, f'✅ Guest {guest.full_name} added, invited to {event.name}, and email sent!')
                    else:
                        messages.success(request, f'Guest {guest.full_name} added and invited to {event.name}!')
                else:
                    messages.info(request, f'Guest {guest.full_name} was already invited to {event.name}.')
                return redirect('event_dashboard', event_id=event.id)
            else:
                messages.success(request, f'Guest {guest.full_name} added successfully!')
                return redirect('add_guest')
    else:
        # Initialize form with event pre-selected if coming from event dashboard
        initial = {}
        if event:
            initial['event'] = event
            initial['send_invitation'] = True
        form = GuestForm(initial=initial)
    
    return render(request, 'guests/add_guest.html', {
        'form': form,
        'event': event
    })

def qr_code_view(request, code):
    """Display QR code for an invitation"""
    invitation = get_object_or_404(Invitation, code=code)
    
    # Generate QR code if it doesn't exist
    if not invitation.qr_code:
        invitation.generate_qr_code()
    
    return render(request, 'guests/qr_code.html', {
        'invitation': invitation,
    })

def analytics_placeholder(request):
    """Placeholder analytics dashboard"""
    return render(request, 'guests/analytics_placeholder.html', {
        'total_events': Event.objects.count(),
        'total_guests': Guest.objects.count(),
        'total_invitations': Invitation.objects.count(),
    })

def past_events(request):
    """Show all past events"""
    from django.db.models import Count, Q
    from .models import Event
    from django.utils import timezone
    past_events = Event.objects.filter(date__lt=timezone.now()).annotate(
        total_invitations=Count('invitations'),
        confirmed_guests=Count(
            'invitations__rsvp',
            filter=Q(invitations__rsvp__response='yes')
        )
    ).order_by('-date')
    return render(request, 'guests/past_events.html', {'past_events': past_events})

@login_required
def scan_barcode(request):
    """Scan barcode and display guest information"""
    invitation = None
    error_message = None
    
    # Get upcoming events for event selection
    upcoming_events = Event.objects.filter(
        date__gte=timezone.now()
    ).order_by('date')[:50]
    
    # Get event_id from URL parameter if present
    initial_event_id = request.GET.get('event_id')
    
    if request.method == 'POST':
        barcode_number = request.POST.get('barcode_number', '').strip()
        event_id = request.POST.get('event_id') or request.GET.get('event_id')
        
        if barcode_number:
            try:
                if event_id:
                    invitation = Invitation.objects.select_related('guest', 'event').get(barcode_number=barcode_number, event_id=event_id)
                else:
                    invitation = Invitation.objects.select_related('guest', 'event').get(barcode_number=barcode_number)
            except Invitation.DoesNotExist:
                error_message = f"No invitation found for barcode: {barcode_number}"
    
    return render(request, 'guests/scan_barcode.html', {
        'invitation': invitation,
        'error_message': error_message,
        'events': upcoming_events,
        'initial_event_id': initial_event_id,
    })


def mobile_scanner(request):
    """Mobile-optimized scanner with camera support"""
    upcoming_events = Event.objects.filter(
        date__gte=timezone.now()
    ).order_by('date')[:50]
    
    initial_event_id = request.GET.get('event_id')
    
    return render(request, 'guests/mobile_scanner.html', {
        'events': upcoming_events,
        'initial_event_id': initial_event_id
    })


@login_required
def scanner_ui(request):
    """Staff-facing scanner UI that looks up an invitation and allows optional table/seat override before check-in."""
    if not (request.user.is_staff or request.user.is_superuser):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    # Provide a list of upcoming events for the usher to select which check-in session to start
    from django.utils import timezone
    events = Event.objects.filter(date__gte=timezone.now()).order_by('date').values('id', 'name', 'date')[:50]
    return render(request, 'guests/scanner_ui.html', {'events': list(events)})


@login_required
def api_recent_checkins(request):
    """API endpoint to get recent check-ins for an event with undo capability"""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'status': 'forbidden', 'message': 'Not authorized'}, status=403)
    
    event_id = request.GET.get('event_id')
    limit = int(request.GET.get('limit', 20))
    
    if not event_id:
        return JsonResponse({'status': 'error', 'message': 'event_id required'}, status=400)
    
    recent_checkins = Invitation.objects.filter(
        event_id=event_id,
        checked_in=True
    ).select_related('guest').order_by('-check_in_time')[:limit]
    
    data = [{
        'id': inv.id,
        'guest_name': inv.guest.full_name,
        'barcode': inv.barcode_number,
        'check_in_time': inv.check_in_time.isoformat() if inv.check_in_time else None,
        'table_number': inv.table_number or '',
        'seat_number': inv.seat_number or ''
    } for inv in recent_checkins]
    
    return JsonResponse({'success': True, 'checkins': data})


@require_POST
@ratelimit(key='user', rate='60/h', method='POST', block=True)
@login_required
def api_check_in(request):
    """API endpoint for scanning/checking-in a guest via barcode or unique code.

    Accepts JSON body with one of:
      - barcode_number
      - unique_code
    Optional fields:
      - check_in: boolean (if true, perform check-in)
      - table_number, seat_number: strings to assign seating
      - undo: boolean (if true, undo the check-in)

    Returns JSON with invitation and guest info or an error message.
    """
    logger.info(f"api_check_in called by user={getattr(request.user, 'username', 'anonymous')} from {request.META.get('REMOTE_ADDR')}")

    # Enforce role-based permission: only staff/superusers can perform check-ins
    if not (request.user.is_staff or request.user.is_superuser):
        logger.warning(f"Unauthorized check-in attempt by user={getattr(request.user, 'username', 'anonymous')}")
        return JsonResponse({'status': 'forbidden', 'message': 'User not authorized to perform check-ins.'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        # Fallback to POST form-encoded
        data = request.POST

    barcode = data.get('barcode_number') or data.get('barcode')
    unique_code = data.get('unique_code')
    event_id = data.get('event_id') or data.get('event')
    do_check = data.get('check_in') in [True, 'true', 'True', '1', 1]
    do_undo = data.get('undo') in [True, 'true', 'True', '1', 1]
    table = data.get('table_number')
    seat = data.get('seat_number')

    # If the deployment requires a barcode for check-ins, reject non-barcode requests
    if do_check and getattr(settings, 'CHECKIN_REQUIRE_BARCODE', False) and not barcode:
        return JsonResponse({'status': 'error', 'message': 'Barcode required for check-in by server configuration.'}, status=400)

    # If session enforcement is enabled, require event_id and an active session for that event
    if getattr(settings, 'CHECKIN_SESSION_ENFORCE', False) and (request.user.is_staff or request.user.is_superuser):
        if not event_id:
            return JsonResponse({'status': 'error', 'message': 'event_id is required while check-in sessions are enforced.'}, status=400)
        session_key = f'guests:checkin_session:{event_id}'
        active = cache.get(session_key)
        if not active:
            return JsonResponse({'status': 'error', 'message': 'No active check-in session for the requested event.'}, status=400)

    invitation = None
    if barcode:
        try:
            if event_id:
                invitation = Invitation.objects.select_related('guest', 'event').get(barcode_number=barcode, event_id=event_id)
            else:
                invitation = Invitation.objects.select_related('guest', 'event').get(barcode_number=barcode)
        except Invitation.DoesNotExist:
            logger.info(f"api_check_in: barcode not found: {barcode}")
            return JsonResponse({'status': 'not_found', 'message': f'No invitation found for barcode {barcode}'}, status=404)
    elif unique_code:
        try:
            if event_id:
                invitation = Invitation.objects.select_related('guest', 'event').get(unique_code=unique_code, event_id=event_id)
            else:
                invitation = Invitation.objects.select_related('guest', 'event').get(unique_code=unique_code)
        except Invitation.DoesNotExist:
            logger.info(f"api_check_in: unique code not found: {unique_code}")
            return JsonResponse({'status': 'not_found', 'message': f'No invitation found for code {unique_code}'}, status=404)
    else:
        return JsonResponse({'status': 'error', 'message': 'No identifier provided (barcode_number or unique_code required).'}, status=400)

    # Handle undo operation
    if do_undo:
        if invitation.checked_in:
            invitation.checked_in = False
            invitation.check_in_time = None
            invitation.table_number = ''
            invitation.seat_number = ''
            invitation.save()
            logger.info(f"Check-in undone for {invitation.guest.full_name} by {request.user.username}")
            return JsonResponse({
                'success': True,
                'message': f'Check-in undone for {invitation.guest.full_name}',
                'guest_name': invitation.guest.full_name,
                'checked_in': False
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'Guest is not checked in.'}, status=400)

    # Only assign seating when performing check-in.
    if do_check:
        # Use the new method that assigns seating only during check-in
        checked = invitation.check_in_guest_with_seating(table=table, seat=seat, checked_in_by=request.user)


    payload = {
        'status': 'ok',
        'invitation': {
            'guest_name': invitation.guest.full_name,
            'guest_rank': getattr(invitation.guest, 'rank', '') or '',
            'guest_institution': getattr(invitation.guest, 'institution', '') or '',
            'email': invitation.guest.email,
            'event': invitation.event.name,
            'checked_in': invitation.checked_in,
            'check_in_time': invitation.check_in_time.isoformat() if invitation.check_in_time else None,
            # Include seating details regardless of check-in status
            'table_number': invitation.table_number or '',
            'seat_number': invitation.seat_number or '',
            'barcode_number': invitation.barcode_number,
            'unique_code': str(invitation.unique_code),
        }
    }

    logger.info(f"api_check_in success for invitation={invitation.id} user={request.user.username} checked_in={invitation.checked_in}")

    return JsonResponse(payload)


@require_POST
def recaptcha_enterprise_verify(request):
    """Verify a reCAPTCHA Enterprise token posted from the client.

    Expects JSON body: { "token": "...", "action": "<ACTION>" }
    Returns JSON: { success, valid, riskScore, action_mismatch, tokenProperties }
    """
    if not RECAPTCHA_ENTERPRISE_AVAILABLE:
        return JsonResponse({'success': False, 'message': 'recaptcha enterprise client not available'}, status=500)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)

    token = data.get('token')
    action = data.get('action', '')
    if not token:
        return JsonResponse({'success': False, 'message': 'Missing token'}, status=400)

    # Load credentials if a service account path is provided via env
    credentials = None
    sa_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if sa_path and os.path.exists(sa_path):
        try:
            credentials = service_account.Credentials.from_service_account_file(sa_path)
        except Exception:
            logger.exception('Failed to load service account credentials from %s', sa_path)

    client = recaptchaenterprise_v1.RecaptchaEnterpriseServiceClient(credentials=credentials)

    project_id = os.environ.get('RECAPTCHA_ENTERPRISE_PROJECT')
    site_key = os.environ.get('RECAPTCHA_ENTERPRISE_SITE_KEY')
    if not project_id or not site_key:
        return JsonResponse({'success': False, 'message': 'Server not configured for reCAPTCHA Enterprise'}, status=500)

    event = recaptchaenterprise_v1.Event()
    event.site_key = site_key
    event.token = token

    assessment = recaptchaenterprise_v1.Assessment()
    assessment.event = event

    parent = f"projects/{project_id}"
    request_proto = recaptchaenterprise_v1.CreateAssessmentRequest()
    request_proto.parent = parent
    request_proto.assessment = assessment

    try:
        resp = client.create_assessment(request=request_proto)
    except Exception as e:
        logger.exception('reCAPTCHA Enterprise create_assessment failed')
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # Token validity
    if not getattr(resp.token_properties, 'valid', False):
        return JsonResponse({'success': False, 'valid': False, 'invalid_reason': getattr(resp.token_properties, 'invalid_reason', None)}, status=400)

    action_mismatch = False
    if action and getattr(resp.token_properties, 'action', None) != action:
        action_mismatch = True

    score = None
    if resp.risk_analysis and getattr(resp.risk_analysis, 'score', None) is not None:
        score = resp.risk_analysis.score

    return JsonResponse({
        'success': True,
        'valid': True,
        'riskScore': score,
        'action_mismatch': action_mismatch,
        'tokenProperties': {
            'valid': resp.token_properties.valid,
            'action': getattr(resp.token_properties, 'action', None),
        }
    })

@login_required
def check_in_guest(request, code):
    """Check in a guest using their invitation code or barcode"""
    invitation = get_object_or_404(Invitation, unique_code=code)
    
    if request.method == 'POST':
        success = invitation.check_in_guest()
        if success:
            messages.success(request, f'{invitation.guest.full_name} has been checked in successfully!')
        else:
            messages.info(request, f'{invitation.guest.full_name} was already checked in at {invitation.check_in_time}.')
        
        return redirect('guest_info', code=code)
    
    return render(request, 'guests/check_in_confirm.html', {
        'invitation': invitation
    })


@require_POST
@login_required
def start_checkin_session(request):
    """Start a check-in session for an event. Uses cache to publish active session state shared between ushers."""
    if not (request.user.is_staff or request.user.is_superuser):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST
    event_id = data.get('event_id')
    join_existing = data.get('join', False)  # Allow joining existing session
    if not event_id:
        return JsonResponse({'status': 'error', 'message': 'event_id required'}, status=400)
    try:
        ev = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Event not found'}, status=404)

    session_key = f'guests:checkin_session:{event_id}'
    # Check if session already exists
    existing_session = cache.get(session_key)
    active_db = CheckInSession.objects.filter(event=ev, ended_at__isnull=True).first()
    
    # If joining an existing session, return the active session details
    if join_existing and (existing_session or active_db):
        if existing_session:
            return JsonResponse({
                'status': 'ok', 
                'session': existing_session,
                'joined': True,
                'message': f'{request.user.username} joined the session'
            })
        # If cache missing but DB has active session, reconstruct from DB
        if active_db:
            session_data = {
                'event_id': int(event_id),
                'event_name': ev.name,
                'started_by': active_db.started_by.username if active_db.started_by else 'Unknown',
                'started_at': active_db.started_at.isoformat(),
                'session_id': active_db.id
            }
            # Restore to cache
            cache.set(session_key, session_data, timeout=getattr(settings, 'CHECKIN_SESSION_TIMEOUT', 60 * 60 * 8))
            return JsonResponse({
                'status': 'ok',
                'session': session_data,
                'joined': True,
                'message': f'{request.user.username} joined the session'
            })
    
    # Prevent starting a second active session for the same event (unless joining)
    if not join_existing and (existing_session or active_db):
        return JsonResponse({
            'status': 'error', 
            'message': 'A session is already active for this event. Use join=true to join it.',
            'can_join': True
        }, status=409)

    session_data = {
        'event_id': int(event_id),
        'event_name': ev.name,
        'started_by': request.user.username,
        'started_at': timezone.now().isoformat()
    }
    # Store in cache (shared cache recommended) with configured timeout
    cache.set(session_key, session_data, timeout=getattr(settings, 'CHECKIN_SESSION_TIMEOUT', 60 * 60 * 8))

    # Persist audit record
    try:
        sess = CheckInSession.objects.create(event=ev, started_by=request.user)
        session_data['session_id'] = sess.id
    except Exception:
        logger.exception('Failed to create CheckInSession record')

    return JsonResponse({'status': 'ok', 'session': session_data})


@require_POST
@login_required
def end_checkin_session(request):
    if not (request.user.is_staff or request.user.is_superuser):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST
    event_id = data.get('event_id')
    if not event_id:
        return JsonResponse({'status': 'error', 'message': 'event_id required'}, status=400)
    session_key = f'guests:checkin_session:{event_id}'
    # Delete cache key
    cache.delete(session_key)

    # Update DB audit record if present (mark ended)
    try:
        active = CheckInSession.objects.filter(event_id=event_id, ended_at__isnull=True).order_by('-started_at').first()
        if active:
            active.ended_at = timezone.now()
            active.ended_by = request.user
            active.save(update_fields=['ended_at', 'ended_by'])
    except Exception:
        logger.exception('Failed to mark CheckInSession ended in DB')

    return JsonResponse({'status': 'ok'})


@login_required
def active_checkin_sessions(request):
    """Return active check-in sessions (best-effort). Since cache doesn't list keys portably, accept event_id param or return empty list."""
    event_id = request.GET.get('event_id')
    if event_id:
        session = cache.get(f'guests:checkin_session:{event_id}')
        if not session:
            return JsonResponse({'status': 'ok', 'active': False, 'session': None})
        return JsonResponse({'status': 'ok', 'active': True, 'session': session})
    # Without event_id we can't reliably enumerate cache keys in portable way; client should request per-event
    return JsonResponse({'status': 'ok', 'active': False, 'session': None})

@login_required
def guest_info(request, code):
    """Display detailed guest information from scanned barcode/QR code"""
    invitation = get_object_or_404(Invitation.objects.select_related('guest', 'event'), unique_code=code)
    
    # Get RSVP if exists
    rsvp = None
    if hasattr(invitation, 'rsvp'):
        rsvp = invitation.rsvp
    
    return render(request, 'guests/guest_info.html', {
        'invitation': invitation,
        'rsvp': rsvp
    })

@login_required
def seating_chart(request, event_id):
    """Display seating chart for an event"""
    event = get_object_or_404(Event, id=event_id, created_by=request.user)
    
    # Get all invitations with assigned seating
    seated_invitations = event.invitations.filter(
        Q(table_number__isnull=False) | Q(seat_number__isnull=False)
    ).select_related('guest', 'rsvp').order_by('table_number', 'seat_number')
    
    # Group by table
    tables = {}
    for invitation in seated_invitations:
        table = invitation.table_number or 'Unassigned'
        if table not in tables:
            tables[table] = []
        tables[table].append(invitation)
    
    return render(request, 'guests/seating_chart.html', {
        'event': event,
        'tables': tables,
        'seated_count': seated_invitations.count(),
        'total_invitations': event.invitations.count()
    })

@login_required
@ratelimit(key='user', rate='20/h', method='POST', block=True)
def resend_invitation(request, invitation_id):
    """Resend a single invitation email"""
    invitation = get_object_or_404(Invitation, id=invitation_id)
    
    # Check if user has permission
    if invitation.event.created_by != request.user:
        messages.error(request, 'You do not have permission to resend this invitation.')
        return redirect('organizer_dashboard')
    
    if request.method == 'POST':
        logger.info(f"User {request.user.username} resending invitation {invitation.id}")
        send_invitation_email(invitation, request)
        invitation.email_sent = True
        invitation.email_sent_at = timezone.now()
        invitation.status = 'sent'
        invitation.save(update_fields=['email_sent', 'email_sent_at', 'status'])
        
        messages.success(request, f'Invitation resent to {invitation.guest.full_name}!')
        
        # Redirect back to event dashboard or referrer
        next_url = request.POST.get('next', None)
        if next_url:
            return redirect(next_url)
        return redirect('event_dashboard', event_id=invitation.event.id)
    
    return redirect('event_dashboard', event_id=invitation.event.id)

@login_required
def bulk_resend_invitations(request, event_id):
    """Bulk resend invitation emails to all guests for an event"""
    event = get_object_or_404(Event, id=event_id, created_by=request.user)
    
    if request.method == 'POST':
        # Get all invitations for the event
        invitations = event.invitations.all()
        
        success_count = 0
        error_count = 0
        
        for invitation in invitations:
            try:
                send_invitation_email(invitation, request)
                invitation.email_sent = True
                invitation.email_sent_at = timezone.now()
                invitation.status = 'sent'
                invitation.save(update_fields=['email_sent', 'email_sent_at', 'status'])
                success_count += 1
                logger.info(f"Bulk resend: Invitation {invitation.id} sent to {invitation.guest.email}")
            except Exception as e:
                error_count += 1
                logger.error(f"Bulk resend: Failed to send invitation {invitation.id} to {invitation.guest.email}: {str(e)}")
        
        if success_count > 0:
            messages.success(request, f'Successfully sent {success_count} invitation email(s)!')
        if error_count > 0:
            messages.warning(request, f'Failed to send {error_count} invitation email(s). Please check the logs.')
        
        logger.info(f"User {request.user.username} bulk resent {success_count} invitations for event {event.id}")
        
        return redirect('event_dashboard', event_id=event.id)
    
    return redirect('event_dashboard', event_id=event.id)

# Guest Portal Views - Append to views.py

# Guest Portal Views
@login_required
def guest_portal(request):
    """Guest portal dashboard showing their invitations and RSVPs"""
    try:
        guest = request.user.guest_profile
    except Guest.DoesNotExist:
        messages.error(request, 'No guest profile found for your account.')
        return redirect('home')
    
    # Update last login
    guest.last_login = timezone.now()
    guest.save(update_fields=['last_login'])
    
    # Get all invitations for this guest
    invitations = Invitation.objects.filter(guest=guest).select_related('event', 'rsvp').order_by('-event__date')
    
    # Separate upcoming and past
    upcoming_invitations = invitations.filter(event__date__gte=timezone.now())
    past_invitations = invitations.filter(event__date__lt=timezone.now())
    
    # Count RSVPs
    pending_rsvps = invitations.filter(rsvp__isnull=True).count()
    confirmed = invitations.filter(rsvp__response='yes').count()
    declined = invitations.filter(rsvp__response='no').count()
    
    context = {
        'guest': guest,
        'upcoming_invitations': upcoming_invitations,
        'past_invitations': past_invitations,
        'pending_rsvps': pending_rsvps,
        'confirmed': confirmed,
        'declined': declined,
    }
    
    return render(request, 'guests/guest_portal.html', context)

@login_required
def guest_profile_edit(request):
    """Allow guests to edit their profile"""
    try:
        guest = request.user.guest_profile
    except Guest.DoesNotExist:
        messages.error(request, 'No guest profile found.')
        return redirect('home')
    
    if request.method == 'POST':
        form = GuestProfileForm(request.POST, instance=guest)
        if form.is_valid():
            guest = form.save()
            # Also update user model
            request.user.first_name = guest.first_name
            request.user.last_name = guest.last_name
            request.user.email = guest.email
            request.user.save()
            
            messages.success(request, '✅ Your profile has been updated successfully!')
            return redirect('guest_portal')
    else:
        form = GuestProfileForm(instance=guest)
    
    return render(request, 'guests/guest_profile_edit.html', {
        'form': form,
        'guest': guest
    })

@login_required
def user_profile_edit(request):
    """Allow organizers/admins to edit their profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Your profile has been updated successfully!')
            return redirect('organizer_dashboard')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'guests/user_profile_edit.html', {
        'form': form,
    })

def guest_register(request):
    """Allow guests to self-register for an account"""
    if request.user.is_authenticated:
        return redirect('guest_portal')
    
    if request.method == 'POST':
        form = GuestRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in
            login(request, user)
            messages.success(request, f'Welcome {user.first_name}! Your account has been created successfully.')
            return redirect('guest_portal')
    else:
        form = GuestRegistrationForm()
    
    return render(request, 'guests/guest_register.html', {
        'form': form
    })

@login_required
def guest_rsvp_manage(request, invitation_id):
    """Allow guests to view/edit their RSVP from the portal"""
    invitation = get_object_or_404(Invitation, id=invitation_id)
    
    # Check if this guest owns this invitation
    try:
        guest = request.user.guest_profile
        if invitation.guest != guest:
            messages.error(request, 'You do not have permission to manage this invitation.')
            return redirect('guest_portal')
    except Guest.DoesNotExist:
        messages.error(request, 'No guest profile found.')
        return redirect('home')
    
    # Use existing RSVP form and logic
    try:
        rsvp = invitation.rsvp
    except RSVP.DoesNotExist:
        rsvp = None
    
    if request.method == 'POST':
        form = RSVPForm(request.POST, instance=rsvp)
        if form.is_valid():
            rsvp = form.save(commit=False)
            rsvp.invitation = invitation
            rsvp.save()
            
            # Update invitation status
            invitation.status = 'responded'
            invitation.save(update_fields=['status'])
            
            messages.success(request, f'✅ Your RSVP for {invitation.event.name} has been updated!')
            return redirect('guest_portal')
    else:
        form = RSVPForm(instance=rsvp)
    
    return render(request, 'guests/guest_rsvp_manage.html', {
        'form': form,
        'invitation': invitation,
        'event': invitation.event,
    })

@login_required
def guest_invitation_detail(request, invitation_id):
    """Show detailed invitation information to guest"""
    invitation = get_object_or_404(Invitation, id=invitation_id)
    
    # Check if this guest owns this invitation
    try:
        guest = request.user.guest_profile
        if invitation.guest != guest:
            messages.error(request, 'You do not have permission to view this invitation.')
            return redirect('guest_portal')
    except Guest.DoesNotExist:
        messages.error(request, 'No guest profile found.')
        return redirect('home')
    
    # Mark as opened if not already
    if not invitation.opened_at:
        invitation.opened_at = timezone.now()
        invitation.status = 'opened'
        invitation.save(update_fields=['opened_at', 'status'])
    
    context = {
        'invitation': invitation,
        'event': invitation.event,
    }
    
    return render(request, 'guests/guest_invitation_detail.html', context)


@login_required
def live_checkin_dashboard(request):
    """Live check-in dashboard with real-time updates"""
    return render(request, 'guests/live_checkin_dashboard.html')


@login_required
def live_checkin_data_api(request):
    """API endpoint for live check-in dashboard data"""
    from datetime import timedelta
    from django.db.models import Count
    from django.db.models.functions import TruncMinute
    
    # Get all checked-in invitations from today
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    checked_in_invitations = Invitation.objects.filter(
        checked_in=True,
        check_in_time__gte=today_start
    ).select_related('guest', 'event')
    
    # Calculate stats
    total_checked_in = checked_in_invitations.count()
    total_expected = Invitation.objects.filter(
        event__date__gte=today_start,
        event__date__lte=timezone.now() + timedelta(days=1)
    ).count()
    
    # Calculate arrival rate (last 5 minutes)
    five_minutes_ago = timezone.now() - timedelta(minutes=5)
    arrival_rate = checked_in_invitations.filter(check_in_time__gte=five_minutes_ago).count()
    
    # Calculate percentage
    percentage_checked_in = round((total_checked_in / total_expected * 100) if total_expected > 0 else 0, 1)
    
    # Timeline data (last 60 minutes, grouped by 5-minute intervals)
    sixty_minutes_ago = timezone.now() - timedelta(minutes=60)
    timeline_data = []
    timeline_labels = []
    
    for i in range(12):  # 12 intervals of 5 minutes
        interval_start = sixty_minutes_ago + timedelta(minutes=i*5)
        interval_end = interval_start + timedelta(minutes=5)
        count = checked_in_invitations.filter(
            check_in_time__gte=interval_start,
            check_in_time__lt=interval_end
        ).count()
        timeline_data.append(count)
        timeline_labels.append(interval_start.strftime('%H:%M'))
    
    # Recent check-ins (last 10)
    recent_checkins = []
    for invitation in checked_in_invitations.order_by('-check_in_time')[:10]:
        recent_checkins.append({
            'time': invitation.check_in_time.strftime('%H:%M:%S') if invitation.check_in_time else '',
            'guest_name': invitation.guest.full_name,
            'rank': invitation.guest.rank or '',
            'event_name': invitation.event.name,
            'table_number': invitation.table_number or ''
        })
    
    return JsonResponse({
        'total_checked_in': total_checked_in,
        'total_expected': total_expected,
        'arrival_rate': arrival_rate,
        'percentage_checked_in': percentage_checked_in,
        'timeline_labels': timeline_labels,
        'timeline_data': timeline_data,
        'recent_checkins': recent_checkins
    })

