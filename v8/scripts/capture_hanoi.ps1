# Capture a stationary freedrive-taught pose; never commands robot motion or jaws.
# From the project folder: .\v8\scripts\capture_hanoi.ps1 1 5
[CmdletBinding(DefaultParameterSetName = 'Capture')]
param(
    [Parameter(Mandatory = $true, Position = 0, ParameterSetName = 'Capture')]
    [ValidateRange(1, 8)][int]$Peg,
    [Parameter(Mandatory = $true, Position = 1, ParameterSetName = 'Capture')]
    [ValidateRange(1, 7)][int]$Location,
    [ValidateSet('source_approach', 'pickup', 'pickup_entry', 'side_approach', 'clearance', 'destination_approach', 'place', 'place_withdrawal', 'retreat', 'home')]
    [string]$Role = 'source_approach',
    [Parameter(Mandatory = $true, ParameterSetName = 'Sync')]
    [switch]$SyncOnly,
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9.-]*$')]
    [string]$PiHost = 'on-edge-pi.local'
)
$ErrorActionPreference = 'Stop'
if (-not $SyncOnly -and $Peg -ge 5 -and $Location -le 6 -and -not $PSBoundParameters.ContainsKey('Role')) {
    $Role = 'side_approach'
}
if (-not $SyncOnly -and $Location -eq 7) {
    if (-not $PSBoundParameters.ContainsKey('Role')) { $Role = 'clearance' }
    elseif ($Role -ne 'clearance') { throw 'Location 7 is a clearance label, not a disk position. Use -Role clearance.' }
}
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$data = Join-Path $repo 'data\hanoi_teaching'
$node = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$exporter = Join-Path $PSScriptRoot 'export_hanoi_csv.mjs'
$remoteDir = '/home/seeker/Documents/On-Edge/data/hanoi_teaching'
$jsonPath = Join-Path $data '2026-09-29.jsonl'
$csvPath = Join-Path $data 'hanoi_poses_2026-09-29.csv'
$target = "seeker@$PiHost"
$connectionArgs = @('-o', 'BatchMode=yes', '-o', 'ConnectTimeout=6')
$captureSaved = $false
$download = $null
try {
    if (-not (Test-Path -LiteralPath $node)) { throw 'Bundled Node runtime is missing.' }
    if (-not (Test-Path -LiteralPath $exporter)) { throw 'CSV exporter is missing.' }
    $null = Get-Command ssh, scp -ErrorAction Stop
    if (-not $SyncOnly) {
        $name = "peg${Peg}_location${Location}_${Role}"
        $command = "bash -lc 'source /opt/ros/humble/setup.bash && export ROS_LOCALHOST_ONLY=1 && cd /home/seeker/Documents/On-Edge && python3 v8/scripts/hanoi_teach.py capture --name $name --note freedrive_taught'"
        $result = & ssh @connectionArgs $target $command
        if ($LASTEXITCODE -ne 0) { throw 'Capture failed. No pose success was confirmed; check the Pi log before retrying.' }
        $pose = @($result | ForEach-Object {
            try { $_ | ConvertFrom-Json } catch { }
        } | Where-Object { $_.event -eq 'pose_capture' -and $_.name -eq $name })
        if ($pose.Count -ne 1) { throw 'Capture response was not confirmed; inspect the Pi log before retrying.' }
        $captureSaved = $true
    }
    New-Item -ItemType Directory -Path $data -Force | Out-Null
    $download = Join-Path $data (([guid]::NewGuid().ToString()) + '.download')
    & scp -q @connectionArgs "${target}:$remoteDir/2026-09-29.jsonl" $download
    if ($LASTEXITCODE -ne 0) { throw 'Could not download the Pi log.' }
    $raw = [IO.File]::ReadAllText($download)
    foreach ($line in ($raw -split '\r?\n')) {
        if ($line.Trim()) { $null = $line | ConvertFrom-Json -ErrorAction Stop }
    }
    if (Test-Path -LiteralPath $jsonPath) {
        $previous = [IO.File]::ReadAllText($jsonPath)
        if (-not $raw.StartsWith($previous, [StringComparison]::Ordinal)) {
            throw 'Pi log differs from local history. Existing files preserved; reconcile before syncing.'
        }
    }
    Move-Item -LiteralPath $download -Destination $jsonPath -Force
    $download = $null
    $exportResult = & $node $exporter
    if ($LASTEXITCODE -ne 0) { throw 'CSV export failed. The raw capture remains saved.' }
    $summary = $exportResult | Select-Object -Last 1 | ConvertFrom-Json
    & scp -q @connectionArgs $csvPath "${target}:$remoteDir/hanoi_poses_2026-09-29.csv"
    if ($LASTEXITCODE -ne 0) { throw 'Local CSV saved, but its Pi copy could not be updated.' }
    if ($SyncOnly) { Write-Host "Synced $($summary.rows) poses." }
    else { Write-Host "Logged ($Peg,$Location) [$Role]. $($summary.rows) poses saved." }
    Write-Host $csvPath
} catch {
    if ($captureSaved) {
        Write-Warning 'The pose was saved on the Pi. Run this command with -SyncOnly to recover export/sync without capturing twice.'
    }
    Write-Error $_
    exit 1
} finally {
    if ($download -and (Test-Path -LiteralPath $download)) { Remove-Item -LiteralPath $download }
}
