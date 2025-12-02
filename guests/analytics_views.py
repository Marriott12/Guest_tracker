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


@login_required
def checkin_analytics(request, event_id):
    """Enhanced check-in analytics with real-time patterns"""
    from .models import CheckInLog
    from django.db.models.functions import TruncHour, TruncDate
    
    event = get_object_or_404(Event, id=event_id)
    
    # Permission check
    if not (request.user.is_staff or request.user.is_superuser or event.created_by == request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    
    # Get check-in logs
    checkin_logs = CheckInLog.objects.filter(event=event)
    
    # Overall stats
    total_invitations = event.invitations.count()
    total_checkins = event.invitations.filter(checked_in=True).count()
    checkin_rate = (total_checkins / total_invitations * 100) if total_invitations > 0 else 0
    
    # RSVP vs Actual attendance
    rsvp_yes = RSVP.objects.filter(invitation__event=event, response='yes').count()
    actual_attendance = total_checkins
    attendance_fulfillment = (actual_attendance / rsvp_yes * 100) if rsvp_yes > 0 else 0
    
    charts = {}
    
    # 1. Hourly Check-in Pattern
    if checkin_logs.exists():
        hourly_data = checkin_logs.annotate(
            hour=TruncHour('checked_in_at')
        ).values('hour').annotate(count=Count('id')).order_by('hour')
        
        if hourly_data:
            hours = [item['hour'].strftime('%I:%M %p') for item in hourly_data]
            counts = [item['count'] for item in hourly_data]
            
            fig1 = go.Figure(data=[go.Bar(
                x=hours,
                y=counts,
                marker_color='#28a745',
                text=counts,
                textposition='auto',
            )])
            fig1.update_layout(
                title="Arrival Pattern by Hour",
                xaxis_title="Time",
                yaxis_title="Number of Check-ins",
                height=400,
                xaxis_tickangle=-45
            )
            charts['hourly_pattern'] = opy.plot(fig1, auto_open=False, output_type='div')
    
    # 2. Table Distribution
    table_data = event.invitations.filter(
        checked_in=True
    ).exclude(table_number='').values('table_number').annotate(
        count=Count('id')
    ).order_by('-count')[:20]
    
    if table_data:
        tables = [f"Table {item['table_number']}" for item in table_data]
        counts = [item['count'] for item in table_data]
        
        fig2 = go.Figure(data=[go.Bar(
            x=tables,
            y=counts,
            marker_color='#007bff'
        )])
        fig2.update_layout(
            title="Top 20 Tables by Attendance",
            xaxis_title="Table",
            yaxis_title="Guests",
            height=400
        )
        charts['table_distribution'] = opy.plot(fig2, auto_open=False, output_type='div')
    
    # 3. Check-in Status Pie Chart
    checkin_status_data = [
        {'status': 'Checked In', 'count': total_checkins},
        {'status': 'Not Checked In', 'count': total_invitations - total_checkins}
    ]
    
    fig3 = go.Figure(data=[go.Pie(
        labels=[item['status'] for item in checkin_status_data],
        values=[item['count'] for item in checkin_status_data],
        marker_colors=['#28a745', '#dc3545'],
        hole=.4
    )])
    fig3.update_layout(
        title="Check-in Status Overview",
        height=400
    )
    charts['checkin_status'] = opy.plot(fig3, auto_open=False, output_type='div')
    
    # 4. RSVP vs Attendance Comparison
    rsvp_data = {
        'Yes': RSVP.objects.filter(invitation__event=event, response='yes').count(),
        'No': RSVP.objects.filter(invitation__event=event, response='no').count(),
        'Maybe': RSVP.objects.filter(invitation__event=event, response='maybe').count(),
        'No Response': total_invitations - RSVP.objects.filter(invitation__event=event).count()
    }
    
    fig4 = go.Figure(data=[
        go.Bar(name='Expected (RSVP Yes)', x=['Expected'], y=[rsvp_yes], marker_color='#ffc107'),
        go.Bar(name='Actual (Checked In)', x=['Actual'], y=[actual_attendance], marker_color='#28a745')
    ])
    fig4.update_layout(
        title="Expected vs Actual Attendance",
        yaxis_title="Number of Guests",
        barmode='group',
        height=400
    )
    charts['rsvp_vs_actual'] = opy.plot(fig4, auto_open=False, output_type='div')
    
    # 5. Daily Cumulative Check-ins (for multi-day events or tracking)
    if checkin_logs.exists():
        daily_data = checkin_logs.annotate(
            date=TruncDate('checked_in_at')
        ).values('date').annotate(count=Count('id')).order_by('date')
        
        if len(daily_data) > 1:  # Only show if multiple days
            dates = [item['date'].strftime('%Y-%m-%d') for item in daily_data]
            counts = [item['count'] for item in daily_data]
            cumulative = []
            total = 0
            for count in counts:
                total += count
                cumulative.append(total)
            
            fig5 = go.Figure()
            fig5.add_trace(go.Scatter(
                x=dates,
                y=counts,
                name='Daily',
                mode='lines+markers',
                marker_color='#007bff'
            ))
            fig5.add_trace(go.Scatter(
                x=dates,
                y=cumulative,
                name='Cumulative',
                mode='lines+markers',
                marker_color='#28a745'
            ))
            fig5.update_layout(
                title="Check-in Trend Over Time",
                xaxis_title="Date",
                yaxis_title="Check-ins",
                height=400
            )
            charts['daily_trend'] = opy.plot(fig5, auto_open=False, output_type='div')
    
    context = {
        'event': event,
        'total_invitations': total_invitations,
        'total_checkins': total_checkins,
        'checkin_rate': round(checkin_rate, 1),
        'rsvp_yes': rsvp_yes,
        'actual_attendance': actual_attendance,
        'attendance_fulfillment': round(attendance_fulfillment, 1),
        'charts': charts,
        'checkin_logs': checkin_logs.select_related('guest', 'invitation').order_by('-checked_in_at')[:50]
    }
    
    return render(request, 'guests/checkin_analytics.html', context)
