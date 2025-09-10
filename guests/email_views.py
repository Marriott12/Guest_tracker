from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from .models import Event, Invitation, EmailTemplate, Guest
from .forms import EmailTemplateForm, BulkEmailForm
import logging
from email.mime.image import MIMEImage
import os

logger = logging.getLogger(__name__)

@login_required
def email_templates(request):
    """Manage email templates"""
    templates = EmailTemplate.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Email template created successfully!')
            return redirect('email_templates')
    else:
        form = EmailTemplateForm()
    
    context = {
        'templates': templates,
        'form': form,
    }
    return render(request, 'guests/email_templates.html', context)

@login_required
def send_bulk_invitations(request):
    """Send invitations to multiple guests"""
    if request.method == 'POST':
        form = BulkEmailForm(request.POST)
        if form.is_valid():
            event = form.cleaned_data['event']
            template = form.cleaned_data.get('template')
            send_to = form.cleaned_data['send_to']
            
            # Get invitations based on selection
            invitations = event.invitations.all()
            
            if send_to == 'pending':
                invitations = invitations.filter(
                    Q(rsvp_status='') | Q(rsvp_status__isnull=True)
                )
            elif send_to == 'confirmed':
                invitations = invitations.filter(rsvp_status='yes')
            elif send_to == 'declined':
                invitations = invitations.filter(rsvp_status='no')
            
            success_count = 0
            error_count = 0
            
            for invitation in invitations:
                try:
                    if send_invitation_email(invitation, template, request):
                        success_count += 1
                        # Update invitation status
                        invitation.invitation_sent = True
                        invitation.sent_at = timezone.now()
                        invitation.save()
                    else:
                        error_count += 1
                except Exception as e:
                    logger.error(f"Error sending invitation to {invitation.guest.email}: {str(e)}")
                    error_count += 1
            
            if success_count > 0:
                messages.success(
                    request, 
                    f'Successfully sent {success_count} invitations!'
                )
            if error_count > 0:
                messages.warning(
                    request,
                    f'Failed to send {error_count} invitations. Check logs for details.'
                )
            
            return redirect('send_bulk_invitations')
    else:
        form = BulkEmailForm()
    
    context = {
        'form': form,
        'recent_sends': get_recent_email_activity(),
    }
    return render(request, 'guests/send_bulk_invitations.html', context)

def send_invitation_email(invitation, template=None, request=None):
    """Send an invitation email with QR code attachment"""
    try:
        # Generate QR code if not exists
        if not invitation.qr_code:
            invitation.generate_qr_code()
        
        # Build URLs
        rsvp_url = reverse('rsvp', kwargs={'code': invitation.code})
        qr_url = reverse('qr_code', kwargs={'code': invitation.code})
        
        if request:
            rsvp_url = request.build_absolute_uri(rsvp_url)
            qr_url = request.build_absolute_uri(qr_url)
        else:
            # Fallback for when request is not available
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')
            rsvp_url = base_url + rsvp_url
            qr_url = base_url + qr_url
        
        # Prepare email context
        context = {
            'invitation': invitation,
            'event': invitation.event,
            'guest': invitation.guest,
            'rsvp_url': rsvp_url,
            'qr_url': qr_url,
            'current_year': timezone.now().year,
        }
        
        # Use custom template or default
        if template:
            html_content = render_to_string(
                'guests/custom_email_template.html',
                {**context, 'template': template}
            )
            text_content = template.content
            subject = template.subject
        else:
            html_content = render_to_string(
                'guests/invitation_email_enhanced.html',
                context
            )
            text_content = render_to_string(
                'guests/invitation_email.txt',
                context
            )
            subject = f"Invitation: {invitation.event.name}"
        
        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[invitation.guest.email],
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Attach QR code if exists
        if invitation.qr_code and os.path.exists(invitation.qr_code.path):
            with open(invitation.qr_code.path, 'rb') as qr_file:
                qr_image = MIMEImage(qr_file.read())
                qr_image.add_header('Content-ID', '<qr_code>')
                qr_image.add_header('Content-Disposition', 'inline', filename='qr_code.png')
                email.attach(qr_image)
        
        # Send email
        email.send()
        
        logger.info(f"Invitation sent successfully to {invitation.guest.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send invitation to {invitation.guest.email}: {str(e)}")
        return False

@require_POST
@login_required
def send_single_invitation(request, invitation_id):
    """Send a single invitation via AJAX"""
    invitation = get_object_or_404(Invitation, id=invitation_id)
    
    success = send_invitation_email(invitation, None, request)
    
    if success:
        invitation.invitation_sent = True
        invitation.sent_at = timezone.now()
        invitation.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Invitation sent to {invitation.guest.name}'
        })
    else:
        return JsonResponse({
            'success': False,
            'message': f'Failed to send invitation to {invitation.guest.name}'
        })

@require_POST
@login_required
def send_reminder_email(request, invitation_id):
    """Send a reminder email for pending RSVPs"""
    invitation = get_object_or_404(Invitation, id=invitation_id)
    
    if invitation.rsvp_status in ['yes', 'no']:
        return JsonResponse({
            'success': False,
            'message': 'Guest has already responded'
        })
    
    # Use reminder template context
    context = {
        'invitation': invitation,
        'event': invitation.event,
        'guest': invitation.guest,
        'is_reminder': True,
        'rsvp_url': request.build_absolute_uri(
            reverse('rsvp', kwargs={'code': invitation.code})
        ),
    }
    
    try:
        subject = f"Reminder: RSVP for {invitation.event.name}"
        html_content = render_to_string('guests/reminder_email.html', context)
        text_content = render_to_string('guests/reminder_email.txt', context)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[invitation.guest.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        # Update reminder sent timestamp
        invitation.last_reminder_sent = timezone.now()
        invitation.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Reminder sent to {invitation.guest.name}'
        })
        
    except Exception as e:
        logger.error(f"Failed to send reminder to {invitation.guest.email}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to send reminder to {invitation.guest.name}'
        })

def get_recent_email_activity():
    """Get recent email sending activity"""
    return Invitation.objects.filter(
        sent_at__isnull=False
    ).select_related(
        'event', 'guest'
    ).order_by('-sent_at')[:10]

@login_required
def email_analytics(request):
    """Email performance analytics"""
    from django.db.models import Count, Avg
    from datetime import datetime, timedelta
    
    # Get email statistics
    total_sent = Invitation.objects.filter(invitation_sent=True).count()
    total_delivered = Invitation.objects.filter(
        invitation_sent=True, 
        rsvp_status__isnull=False
    ).count()
    
    # Response rates by timeframe
    last_30_days = timezone.now() - timedelta(days=30)
    recent_invitations = Invitation.objects.filter(
        sent_at__gte=last_30_days
    )
    
    recent_sent = recent_invitations.count()
    recent_responses = recent_invitations.filter(
        rsvp_status__isnull=False
    ).count()
    
    response_rate = (recent_responses / recent_sent * 100) if recent_sent > 0 else 0
    
    # Top performing events
    top_events = Event.objects.annotate(
        response_rate=Count('invitations__rsvp_status') * 100.0 / Count('invitations')
    ).order_by('-response_rate')[:5]
    
    context = {
        'total_sent': total_sent,
        'total_delivered': total_delivered,
        'recent_sent': recent_sent,
        'recent_responses': recent_responses,
        'response_rate': round(response_rate, 1),
        'top_events': top_events,
        'recent_activity': get_recent_email_activity(),
    }
    
    return render(request, 'guests/email_analytics.html', context)
