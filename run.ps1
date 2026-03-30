$ErrorActionPreference = "Stop"

function Get-FreePort {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    $listener.Start()
    $port = ($listener.LocalEndpoint).Port
    $listener.Stop()
    return $port
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppsDir = Join-Path $ScriptDir "apps"
$TrafficAiDir = Join-Path $AppsDir "traffic-ai"
$LegacyDir = Join-Path $AppsDir "legacy-sumo"
$FrontendDir = Join-Path $TrafficAiDir "frontend"
$LogsDir = Join-Path $ScriptDir "logs"

if (-not (Test-Path $LogsDir)) {
    New-Item -Path $LogsDir -ItemType Directory | Out-Null
}

$trafficPort = Get-FreePort
$legacyPort = Get-FreePort
while ($legacyPort -eq $trafficPort) {
    $legacyPort = Get-FreePort
}

Write-Host ""
Write-Host "Using random ports:"
Write-Host "  Traffic AI backend : $trafficPort"
Write-Host "  Legacy backend     : $legacyPort"
Write-Host ""

$envFile = Join-Path $FrontendDir ".env"
@"
VITE_API_BASE_URL=http://localhost:$trafficPort
VITE_LEGACY_API_BASE_URL=http://localhost:$legacyPort
"@ | Set-Content -Path $envFile -Encoding UTF8

Write-Host "Wrote Vite env: $envFile"

function Wait-Url([string]$url, [int]$timeoutSeconds = 90) {
    $deadline = (Get-Date).AddSeconds($timeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2 | Out-Null
            return $true
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

Write-Host "Starting Traffic AI backend..."
$trafficLog = Join-Path $LogsDir ".traffic_ai_backend.log"
$trafficProc = Start-Process -FilePath "python" `
    -ArgumentList "-m uvicorn backend.main:app --host 0.0.0.0 --port $trafficPort" `
    -WorkingDirectory $TrafficAiDir `
    -RedirectStandardOutput $trafficLog `
    -RedirectStandardError $trafficLog `
    -PassThru

Write-Host "Starting legacy backend..."
$legacyLog = Join-Path $LogsDir ".legacy_backend.log"
$legacyProc = Start-Process -FilePath "python" `
    -ArgumentList "-m uvicorn backend.main:app --host 0.0.0.0 --port $legacyPort" `
    -WorkingDirectory $LegacyDir `
    -RedirectStandardOutput $legacyLog `
    -RedirectStandardError $legacyLog `
    -PassThru

try {
    Write-Host "Waiting for backends..."
    if (-not (Wait-Url "http://localhost:$trafficPort/api/v1/health")) {
        throw "Timed out waiting for Traffic AI backend."
    }
    if (-not (Wait-Url "http://localhost:$legacyPort/")) {
        throw "Timed out waiting for Legacy backend."
    }

    Write-Host ""
    Write-Host "Starting React frontend..."
    Write-Host "  Open: http://localhost:5173"
    Write-Host ""

    Push-Location $FrontendDir
    if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
        npm install
    }
    npm run dev
    Pop-Location
}
finally {
    if ($trafficProc -and -not $trafficProc.HasExited) {
        Stop-Process -Id $trafficProc.Id -Force
    }
    if ($legacyProc -and -not $legacyProc.HasExited) {
        Stop-Process -Id $legacyProc.Id -Force
    }
}

