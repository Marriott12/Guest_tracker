#!/usr/bin/env python
"""
Test script for Guest Tracking System
Run this after setting up the project to verify everything works
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guest_tracker.settings')
django.setup()

from guests.models import Event, Guest, Invitation, RSVP
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

def test_system():
    print("Testing Guest Tracking System...")
    print("=" * 50)
    
    # Test 1: Create a test user (event organizer)
    try:
        user, created = User.objects.get_or_create(
            username='testorganizer',
            defaults={
                'email': 'organizer@test.com',
                'first_name': 'Test',
                'last_name': 'Organizer'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
        print("[OK] Test user created/verified")
    except Exception as e:
        print(f"[ERROR] Error creating test user: {e}")
        return False
    
    # Test 2: Create a test event
    try:
        event, created = Event.objects.get_or_create(
            name='Test Birthday Party',
            defaults={
                'description': 'A fun test birthday party!',
                'date': timezone.now() + timedelta(days=30),
                'location': '123 Test Street, Test City',
                'created_by': user,
                'rsvp_deadline': timezone.now() + timedelta(days=25),
                'max_guests': 50
            }
        )
        print("[OK] Test event created/verified")
    except Exception as e:
        print(f"[ERROR] Error creating test event: {e}")
        return False
    
    # Test 3: Create test guests
    test_guests_data = [
        ('John', 'Doe', 'john.doe@test.com', '+1234567890'),
        ('Jane', 'Smith', 'jane.smith@test.com', '+0987654321'),
        ('Bob', 'Johnson', 'bob.johnson@test.com', '+1122334455'),
    ]
    
    guests = []
    try:
        for first_name, last_name, email, phone in test_guests_data:
            guest, created = Guest.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'address': f'123 {first_name} Street, Test City'
                }
            )
            guests.append(guest)
        print(f"[OK] {len(guests)} test guests created/verified")
    except Exception as e:
        print(f"[ERROR] Error creating test guests: {e}")
        return False
    
    # Test 4: Create invitations
    try:
        for guest in guests:
            invitation, created = Invitation.objects.get_or_create(
                event=event,
                guest=guest
            )
        invitations = Invitation.objects.filter(event=event)
        print(f"[OK] {invitations.count()} invitations created/verified")
    except Exception as e:
        print(f"[ERROR] Error creating invitations: {e}")
        return False
    
    # Test 5: Create sample RSVP responses
    try:
        responses = ['yes', 'no', 'maybe']
        for i, invitation in enumerate(invitations[:3]):
            rsvp, created = RSVP.objects.get_or_create(
                invitation=invitation,
                defaults={
                    'response': responses[i % 3],
                    'plus_ones': i,
                    'dietary_restrictions': f'Test dietary restriction {i+1}' if i == 0 else '',
                    'special_requests': f'Test special request {i+1}' if i == 1 else ''
                }
            )
        rsvps = RSVP.objects.filter(invitation__event=event)
        print(f"[OK] {rsvps.count()} RSVP responses created/verified")
    except Exception as e:
        print(f"[ERROR] Error creating RSVP responses: {e}")
        return False
    
    # Test 6: Display statistics
    try:
        total_invitations = invitations.count()
        rsvp_yes = rsvps.filter(response='yes').count()
        rsvp_no = rsvps.filter(response='no').count()
        rsvp_maybe = rsvps.filter(response='maybe').count()
        no_response = total_invitations - rsvps.count()
        
        print("\n[STATS] Event Statistics:")
        print(f"   Total Invitations: {total_invitations}")
        print(f"   Yes Responses: {rsvp_yes}")
        print(f"   No Responses: {rsvp_no}")
        print(f"   Maybe Responses: {rsvp_maybe}")
        print(f"   No Response: {no_response}")
        
        # Show RSVP URLs
        print("\n[LINKS] Sample RSVP URLs:")
        for invitation in invitations[:2]:
            print(f"   {invitation.guest.full_name}: /rsvp/{invitation.unique_code}/")
        
        print("[OK] Statistics generated successfully")
    except Exception as e:
        print(f"[ERROR] Error generating statistics: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("[SUCCESS] All tests passed! Your Guest Tracking System is working correctly!")
    print("\nNext steps:")
    print("1. Visit http://localhost:8000/admin/ to manage your events")
    print("2. Login with username: testorganizer, password: testpass123")
    print("3. Check the test event and guest data")
    print("4. Try the RSVP links shown above")
    
    return True

if __name__ == '__main__':
    test_system()
