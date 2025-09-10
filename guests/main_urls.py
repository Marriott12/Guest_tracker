# guest_tracker/guest_tracker/urls.py
# Replace the contents of this file with:

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('guests.urls')),
]
