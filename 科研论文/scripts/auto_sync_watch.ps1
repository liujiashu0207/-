param(
  [int]$IntervalSeconds = 60
)

$ErrorActionPreference = "Continue"

Write-Host "[INFO] Auto sync watcher started. Interval: $IntervalSeconds sec"
Write-Host "[INFO] Stop with Ctrl + C"

while ($true) {
  try {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
      Write-Host "[WARN] git not found. Waiting..." -ForegroundColor Yellow
      Start-Sleep -Seconds $IntervalSeconds
      continue
    }

    if (-not (Test-Path ".git")) {
      Write-Host "[WARN] Not a git repo. Waiting..." -ForegroundColor Yellow
      Start-Sleep -Seconds $IntervalSeconds
      continue
    }

    $changes = git status --porcelain
    if ($changes) {
      & ".\scripts\sync_to_github.ps1" -Message "auto watcher sync: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    } else {
      Write-Host "[INFO] No changes at $(Get-Date -Format 'HH:mm:ss')"
    }
  }
  catch {
    Write-Host "[WARN] Auto sync failed: $($_.Exception.Message)" -ForegroundColor Yellow
  }

  Start-Sleep -Seconds $IntervalSeconds
}

