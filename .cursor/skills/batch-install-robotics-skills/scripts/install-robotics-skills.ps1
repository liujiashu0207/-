param(
    [switch]$Update
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

$skillRoot = Join-Path $HOME ".cursor/skills"
$repos = @(
    "https://github.com/anthropics/skills.git",
    "https://github.com/composiohq/composio.git",
    "https://github.com/microsoft/promptflow-skills.git",
    "https://github.com/run-llama/llama-lab-skills.git",
    "https://github.com/ollama/ollama-skills.git",
    "https://github.com/huggingface/skills.git",
    "https://github.com/jmorgancusick/robotics-skills.git",
    "https://github.com/anthonyjcrane/robotics-control-skills.git",
    "https://github.com/ndrwn/cursor-robotics-skills.git",
    "https://github.com/neuromorphics/robotics-skills.git"
)

function Write-Status {
    param(
        [string]$Tag,
        [string]$Message,
        [ConsoleColor]$Color
    )
    Write-Host ("[{0}] {1}" -f $Tag, $Message) -ForegroundColor $Color
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git is not installed or not in PATH."
}

New-Item -ItemType Directory -Path $skillRoot -Force | Out-Null
Set-Location $skillRoot

Write-Host ("Target directory: {0}" -f $skillRoot)
Write-Host ("Update mode: {0}" -f $Update)

foreach ($repo in $repos) {
    $match = [regex]::Match($repo, "github\.com/([^/]+)/([^/]+?)(?:\.git)?$")
    if ($match.Success) {
        $owner = $match.Groups[1].Value
        $name = $match.Groups[2].Value
        $repoName = "$owner-$name"
    } else {
        $repoName = [System.IO.Path]::GetFileNameWithoutExtension($repo)
    }
    $repoPath = Join-Path $skillRoot $repoName
    $gitPath = Join-Path $repoPath ".git"

    try {
        if (Test-Path $gitPath) {
            if ($Update) {
                git -C $repoPath pull --ff-only
                Write-Status -Tag "OK" -Message ("Updated {0}" -f $repoName) -Color Green
            } else {
                Write-Status -Tag "SKIP" -Message ("Exists {0}" -f $repoName) -Color Yellow
            }
            continue
        }

        if (Test-Path $repoPath) {
            Write-Status -Tag "SKIP" -Message ("Exists (not git repo) {0}" -f $repoName) -Color Yellow
            continue
        }

        git clone $repo $repoPath
        if ($LASTEXITCODE -ne 0) {
            throw "git clone failed with exit code $LASTEXITCODE"
        }
        Write-Status -Tag "OK" -Message ("Cloned {0}" -f $repoName) -Color Green
    }
    catch {
        Write-Status -Tag "FAIL" -Message ("{0}: {1}" -f $repoName, $_.Exception.Message) -Color Red
    }
}

Write-Host ""
Write-Host "Done. Restart Cursor to load newly installed skills."
