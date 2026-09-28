<#
.SYNOPSIS
  Start the V8 dashboard on the Windows lunchbox, connected to the Pi through an SSH tunnel.

.DESCRIPTION
  1. Opens an SSH tunnel: local 127.0.0.1:8765 -> Pi 127.0.0.1:8765 (key-based login).
  2. Starts the dashboard server on http://127.0.0.1:8080 and opens the browser.
  Closing this window stops the dashboard and the tunnel. Acquisition on the Pi continues
  independently; a running campaign pauses between trials when no dashboard heartbeat arrives.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File v8\scripts\start_dashboard.ps1
  powershell -ExecutionPolicy Bypass -File v8\scripts\start_dashboard.ps1 -PiHost 192.168.0.50
  powershell -ExecutionPolicy Bypass -File v8\scripts\start_dashboard.ps1 -ReplayOnly
#>
param(
  [string]$PiHost = "on-edge-pi.local",
  [string]$PiUser = "seeker",
  [int]$PiPort = 8765,
  [int]$LocalPort = 8080,
  [switch]$ReplayOnly
)
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$tunnel = $null
if (-not $ReplayOnly) {
  $inUse = Get-NetTCPConnection -LocalPort $PiPort -State Listen -ErrorAction SilentlyContinue
  if ($inUse) {
    Write-Host "Port $PiPort is already listening on this PC (a local simulated daemon or an old tunnel?)." -ForegroundColor Yellow
    Write-Host "Stop it first, or pass -PiPort <other> after changing the daemon port." -ForegroundColor Yellow
    exit 1
  }
  Write-Host "Opening SSH tunnel to $PiUser@$PiHost (key-based login required) ..."
  $tunnel = Start-Process ssh -PassThru -WindowStyle Minimized -ArgumentList @(
    "-N", "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes", "-o", "ServerAliveInterval=5",
    "-o", "ServerAliveCountMax=3", "-L", "${PiPort}:127.0.0.1:${PiPort}", "$PiUser@$PiHost")
  Start-Sleep -Seconds 3
  if ($tunnel.HasExited) {
    Write-Host "SSH tunnel failed (exit $($tunnel.ExitCode)). Check: ssh -o BatchMode=yes $PiUser@$PiHost hostname" -ForegroundColor Red
    exit 1
  }
  $pi = "http://127.0.0.1:$PiPort"
} else {
  $pi = "none"
}
Start-Process "http://127.0.0.1:$LocalPort/"
try {
  python "$repo\v8\dashboard\server.py" --pi $pi --port $LocalPort
} finally {
  if ($tunnel -and -not $tunnel.HasExited) { Stop-Process -Id $tunnel.Id -ErrorAction SilentlyContinue }
}
