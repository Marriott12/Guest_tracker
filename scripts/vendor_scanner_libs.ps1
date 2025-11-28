# PowerShell script to vendor scanner libraries (quagga and jsQR)
# Downloads minified builds into `guests/static/guests/js/`
# Usage: run from repository root in PowerShell (with virtualenv activated not required)

$dest = Join-Path -Path (Resolve-Path ".") -ChildPath "guests\static\guests\js"
if (-not (Test-Path $dest)) {
    New-Item -ItemType Directory -Path $dest -Force | Out-Null
}

$files = @(
    @{url = 'https://cdn.jsdelivr.net/npm/quagga@0.12.1/dist/quagga.min.js'; name = 'quagga.min.js'},
    @{url = 'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js'; name = 'jsqr.min.js'}
)

foreach ($f in $files) {
    $out = Join-Path $dest $($f.name)
    Write-Host "Downloading $($f.url) -> $out"
    try {
        Invoke-WebRequest -Uri $f.url -OutFile $out -UseBasicParsing -ErrorAction Stop
        Write-Host "Saved $out"
    } catch {
        Write-Warning "Failed to download $($f.url): $_"
    }
}

Write-Host "Done. Run `python manage.py collectstatic --noinput` to include in staticfiles."