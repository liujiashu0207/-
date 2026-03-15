param(
  [Parameter(Mandatory = $true)]
  [string]$RemoteUrl
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Host "[ERROR] git not found. Install Git first." -ForegroundColor Red
  exit 1
}

if (-not (Test-Path ".git")) {
  git init
}

$inside = git rev-parse --is-inside-work-tree
if ($inside.Trim() -ne "true") {
  Write-Host "[ERROR] Current folder is not a git repository." -ForegroundColor Red
  exit 1
}

$hasOrigin = git remote | Select-String -Pattern "^origin$" -Quiet
if ($hasOrigin) {
  git remote set-url origin $RemoteUrl
} else {
  git remote add origin $RemoteUrl
}

git branch -M main

Write-Host "[OK] Git sync setup completed." -ForegroundColor Green
Write-Host "Next step: run .\scripts\sync_to_github.ps1 -Message `"init sync`"" -ForegroundColor Cyan

