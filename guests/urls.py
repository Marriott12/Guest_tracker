from django.urls import path
from . import views
from . import analytics_views
from . import export_views

urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    
    # Login redirect (RBAC)
    path('login-redirect/', views.login_redirect, name='login_redirect'),
    
    # Organizer dashboard
    path('dashboard/', views.organizer_dashboard, name='organizer_dashboard'),
    
    # Analytics dashboard
    path('analytics/', analytics_views.analytics_dashboard, name='analytics_dashboard'),
    path('event/<int:event_id>/analytics/checkins/', analytics_views.checkin_analytics, name='checkin_analytics'),
    
    # Export URLs
    path('event/<int:event_id>/export/guests/csv/', export_views.export_guest_list_csv, name='export_guest_list_csv'),
    path('event/<int:event_id>/export/guests/excel/', export_views.export_guest_list_excel, name='export_guest_list_excel'),
    path('event/<int:event_id>/export/checkin/csv/', export_views.export_checkin_log_csv, name='export_checkin_log_csv'),
    path('event/<int:event_id>/export/rsvp/csv/', export_views.export_rsvp_report_csv, name='export_rsvp_report_csv'),
    path('event/<int:event_id>/export/seating/pdf/', export_views.export_seating_chart_pdf, name='export_seating_chart_pdf'),
    
    # RSVP URLs
    path('rsvp/<uuid:code>/', views.rsvp_response, name='rsvp'),
    path('qr/<uuid:code>/', views.qr_code_view, name='qr_code'),
    
    # Event management URLs
    path('event/<int:event_id>/dashboard/', views.event_dashboard, name='event_dashboard'),
    path('event/<int:event_id>/send-invitations/', views.send_invitations, name='send_invitations'),
    path('event/<int:event_id>/add-guest/', views.add_guest, name='add_guest_to_event'),
    path('event/<int:event_id>/seating-chart/', views.seating_chart, name='seating_chart'),
    
    # Invitation management
    path('invitation/<int:invitation_id>/resend/', views.resend_invitation, name='resend_invitation'),
    path('event/<int:event_id>/bulk-resend-invitations/', views.bulk_resend_invitations, name='bulk_resend_invitations'),
    
    # Guest management URLs
    path('add-guest/', views.add_guest, name='add_guest'),

    # Past events page
    path('past-events/', views.past_events, name='past_events'),
    
    # Barcode scanning and guest check-in
    path('scan/', views.scan_barcode, name='scan_barcode'),
    path('scanner/', views.scanner_ui, name='scanner_ui'),
    path('mobile-scanner/', views.mobile_scanner, name='mobile_scanner'),
    path('api/check-in/', views.api_check_in, name='api_check_in'),
    path('api/recent-checkins/', views.api_recent_checkins, name='api_recent_checkins'),
    path('api/check-in-session/start/', views.start_checkin_session, name='start_checkin_session'),
    path('api/check-in-session/end/', views.end_checkin_session, name='end_checkin_session'),
    path('api/check-in-session/active/', views.active_checkin_sessions, name='active_checkin_sessions'),
    path('recaptcha/verify/', views.recaptcha_enterprise_verify, name='recaptcha_enterprise_verify'),
    path('event/<int:event_id>/checkin-summary-json/', views.checkin_summary_json, name='checkin_summary_json'),
    path('guest/<uuid:code>/', views.guest_info, name='guest_info'),
    path('check-in/<uuid:code>/', views.check_in_guest, name='check_in_guest'),
    
    # Guest Portal URLs
    path('portal/', views.guest_portal, name='guest_portal'),
    path('portal/profile/', views.guest_profile_edit, name='guest_profile_edit'),
    path('portal/invitation/<int:invitation_id>/', views.guest_invitation_detail, name='guest_invitation_detail'),
    path('portal/rsvp/<int:invitation_id>/', views.guest_rsvp_manage, name='guest_rsvp_manage'),
    path('register/', views.guest_register, name='guest_register'),
    
    # User Profile URLs
    path('profile/edit/', views.user_profile_edit, name='user_profile_edit'),
    
    # Export URLs
    path('event/<int:event_id>/export/guests/csv/', export_views.export_guest_list_csv, name='export_guest_list_csv'),
    path('event/<int:event_id>/export/guests/excel/', export_views.export_guest_list_excel, name='export_guest_list_excel'),
    path('event/<int:event_id>/export/checkin/csv/', export_views.export_checkin_log_csv, name='export_checkin_log_csv'),
    path('event/<int:event_id>/export/rsvp/csv/', export_views.export_rsvp_report_csv, name='export_rsvp_report_csv'),
    path('event/<int:event_id>/export/seating/pdf/', export_views.export_seating_chart_pdf, name='export_seating_chart_pdf'),
    
    # Live Dashboard URLs
    path('live-checkin/', views.live_checkin_dashboard, name='live_checkin_dashboard'),
    path('api/live-checkin-data/', views.live_checkin_data_api, name='live_checkin_data_api'),
]
