param(
  [string]$Message = ""
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
  Write-Host "[ERROR] .git folder missing. Run setup script first." -ForegroundColor Red
  exit 1
}

$inside = & $gitCmd rev-parse --is-inside-work-tree
if ($inside.Trim() -ne "true") {
  Write-Host "[ERROR] Current folder is not a git repo." -ForegroundColor Red
  exit 1
}

$hasOrigin = (& $gitCmd remote) | Select-String -Pattern "^origin$" -Quiet
if (-not $hasOrigin) {
  Write-Host "[ERROR] origin remote not configured. Run setup_git_sync.ps1 first." -ForegroundColor Red
  exit 1
}

& $gitCmd add .

& $gitCmd diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
  Write-Host "[OK] No staged changes. Nothing to sync." -ForegroundColor Yellow
  exit 0
}

if ([string]::IsNullOrWhiteSpace($Message)) {
  $Message = "auto sync: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}

& $gitCmd commit -m $Message
& $gitCmd push origin main

Write-Host "[OK] Synced to GitHub." -ForegroundColor Green

