# Database Restore Script
# Use this script to restore a database backup

param(
    [Parameter(Mandatory=$false)]
    [string]$BackupFile,
    [string]$BackupDir = ".\backups\database"
)

Write-Host "=== Database Restore Tool ===" -ForegroundColor Cyan

# If no backup file specified, show available backups
if (-not $BackupFile) {
    Write-Host "`nAvailable backups:" -ForegroundColor Yellow
    
    $backups = Get-ChildItem $BackupDir -Filter "db_backup_*.sqlite3" | Sort-Object LastWriteTime -Descending
    
    if ($backups.Count -eq 0) {
        Write-Host "No backups found in $BackupDir" -ForegroundColor Red
        exit 1
    }
    
    for ($i = 0; $i -lt $backups.Count; $i++) {
        $backup = $backups[$i]
        $size = [math]::Round($backup.Length / 1KB, 2)
        Write-Host "$($i + 1). $($backup.Name) - $size KB - $($backup.LastWriteTime)" -ForegroundColor White
    }
    
    $selection = Read-Host "`nEnter the number of the backup to restore (or 'q' to quit)"
    
    if ($selection -eq 'q') {
        Write-Host "Restore cancelled." -ForegroundColor Yellow
        exit 0
    }
    
    $index = [int]$selection - 1
    if ($index -lt 0 -or $index -ge $backups.Count) {
        Write-Host "Invalid selection." -ForegroundColor Red
        exit 1
    }
    
    $BackupFile = $backups[$index].FullName
}

# Confirm restore
Write-Host "`nWARNING: This will replace your current database!" -ForegroundColor Red
Write-Host "Backup file: $BackupFile" -ForegroundColor Yellow
$confirm = Read-Host "Are you sure you want to continue? (yes/no)"

if ($confirm -ne 'yes') {
    Write-Host "Restore cancelled." -ForegroundColor Yellow
    exit 0
}

# Create a backup of current database before restoring
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$preRestoreBackup = ".\db_before_restore_$timestamp.sqlite3"

Write-Host "`nCreating safety backup of current database..." -ForegroundColor Yellow
Copy-Item ".\db.sqlite3" $preRestoreBackup -Force
Write-Host "✓ Safety backup created: $preRestoreBackup" -ForegroundColor Green

# Restore the backup
Write-Host "`nRestoring database..." -ForegroundColor Yellow
try {
    Copy-Item $BackupFile ".\db.sqlite3" -Force
    Write-Host "✓ Database restored successfully!" -ForegroundColor Green
    Write-Host "`nYou may need to restart your application." -ForegroundColor Cyan
}
catch {
    Write-Host "✗ Restore failed: $_" -ForegroundColor Red
    Write-Host "Your original database has been preserved." -ForegroundColor Yellow
    exit 1
}
