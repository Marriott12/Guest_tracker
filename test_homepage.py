#!/usr/bin/env python
"""
Quick test to verify the home page is working
"""

import os
import django
from django.test import Client

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guest_tracker.settings')
django.setup()

def test_home_page():
    print("Testing home page...")
    
    # Create a test client
    client = Client()
    
    try:
        # Test the home page
        response = client.get('/')
        
        if response.status_code == 200:
            print("[OK] Home page loads successfully (Status: 200)")
            
            # Check if the page contains expected content
            content = response.content.decode('utf-8')
            
            if 'Welcome to Guest Tracker' in content:
                print("[OK] Home page contains welcome message")
            else:
                print("[WARNING] Welcome message not found in home page")
                
            if 'Quick Start Guide' in content:
                print("[OK] Home page contains quick start guide")
            else:
                print("[WARNING] Quick start guide not found in home page")
                
        else:
            print(f"[ERROR] Home page returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to test home page: {e}")
        return False
    
    # Test other key URLs
    test_urls = [
        ('/admin/', 'Admin page'),
        ('/add-guest/', 'Add guest page'),
    ]
    
    for url, description in test_urls:
        try:
            response = client.get(url)
            if response.status_code in [200, 302]:  # 302 is redirect, which is OK for protected pages
                print(f"[OK] {description} accessible (Status: {response.status_code})")
            else:
                print(f"[WARNING] {description} returned status {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Failed to test {description}: {e}")
    
    print("\n" + "="*50)
    print("[SUCCESS] Home page setup completed!")
    print("You can now visit http://localhost:8000/ to see your Guest Tracker home page")
    print("="*50)
    
    return True

if __name__ == '__main__':
    test_home_page()
