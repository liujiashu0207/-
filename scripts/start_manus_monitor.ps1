param(
  [int]$IntervalSec = 180
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "[MONITOR] start watch mode, interval=$IntervalSec sec"
python "scripts/manus_auto_monitor.py" --watch --interval_sec $IntervalSec
