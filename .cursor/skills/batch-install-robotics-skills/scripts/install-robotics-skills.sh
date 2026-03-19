#!/usr/bin/env bash
set -euo pipefail

SKILL_ROOT="${HOME}/.cursor/skills"
UPDATE_MODE="${1:-}"

REPOS=(
  "https://github.com/anthony-j-casper/robotics-skills.git"
  "https://github.com/robotics-ai/path-planning-skills.git"
  "https://github.com/ros-simulation/ros-simulation-skills.git"
  "https://github.com/control-ai/control-algorithms-skills.git"
  "https://github.com/robotics-optimization/optimization-for-robotics.git"
  "https://github.com/mobile-robotics/dynamic-obstacle-avoidance-skills.git"
  "https://github.com/slam-ai/slam-navigation-fusion-skills.git"
  "https://github.com/robotics-paper/paper-writing-robotics.git"
  "https://github.com/scientific-robotics/python-scientific-robotics.git"
  "https://github.com/robotics-code/code-review-robotics.git"
)

log() {
  local tag="$1"
  shift
  printf '[%s] %s\n' "$tag" "$*"
}

if ! command -v git >/dev/null 2>&1; then
  echo "git is not installed or not in PATH." >&2
  exit 1
fi

mkdir -p "$SKILL_ROOT"
cd "$SKILL_ROOT"

echo "Target directory: $SKILL_ROOT"
echo "Update mode: $UPDATE_MODE"

for repo in "${REPOS[@]}"; do
  repo_name="$(basename "$repo" .git)"
  repo_path="$SKILL_ROOT/$repo_name"

  if [[ -d "$repo_path/.git" ]]; then
    if [[ "$UPDATE_MODE" == "--update" ]]; then
      if git -C "$repo_path" pull --ff-only; then
        log "OK" "Updated $repo_name"
      else
        log "FAIL" "Update failed $repo_name"
      fi
    else
      log "SKIP" "Exists $repo_name"
    fi
    continue
  fi

  if [[ -d "$repo_path" ]]; then
    log "SKIP" "Exists (not git repo) $repo_name"
    continue
  fi

  if git clone "$repo" "$repo_path"; then
    log "OK" "Cloned $repo_name"
  else
    log "FAIL" "Clone failed $repo_name"
  fi
done

echo
echo "Done. Restart Cursor to load newly installed skills."
