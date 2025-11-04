from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q, Avg
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
import plotly.graph_objs as go
import plotly.offline as opy
import pandas as pd
from .models import Event, Guest, Invitation, RSVP, EventAnalytics

@login_required
def analytics_dashboard(request):
    """Advanced analytics dashboard"""
    # Get user's events
    user_events = Event.objects.filter(created_by=request.user)
    
    # Overall statistics
    total_events = user_events.count()
    upcoming_events = user_events.filter(date__gte=timezone.now()).count()
    total_guests = Guest.objects.count()
    total_invitations = Invitation.objects.filter(event__created_by=request.user).count()
    total_rsvps = RSVP.objects.filter(invitation__event__created_by=request.user).count()
    
    # Response rate calculation
    response_rate = (total_rsvps / total_invitations * 100) if total_invitations > 0 else 0
    
    # Recent events performance
    recent_events = user_events.order_by('-date')[:10]
    
    # Create charts
    charts = {}
    
    # 1. RSVP Status Distribution Chart
    rsvp_data = RSVP.objects.filter(
        invitation__event__created_by=request.user
    ).values('response').annotate(count=Count('response'))
    
    if rsvp_data:
        labels = [item['response'].title() for item in rsvp_data]
        values = [item['count'] for item in rsvp_data]
        colors = ['#28a745', '#dc3545', '#ffc107']  # Green, Red, Yellow
        
        fig1 = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            hole=.3
        )])
        fig1.update_layout(
            title="Overall RSVP Distribution",
            font=dict(size=14),
            showlegend=True,
            height=400
        )
        charts['rsvp_distribution'] = opy.plot(fig1, auto_open=False, output_type='div')
    
    # 2. Events Timeline Chart
    if user_events.exists():
        events_by_month = user_events.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(count=Count('id')).order_by('month')
        
        if events_by_month:
            months = [item['month'].strftime('%Y-%m') for item in events_by_month]
            counts = [item['count'] for item in events_by_month]
            
            fig2 = go.Figure(data=[go.Bar(
                x=months,
                y=counts,
                marker_color='#007bff'
            )])
            fig2.update_layout(
                title="Events by Month",
                xaxis_title="Month",
                yaxis_title="Number of Events",
                height=400
            )
            charts['events_timeline'] = opy.plot(fig2, auto_open=False, output_type='div')
    
    # 3. Response Time Analysis
    response_times = RSVP.objects.filter(
        invitation__event__created_by=request.user
    ).select_related('invitation')
    
    if response_times.exists():
        times = []
        for rsvp in response_times:
            if rsvp.invitation.sent_at and rsvp.responded_at:
                delta = rsvp.responded_at - rsvp.invitation.sent_at
                times.append(delta.days)
        
        if times:
            fig3 = go.Figure(data=[go.Histogram(
                x=times,
                nbinsx=20,
                marker_color='#28a745'
            )])
            fig3.update_layout(
                title="Response Time Distribution (Days)",
                xaxis_title="Days to Respond",
                yaxis_title="Number of Responses",
                height=400
            )
            charts['response_times'] = opy.plot(fig3, auto_open=False, output_type='div')
    
    # 4. Event Performance Comparison
    if recent_events.exists():
        event_names = []
        invitation_counts = []
        response_counts = []
        
        for event in recent_events:
            invitations = event.invitations.count()
            responses = RSVP.objects.filter(invitation__event=event).count()
            
            event_names.append(event.name[:20] + '...' if len(event.name) > 20 else event.name)
            invitation_counts.append(invitations)
            response_counts.append(responses)
        
        fig4 = go.Figure(data=[
            go.Bar(name='Invitations Sent', x=event_names, y=invitation_counts, marker_color='#007bff'),
            go.Bar(name='Responses Received', x=event_names, y=response_counts, marker_color='#28a745')
        ])
        fig4.update_layout(
            title="Event Performance Comparison",
            xaxis_title="Events",
            yaxis_title="Count",
            barmode='group',
            height=400
        )
        charts['event_performance'] = opy.plot(fig4, auto_open=False, output_type='div')
    
    context = {
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'total_guests': total_guests,
        'total_invitations': total_invitations,
        'total_rsvps': total_rsvps,
        'response_rate': round(response_rate, 1),
        'recent_events': recent_events,
        'charts': charts,
    }
    
    return render(request, 'guests/analytics_dashboard.html', context)

@login_required
def event_analytics(request, event_id):
    """Detailed analytics for a specific event"""
    event = get_object_or_404(Event, id=event_id, created_by=request.user)
    
    # Get or create analytics record
    analytics, created = EventAnalytics.objects.get_or_create(event=event)
    
    # Update analytics data
    invitations = event.invitations.all()
    rsvps = RSVP.objects.filter(invitation__event=event)
    
    analytics.total_responses = rsvps.count()
    analytics.yes_responses = rsvps.filter(response='yes').count()
    analytics.no_responses = rsvps.filter(response='no').count()
    analytics.maybe_responses = rsvps.filter(response='maybe').count()
    analytics.save()
    
    # Create detailed charts for this event
    charts = {}
    
    # Daily response chart
    if rsvps.exists():
        daily_responses = rsvps.extra(
            select={'day': 'DATE(responded_at)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        if daily_responses:
            days = [item['day'] for item in daily_responses]
            counts = [item['count'] for item in daily_responses]
            
            fig = go.Figure(data=[go.Scatter(
                x=days,
                y=counts,
                mode='lines+markers',
                marker_color='#007bff'
            )])
            fig.update_layout(
                title="Daily Response Activity",
                xaxis_title="Date",
                yaxis_title="Responses",
                height=400
            )
            charts['daily_responses'] = opy.plot(fig, auto_open=False, output_type='div')
    
    context = {
        'event': event,
        'analytics': analytics,
        'invitations': invitations,
        'charts': charts,
    }
    
    return render(request, 'guests/event_analytics.html', context)
