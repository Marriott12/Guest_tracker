# Database Backup Script
# Run this script regularly to backup your database

param(
    [string]$BackupDir = ".\backups\database",
    [int]$RetentionDays = 30
)

# Create backup directory if it doesn't exist
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

# Get current timestamp
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$backupFile = Join-Path $BackupDir "db_backup_$timestamp.sqlite3"

Write-Host "Creating database backup..." -ForegroundColor Green

# Copy SQLite database
try {
    Copy-Item ".\db.sqlite3" $backupFile -Force
    Write-Host "✓ Backup created: $backupFile" -ForegroundColor Green
    
    # Get backup size
    $size = (Get-Item $backupFile).Length / 1KB
    Write-Host "  Backup size: $([math]::Round($size, 2)) KB" -ForegroundColor Cyan
}
catch {
    Write-Host "✗ Backup failed: $_" -ForegroundColor Red
    exit 1
}

# Clean up old backups (older than retention days)
Write-Host "`nCleaning up old backups (keeping last $RetentionDays days)..." -ForegroundColor Yellow
$cutoffDate = (Get-Date).AddDays(-$RetentionDays)
$oldBackups = Get-ChildItem $BackupDir -Filter "db_backup_*.sqlite3" | Where-Object { $_.LastWriteTime -lt $cutoffDate }

foreach ($backup in $oldBackups) {
    Remove-Item $backup.FullName -Force
    Write-Host "  Deleted: $($backup.Name)" -ForegroundColor Gray
}

# Show backup statistics
$totalBackups = (Get-ChildItem $BackupDir -Filter "db_backup_*.sqlite3").Count
$totalSize = ((Get-ChildItem $BackupDir -Filter "db_backup_*.sqlite3" | Measure-Object -Property Length -Sum).Sum) / 1MB

Write-Host "`n=== Backup Summary ===" -ForegroundColor Cyan
Write-Host "Total backups: $totalBackups" -ForegroundColor White
Write-Host "Total size: $([math]::Round($totalSize, 2)) MB" -ForegroundColor White
Write-Host "Backup location: $BackupDir" -ForegroundColor White
Write-Host "======================" -ForegroundColor Cyan
