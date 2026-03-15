param(
  [int]$IntervalSeconds = 60
)

$ErrorActionPreference = "Continue"

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

Write-Host "[INFO] Auto sync watcher started. Interval: $IntervalSeconds sec"
Write-Host "[INFO] Stop with Ctrl + C"

while ($true) {
  try {
    $gitCmd = Resolve-GitCommand
    if (-not $gitCmd) {
      Write-Host "[WARN] git not found. Waiting..." -ForegroundColor Yellow
      Start-Sleep -Seconds $IntervalSeconds
      continue
    }

    if (-not (Test-Path ".git")) {
      Write-Host "[WARN] Not a git repo. Waiting..." -ForegroundColor Yellow
      Start-Sleep -Seconds $IntervalSeconds
      continue
    }

    $changes = & $gitCmd status --porcelain
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

