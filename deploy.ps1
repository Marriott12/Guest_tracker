# Production Deployment Script for Guest Tracker
# This script handles common deployment tasks: migrations, static files, and optional cache clearing

param(
    [switch]$Migrate,
    [switch]$CollectStatic,
    [switch]$ClearCache,
    [switch]$All
)

Write-Host "=== Guest Tracker Deployment Script ===" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment if not already active
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "$PSScriptRoot\.venv\Scripts\Activate.ps1"
}

# Run migrations
if ($Migrate -or $All) {
    Write-Host "Running database migrations..." -ForegroundColor Green
    python manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Migration failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "Migrations completed successfully." -ForegroundColor Green
    Write-Host ""
}

# Collect static files
if ($CollectStatic -or $All) {
    Write-Host "Collecting static files..." -ForegroundColor Green
    python manage.py collectstatic --noinput --clear
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Static file collection failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "Static files collected successfully." -ForegroundColor Green
    Write-Host ""
}

# Clear cache
if ($ClearCache -or $All) {
    Write-Host "Clearing Django cache..." -ForegroundColor Green
    python manage.py shell -c "from django.core.cache import cache; cache.clear(); print('Cache cleared')"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Cache clear failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "Cache cleared successfully." -ForegroundColor Green
    Write-Host ""
}

# Show usage if no flags provided
if (-not ($Migrate -or $CollectStatic -or $ClearCache -or $All)) {
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\deploy.ps1 -All                  # Run all deployment tasks"
    Write-Host "  .\deploy.ps1 -Migrate              # Run database migrations only"
    Write-Host "  .\deploy.ps1 -CollectStatic        # Collect static files only"
    Write-Host "  .\deploy.ps1 -ClearCache           # Clear Django cache only"
    Write-Host "  .\deploy.ps1 -Migrate -CollectStatic  # Run multiple tasks"
    Write-Host ""
    exit 0
}

Write-Host "=== Deployment tasks completed ===" -ForegroundColor Cyan
