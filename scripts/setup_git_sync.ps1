param(
  [Parameter(Mandatory = $true)]
  [string]$RemoteUrl
)

$ErrorActionPreference = "Stop"

function Resolve-GitCommand {
  $cmd = Get-Command git -ErrorAction SilentlyContinue
  if ($cmd) { return "git" }
  $candidates = @(
    "C:\Program Files\Git\cmd\git.exe",
    "C:\Program Files\Git\bin\git.exe"
  )
  foreach ($p in $candidates) {
    if (Test-Path $p) { return $p }
  }
  return $null
}

 $gitCmd = Resolve-GitCommand
 if (-not $gitCmd) {
  Write-Host "[ERROR] git not found. Install Git first." -ForegroundColor Red
  exit 1
 }

if (-not (Test-Path ".git")) {
  & $gitCmd init
}

$inside = & $gitCmd rev-parse --is-inside-work-tree
if ($inside.Trim() -ne "true") {
  Write-Host "[ERROR] Current folder is not a git repository." -ForegroundColor Red
  exit 1
}

$hasOrigin = (& $gitCmd remote) | Select-String -Pattern "^origin$" -Quiet
if ($hasOrigin) {
  & $gitCmd remote set-url origin $RemoteUrl
} else {
  & $gitCmd remote add origin $RemoteUrl
}

& $gitCmd branch -M main

Write-Host "[OK] Git sync setup completed." -ForegroundColor Green
Write-Host "Next step: run .\scripts\sync_to_github.ps1 -Message `"init sync`"" -ForegroundColor Cyan

