# PowerShell script to stop server, apply migrations, and restart

# Kill any running Python processes
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# Change to project directory
Set-Location "c:\wamp64\www\guest_tracker"

# Apply migrations
& "c:/wamp64/www/guest_tracker/.venv/Scripts/python.exe" manage.py migrate

# Start the server
& "c:/wamp64/www/guest_tracker/.venv/Scripts/python.exe" manage.py runserver
