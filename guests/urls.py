from django.urls import path
from . import views
from . import analytics_views

urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    
    # Organizer dashboard
    path('dashboard/', views.organizer_dashboard, name='organizer_dashboard'),
    
    # Analytics dashboard
    path('analytics/', analytics_views.analytics_dashboard, name='analytics_dashboard'),
    
    # RSVP URLs
    path('rsvp/<uuid:code>/', views.rsvp_response, name='rsvp'),
    path('qr/<uuid:code>/', views.qr_code_view, name='qr_code'),
    
    # Event management URLs
    path('event/<int:event_id>/dashboard/', views.event_dashboard, name='event_dashboard'),
    path('event/<int:event_id>/send-invitations/', views.send_invitations, name='send_invitations'),
    path('event/<int:event_id>/add-guest/', views.add_guest, name='add_guest_to_event'),
    
    # Guest management URLs
    path('add-guest/', views.add_guest, name='add_guest'),
]
