param(
  [string]$Message = ""
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Host "[ERROR] git not found. Install Git first." -ForegroundColor Red
  exit 1
}

if (-not (Test-Path ".git")) {
  Write-Host "[ERROR] .git folder missing. Run setup script first." -ForegroundColor Red
  exit 1
}

$inside = git rev-parse --is-inside-work-tree
if ($inside.Trim() -ne "true") {
  Write-Host "[ERROR] Current folder is not a git repo." -ForegroundColor Red
  exit 1
}

$hasOrigin = git remote | Select-String -Pattern "^origin$" -Quiet
if (-not $hasOrigin) {
  Write-Host "[ERROR] origin remote not configured. Run setup_git_sync.ps1 first." -ForegroundColor Red
  exit 1
}

git add .

git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
  Write-Host "[OK] No staged changes. Nothing to sync." -ForegroundColor Yellow
  exit 0
}

if ([string]::IsNullOrWhiteSpace($Message)) {
  $Message = "auto sync: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}

git commit -m $Message
git push origin main

Write-Host "[OK] Synced to GitHub." -ForegroundColor Green

