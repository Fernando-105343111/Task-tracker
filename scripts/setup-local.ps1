$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path '.env')) {
    $bytes = New-Object byte[] 24
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    $password = -join ($bytes | ForEach-Object { $_.ToString('x2') })
    @(
        'POSTGRES_DB=tasktracker',
        'POSTGRES_USER=tasktracker',
        "POSTGRES_PASSWORD=$password",
        'APP_PORT=8080',
        'APP_BIND=127.0.0.1'
    ) | Set-Content -Encoding ASCII '.env'
    Write-Host 'Created .env with a random local database password.'
} else {
    Write-Host 'Keeping the existing .env file.'
}
New-Item -ItemType Directory -Force reports, evidence-local | Out-Null
