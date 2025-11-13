# Quick Deploy Script for Windows PowerShell
# This script pushes local changes to GitHub and deploys to live server

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "GUEST TRACKER - QUICK DEPLOY TO LIVE" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Check for uncommitted changes
Write-Host "Step 1: Checking for local changes..." -ForegroundColor Yellow
$status = git status --porcelain
if ($status) {
    Write-Host "Found uncommitted changes!" -ForegroundColor Green
    git status --short
    
    $commit = Read-Host "`nCommit these changes? (Y/N)"
    if ($commit -eq 'Y' -or $commit -eq 'y') {
        $message = Read-Host "Enter commit message"
        if ([string]::IsNullOrWhiteSpace($message)) {
            $message = "Update from local system"
        }
        
        git add .
        git commit -m "$message"
        Write-Host "✅ Changes committed!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Skipping commit..." -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ No uncommitted changes found" -ForegroundColor Green
}

# Step 2: Push to GitHub
Write-Host "`nStep 2: Pushing to GitHub..." -ForegroundColor Yellow
git push origin main
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Pushed to GitHub successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to push to GitHub" -ForegroundColor Red
    exit 1
}

# Step 3: Display SSH deployment commands
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "READY TO DEPLOY TO LIVE SERVER" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Now SSH into your server and run these commands:`n" -ForegroundColor Yellow

$commands = @"
cd ~/public_html/guest_tracker && \
git pull origin main && \
source /home/envithcy/virtualenv/guest_tracker/3.11/bin/activate && \
pip install -r requirements_clean.txt && \
python manage.py migrate && \
python manage.py collectstatic --noinput && \
touch ~/public_html/guest_tracker/tmp/restart.txt && \
echo '✅ Deployment Complete!'
"@

Write-Host $commands -ForegroundColor Green

# Copy to clipboard if possible
try {
    $commands | Set-Clipboard
    Write-Host "`n✅ Commands copied to clipboard!" -ForegroundColor Cyan
    Write-Host "Just paste into your SSH terminal`n" -ForegroundColor Cyan
} catch {
    Write-Host "`nℹ️  Copy the commands above manually`n" -ForegroundColor Yellow
}

Write-Host "========================================`n" -ForegroundColor Cyan
Write-Host "SSH Connection Command:" -ForegroundColor Yellow
Write-Host "ssh envithcy@server219.web-hosting.com`n" -ForegroundColor Green

Write-Host "After deployment, verify at:" -ForegroundColor Yellow
Write-Host "https://guests.envisagezm.com`n" -ForegroundColor Green
