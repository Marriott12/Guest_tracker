from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q
from .models import Event, Guest, Invitation, RSVP
from .forms import RSVPForm, GuestForm

def home(request):
    """Professional landing page - shows upcoming and past events"""
    
    # Get upcoming events
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
        'user': request.user
    }
    
    return render(request, 'guests/landing.html', context)

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
def send_invitations(request, event_id):
    """Send email invitations for an event"""
    event = get_object_or_404(Event, id=event_id, created_by=request.user)
    
    if request.method == 'POST':
        invitation_ids = request.POST.getlist('invitation_ids')
        sent_count = 0
        
        for invitation_id in invitation_ids:
            try:
                invitation = Invitation.objects.get(id=invitation_id, event=event)
                if not invitation.email_sent:
                    send_invitation_email(invitation, request)
                    invitation.email_sent = True
                    invitation.save()
                    sent_count += 1
            except Invitation.DoesNotExist:
                continue
        
        messages.success(request, f'Successfully sent {sent_count} invitations!')
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
    
    send_mail(
        subject=subject,
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invitation.guest.email],
        fail_silently=False,
    )

@login_required
def add_guest(request, event_id=None):
    """Add a new guest and optionally create invitation"""
    event = None
    if event_id:
        event = get_object_or_404(Event, id=event_id, created_by=request.user)
    
    if request.method == 'POST':
        form = GuestForm(request.POST)
        if form.is_valid():
            guest = form.save()
            
            # Create invitation if event is specified
            if event:
                invitation, created = Invitation.objects.get_or_create(
                    event=event,
                    guest=guest
                )
                if created:
                    messages.success(request, f'Guest {guest.full_name} added and invited to {event.name}!')
                else:
                    messages.info(request, f'Guest {guest.full_name} was already invited to {event.name}.')
                return redirect('event_dashboard', event_id=event.id)
            else:
                messages.success(request, f'Guest {guest.full_name} added successfully!')
                return redirect('add_guest')
    else:
        form = GuestForm()
    
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
