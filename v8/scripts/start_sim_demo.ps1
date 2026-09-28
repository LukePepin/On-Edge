<#
.SYNOPSIS
  Run the complete V8 system on this PC with the SOFTWARE SIMULATOR (no hardware).
  Starts the simulated acquisition daemon (port 8765) in its own window and the dashboard (8080).
  Data go to data\v8_sim and are labeled simulated everywhere.
#>
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$daemon = Start-Process python -PassThru -ArgumentList @("$repo\v8\scripts\daemon.py", "--config",
  "$repo\v8\config\daemon\sim_local.json") -WorkingDirectory $repo
Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:8080/"
try {
  python "$repo\v8\dashboard\server.py" --pi http://127.0.0.1:8765 --port 8080
} finally {
  if (-not $daemon.HasExited) { Stop-Process -Id $daemon.Id -ErrorAction SilentlyContinue }
}
