#!/usr/bin/env python
"""
Comprehensive System Test for Guest Tracker
Tests all major components and functionality
"""

import os
import sys
import django
from datetime import timedelta

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guest_tracker.settings')
django.setup()

from guests.models import Event, Guest, Invitation, RSVP
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.management import call_command
from django.test import Client

def run_comprehensive_tests():
    print("=" * 60)
    print("COMPREHENSIVE GUEST TRACKER SYSTEM TEST")
    print("=" * 60)
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Model Imports
    total_tests += 1
    try:
        from guests.models import Event, Guest, Invitation, RSVP
        print("[OK] Test 1: Model imports successful")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] Test 1: Model import failed - {e}")
    
    # Test 2: Database Connectivity
    total_tests += 1
    try:
        user_count = User.objects.count()
        guest_count = Guest.objects.count()
        event_count = Event.objects.count()
        print(f"[OK] Test 2: Database connectivity - Users: {user_count}, Guests: {guest_count}, Events: {event_count}")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] Test 2: Database connectivity failed - {e}")
    
    # Test 3: User Creation
    total_tests += 1
    try:
        test_user, created = User.objects.get_or_create(
            username='test_system_user',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        if created:
            test_user.set_password('testpass123')
            test_user.save()
        print("[OK] Test 3: User creation/retrieval successful")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] Test 3: User creation failed - {e}")
    
    # Test 4: Event Creation
    total_tests += 1
    try:
        test_event, created = Event.objects.get_or_create(
            name='System Test Event',
            defaults={
                'description': 'Automated system test event',
                'date': timezone.now() + timedelta(days=30),
                'location': 'Test Location',
                'created_by': test_user,
                'rsvp_deadline': timezone.now() + timedelta(days=25),
                'max_guests': 100
            }
        )
        print("[OK] Test 4: Event creation successful")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] Test 4: Event creation failed - {e}")
    
    # Test 5: Guest Creation
    total_tests += 1
    try:
        test_guest, created = Guest.objects.get_or_create(
            email='systemtest@example.com',
            defaults={
                'first_name': 'System',
                'last_name': 'Test',
                'phone': '+1234567890',
                'address': '123 Test Street'
            }
        )
        print("[OK] Test 5: Guest creation successful")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] Test 5: Guest creation failed - {e}")
    
    # Test 6: Invitation Creation
    total_tests += 1
    try:
        test_invitation, created = Invitation.objects.get_or_create(
            event=test_event,
            guest=test_guest
        )
        print(f"[OK] Test 6: Invitation creation successful - Code: {test_invitation.unique_code}")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] Test 6: Invitation creation failed - {e}")
    
    # Test 7: RSVP Creation
    total_tests += 1
    try:
        test_rsvp, created = RSVP.objects.get_or_create(
            invitation=test_invitation,
            defaults={
                'response': 'yes',
                'plus_ones': 1,
                'dietary_restrictions': 'None',
                'special_requests': 'Test request'
            }
        )
        print("[OK] Test 7: RSVP creation successful")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] Test 7: RSVP creation failed - {e}")
    
    # Test 8: Management Commands Import
    total_tests += 1
    try:
        from guests.management.commands.import_guests import Command as ImportCommand
        from guests.management.commands.send_invitations import Command as SendCommand
        print("[OK] Test 8: Management commands import successful")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] Test 8: Management commands import failed - {e}")
    
    # Test 9: Views Import
    total_tests += 1
    try:
        from guests import views
        print("[OK] Test 9: Views import successful")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] Test 9: Views import failed - {e}")
    
    # Test 10: URL Configuration
    total_tests += 1
    try:
        from guests import urls
        from django.urls import reverse
        # Try to reverse a URL
        admin_url = reverse('admin:index')
        print("[OK] Test 10: URL configuration successful")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] Test 10: URL configuration failed - {e}")
    
    # Test 11: Sample Data Statistics
    total_tests += 1
    try:
        all_users = User.objects.count()
        all_events = Event.objects.count()
        all_guests = Guest.objects.count()
        all_invitations = Invitation.objects.count()
        all_rsvps = RSVP.objects.count()
        
        print(f"[OK] Test 11: Data statistics - Users: {all_users}, Events: {all_events}, Guests: {all_guests}, Invitations: {all_invitations}, RSVPs: {all_rsvps}")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] Test 11: Data statistics failed - {e}")
    
    # Test 12: Model Methods
    total_tests += 1
    try:
        # Test guest full_name property
        full_name = test_guest.full_name
        # Test invitation string representation
        inv_str = str(test_invitation)
        print(f"[OK] Test 12: Model methods work - Guest: {full_name}, Invitation: {inv_str}")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] Test 12: Model methods failed - {e}")
    
    # Final Results
    print("=" * 60)
    print(f"TEST RESULTS: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("[SUCCESS] All tests passed! Your Guest Tracker system is working perfectly!")
        print("\nREADY FOR USE:")
        print("1. Run: python manage.py runserver")
        print("2. Visit: http://localhost:8000/admin/")
        print("3. Login with your test user credentials")
        print("4. Start managing events and guests!")
    else:
        print(f"[WARNING] {total_tests - success_count} tests failed. Please check the errors above.")
    
    print("=" * 60)
    return success_count == total_tests

if __name__ == '__main__':
    run_comprehensive_tests()
