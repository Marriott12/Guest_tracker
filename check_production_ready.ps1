# Production Readiness Check Script
# Run this before deploying to production

param([switch]$Fix = $false)

Write-Host "=== Zambia Army Guest Tracking System - Production Readiness Check ===" -ForegroundColor Cyan
Write-Host ""

$issues = 0
$warnings = 0

# Check 1: .env file
Write-Host "Checking .env configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "[OK] .env file exists" -ForegroundColor Green
    
    $env_content = Get-Content ".env" -Raw
    if ($env_content -match 'SECRET_KEY=django-insecure') {
        Write-Host "[ERROR] Using default SECRET_KEY!" -ForegroundColor Red
        $issues++
    } else {
        Write-Host "[OK] SECRET_KEY customized" -ForegroundColor Green
    }
    
    if ($env_content -match 'DEBUG=True') {
        Write-Host "[ERROR] DEBUG is enabled!" -ForegroundColor Red
        $issues++
    } else {
        Write-Host "[OK] DEBUG disabled" -ForegroundColor Green
    }
    
    if ($env_content -match 'ALLOWED_HOSTS=localhost,127.0.0.1$') {
        Write-Host "[WARN] ALLOWED_HOSTS only has localhost" -ForegroundColor Yellow
        $warnings++
    } else {
        Write-Host "[OK] ALLOWED_HOSTS configured" -ForegroundColor Green
    }
    
    if ($env_content -match 'EMAIL_BACKEND=.*console') {
        Write-Host "[WARN] Using console email backend" -ForegroundColor Yellow
        $warnings++
    } else {
        Write-Host "[OK] Production email configured" -ForegroundColor Green
    }
} else {
    Write-Host "[ERROR] .env file not found!" -ForegroundColor Red
    $issues++
}

# Check 2: Database
Write-Host "`nChecking database..." -ForegroundColor Yellow
if (Test-Path "db.sqlite3") {
    $db_size = (Get-Item "db.sqlite3").Length / 1KB
    Write-Host "[OK] Database exists ($([math]::Round($db_size, 2)) KB)" -ForegroundColor Green
} else {
    Write-Host "[WARN] No database found" -ForegroundColor Yellow
    $warnings++
}

# Check 3: Static files
Write-Host "`nChecking static files..." -ForegroundColor Yellow
if (Test-Path "staticfiles") {
    Write-Host "[OK] staticfiles directory exists" -ForegroundColor Green
} else {
    Write-Host "[WARN] Run: python manage.py collectstatic" -ForegroundColor Yellow
    $warnings++
}

# Check 4: Logs
Write-Host "`nChecking logs..." -ForegroundColor Yellow
if (Test-Path "logs") {
    Write-Host "[OK] Logs directory exists" -ForegroundColor Green
} else {
    Write-Host "[WARN] logs directory not found" -ForegroundColor Yellow
    if ($Fix) {
        New-Item -ItemType Directory -Path "logs" -Force | Out-Null
        Write-Host "  Created logs directory" -ForegroundColor Green
    }
    $warnings++
}

# Check 5: Backups
Write-Host "`nChecking backups..." -ForegroundColor Yellow
if (Test-Path "backups\database") {
    $backup_count = (Get-ChildItem "backups\database" -Filter "db_backup_*.sqlite3" -ErrorAction SilentlyContinue).Count
    if ($backup_count -gt 0) {
        Write-Host "[OK] Found $backup_count backup(s)" -ForegroundColor Green
    } else {
        Write-Host "[WARN] No backups found" -ForegroundColor Yellow
        $warnings++
    }
} else {
    Write-Host "[WARN] backups directory not found" -ForegroundColor Yellow
    $warnings++
}

# Check 6: Virtual environment
Write-Host "`nChecking virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv\Scripts\python.exe") {
    Write-Host "[OK] Virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Virtual environment not found!" -ForegroundColor Red
    $issues++
}

# Check 7: Media
Write-Host "`nChecking media..." -ForegroundColor Yellow
if (Test-Path "media") {
    Write-Host "[OK] Media directory exists" -ForegroundColor Green
} else {
    Write-Host "[WARN] Media directory not found" -ForegroundColor Yellow
    $warnings++
}

# Summary
Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Critical Issues: $issues" -ForegroundColor $(if ($issues -gt 0) { "Red" } else { "Green" })
Write-Host "Warnings: $warnings" -ForegroundColor $(if ($warnings -gt 0) { "Yellow" } else { "Green" })

if ($issues -gt 0) {
    Write-Host "`n[ERROR] NOT READY FOR PRODUCTION!" -ForegroundColor Red
    Write-Host "Fix critical issues before deploying." -ForegroundColor Yellow
    exit 1
} elseif ($warnings -gt 0) {
    Write-Host "`n[WARN] Ready with warnings" -ForegroundColor Yellow
    Write-Host "Review warnings before production." -ForegroundColor Gray
    exit 0
} else {
    Write-Host "`n[OK] READY FOR PRODUCTION!" -ForegroundColor Green
    Write-Host "Review DEPLOYMENT.md for next steps." -ForegroundColor Cyan
    exit 0
}
