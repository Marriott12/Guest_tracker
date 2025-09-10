#!/usr/bin/env python
"""
Test QR Code functionality after restoration
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guest_tracker.settings')
django.setup()

from guests.models import Event, Guest, Invitation
from django.contrib.auth.models import User

print('=== TESTING FULL FUNCTIONALITY ===')

# Test QR Code functionality
print('Testing QR Code generation...')
try:
    import qrcode
    from PIL import Image
    print('✅ QR Code packages available')
    
    # Create a test QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data('http://test.com')
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    print('✅ QR Code generation works')
except Exception as e:
    print(f'❌ QR Code error: {e}')

# Test Analytics functionality
print('Testing Analytics packages...')
try:
    import plotly.graph_objs as go
    import pandas as pd
    print('✅ Analytics packages available')
except Exception as e:
    print(f'❌ Analytics error: {e}')

# Test Crispy Forms
print('Testing Crispy Forms...')
try:
    import crispy_forms
    import crispy_bootstrap5
    print('✅ Crispy Forms available')
except Exception as e:
    print(f'❌ Crispy Forms error: {e}')

# Test Database Models
print('Testing Database Models...')
try:
    print(f'Users: {User.objects.count()}')
    print(f'Events: {Event.objects.count()}')
    print(f'Guests: {Guest.objects.count()}')
    print(f'Invitations: {Invitation.objects.count()}')
    print('✅ Database models working')
except Exception as e:
    print(f'❌ Database error: {e}')

print('=== FUNCTIONALITY TEST COMPLETE ===')
